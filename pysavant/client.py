"""High-level async client for Savant home automation systems."""

from __future__ import annotations

import asyncio
import builtins
import logging
from collections.abc import Callable
from typing import Any

from pysavant.config import BinaryTransferReceiver, HouseConfig, download_and_parse_config
from pysavant.exceptions import ConnectionError, TimeoutError
from pysavant.models import DISRequest, ServiceRequest, StateUpdate
from pysavant.protocol import (
    CONNECT_TIMEOUT,
    DEFAULT_PORT,
    PING_INTERVAL,
    PORT_FALLBACKS,
    URI_AUTH_REQUEST,
    URI_DIS_REQUEST_FMT,
    URI_FILE_DOWNLOAD,
    URI_SERVICE_REQUEST,
    URI_STATE_REGISTER,
    URI_STATE_SET,
    URI_STATE_UNREGISTER,
)
from pysavant.session import Session
from pysavant.state import StateManager
from pysavant.transport import Transport

logger = logging.getLogger(__name__)


class SavantClient:
    """Async client for controlling Savant smart home systems.

    Usage:
        async with SavantClient(host="192.168.1.100", user="admin", password="pass") as client:
            await client.register_states(["global.ActiveZones"])
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        user: str = "",
        password: str = "",
        host_token: str = "",
        secret_key: str = "",
        host_uid: str = "",
        home_id: str = "",
        connect_timeout: float = CONNECT_TIMEOUT,
        on_connected: Callable[[], Any] | None = None,
        on_disconnected: Callable[[], Any] | None = None,
        transport: Transport | None = None,
        *,
        auto_reconnect: bool = True,
        reconnect_delay: float = 1.0,
        reconnect_max_delay: float = 60.0,
    ) -> None:
        self.host = host
        self.port = port
        self._connect_timeout = connect_timeout
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._auto_reconnect = auto_reconnect
        self._reconnect_delay = reconnect_delay
        self._reconnect_max_delay = reconnect_max_delay

        self._transport = transport or Transport()
        self._transport_class = type(self._transport)
        self._session = Session(
            user=user,
            password=password,
            host_token=host_token,
            secret_key=secret_key,
            host_uid=host_uid,
            home_id=home_id,
        )
        self._state_manager = StateManager()

        self._read_task: asyncio.Task[None] | None = None
        self._ping_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._connected = False
        self._ping_counter = 0
        self._reconnect_attempt = 0
        self._intentional_disconnect = False

    @property
    def session(self) -> Session:
        return self._session

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    @property
    def is_connected(self) -> bool:
        return self._connected and self._transport.is_connected

    async def connect(self) -> None:
        """Connect, perform handshake, start read/ping loops.

        Tries ports in order: configured port first (default 5000),
        then fallbacks (9108, 8443) if connection fails.
        """
        ports_to_try = [self.port] + [p for p in PORT_FALLBACKS if p != self.port]
        last_error: Exception | None = None

        for port in ports_to_try:
            try:
                await self._transport.connect(self.host, port)
                self.port = port
                break
            except ConnectionError as e:
                last_error = e
                logger.info("Port %d failed: %s", port, e)
                continue
        else:
            raise ConnectionError(
                f"Could not connect to {self.host} on any port {ports_to_try}: {last_error}"
            )

        # Send DevicePresent
        dp = self._session.build_device_present()
        await self._transport.send("session/devicePresent", [dp])
        logger.info("Sent DevicePresent to %s:%d", self.host, self.port)

        # Start read loop before waiting for ready (it processes handshake responses)
        self._read_task = asyncio.create_task(self._read_loop())

        # Wait for session to become ready
        try:
            await asyncio.wait_for(
                self._session.ready_event.wait(),
                timeout=self._connect_timeout,
            )
        except builtins.TimeoutError:
            await self.disconnect()
            raise TimeoutError(f"Handshake did not complete within {self._connect_timeout}s")

        self._connected = True
        self._ping_task = asyncio.create_task(self._ping_loop())

        if self._on_connected:
            self._on_connected()

        logger.info("Connected to %s (%s)", self._session.host_name, self.host)

    async def disconnect(self) -> None:
        """Disconnect and clean up. Idempotent."""
        if not self._connected and self._read_task is None and self._reconnect_task is None:
            return

        self._connected = False
        self._intentional_disconnect = True
        self._reconnect_attempt = 0

        # Cancel reconnect task first so it doesn't interfere
        await self._cancel_reconnect()

        await self._cancel_tasks()

        await self._transport.close()

        if self._on_disconnected:
            self._on_disconnected()

        logger.info("Disconnected")

    async def _cancel_tasks(self) -> None:
        """Cancel read and ping tasks. Idempotent."""
        for task in [self._ping_task, self._read_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

        self._read_task = None
        self._ping_task = None

    async def _cancel_reconnect(self) -> None:
        """Cancel pending reconnect task. Idempotent."""
        task = self._reconnect_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._reconnect_task = None
        self._reconnect_attempt = 0

    async def register_states(self, keys: list[str]) -> None:
        """Subscribe to state keys for real-time updates."""
        msgs = self._state_manager.register(keys)
        await self._transport.send(URI_STATE_REGISTER, msgs)

    async def unregister_states(self, keys: list[str]) -> None:
        """Unsubscribe from state keys."""
        msgs = self._state_manager.unregister(keys)
        await self._transport.send(URI_STATE_UNREGISTER, msgs)

    async def send_service_request(self, req: ServiceRequest) -> None:
        """Send a service control command."""
        await self._transport.send(URI_SERVICE_REQUEST, [req.to_dict()])

    async def set_state(self, key: str, value: object) -> None:
        """Directly set a state value on the host (state/set).

        Some hosts process state/set for KNX writes
        but silently ignore service/request for HVAC operations.
        """
        update = StateUpdate(state=key, value=value)
        await self._transport.send(URI_STATE_SET, [update.to_dict()])

    async def send_dis_request(self, req: DISRequest) -> None:
        """Send a DIS request."""
        uri = URI_DIS_REQUEST_FMT.format(app=req.app)
        await self._transport.send(uri, [req.to_dict()])

    async def download_config_archive(self, file_path: str = "uiconfig.tar.gz") -> bytes:
        """Download a configuration archive (e.g. uiconfig.tar.gz) from the host.

        Returns the raw bytes of the downloaded file.
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        receiver = BinaryTransferReceiver()

        def _on_binary(data: bytes) -> None:
            receiver.feed(data)

        self._transport.set_binary_handler(_on_binary)

        try:
            await self._transport.send(
                URI_FILE_DOWNLOAD,
                [{"filePath": file_path}],
            )
            logger.info("Requested config download: %s", file_path)

            # Wait for the transfer to complete (poll using read loop)
            # The read loop dispatches to _on_binary via the transport handler
            for _ in range(300):  # ~30s max at 0.1s intervals
                if receiver.complete:
                    break
                await asyncio.sleep(0.1)

            if not receiver.complete:
                raise TimeoutError(
                    f"Config download of {file_path} did not complete"
                )

            logger.info(
                "Config download complete: %d bytes (%s)",
                len(receiver.data),
                file_path,
            )
            return receiver.data
        finally:
            self._transport.set_binary_handler(None)

    async def get_config(self) -> HouseConfig:
        """Download the house configuration and parse it into structured models.

        This performs the full uiconfig.tar.gz download, extracts the
        serviceImplementation.sqlite database, and returns a HouseConfig
        with rooms, entities, and services.

        Raises:
            ConnectionError: if not connected
            TimeoutError: if the download doesn't complete
            FileNotFoundError: if serviceImplementation.sqlite is missing
        """
        return await download_and_parse_config(self)

    async def __aenter__(self) -> SavantClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.disconnect()

    async def _read_loop(self) -> None:
        """Background task: receive and dispatch frames.

        On unexpected disconnect, triggers auto-reconnect (if enabled).
        """
        try:
            while self._transport.is_connected:
                try:
                    wrapper = await self._transport.receive()
                except TimeoutError:
                    continue
                except ConnectionError:
                    break
                self._dispatch(wrapper)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Read loop error")
        finally:
            if not self._intentional_disconnect:
                self._connected = False
                if self._on_disconnected:
                    self._on_disconnected()
                if self._auto_reconnect:
                    self._schedule_reconnect()

    async def _ping_loop(self) -> None:
        """Background task: send ping text frames."""
        try:
            while self._connected:
                await asyncio.sleep(PING_INTERVAL)
                self._ping_counter += 1
                await self._transport.send_text(f"SavantPing{self._ping_counter}")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Ping loop error")

    def _schedule_reconnect(self) -> None:
        """Fire off a background reconnect task (no-op if one is already pending)."""
        if self._reconnect_task is not None and not self._reconnect_task.done():
            logger.debug("Reconnect already in progress")
            return
        self._reconnect_task = asyncio.create_task(self._do_reconnect())

    async def _do_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff.

        Re-establishes the WebSocket, performs the full handshake,
        and re-registers all previously subscribed state keys.
        """
        delay = self._reconnect_delay

        while self._auto_reconnect:
            self._reconnect_attempt += 1
            attempt = self._reconnect_attempt

            logger.info(
                "Reconnect attempt %d in %.1fs...",
                attempt,
                delay,
            )

            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                logger.info("Reconnect cancelled during backoff")
                return

            # Double-check we weren't asked to stop
            if not self._auto_reconnect or self._connected:
                return

            # Reset session state for fresh handshake
            self._session.reset()

            # Fresh transport — the old one is dead
            old_transport = self._transport
            self._transport = self._transport_class()
            await old_transport.close()

            try:
                # Connect + handshake
                ports_to_try = [self.port] + [p for p in PORT_FALLBACKS if p != self.port]
                last_error: Exception | None = None

                for port in ports_to_try:
                    try:
                        await self._transport.connect(self.host, port)
                        self.port = port
                        break
                    except ConnectionError as e:
                        last_error = e
                        logger.info("Reconnect: port %d failed: %s", port, e)
                        continue
                else:
                    raise ConnectionError(
                        f"Reconnect failed on all ports {ports_to_try}: {last_error}"
                    )

                # Send DevicePresent
                dp = self._session.build_device_present()
                await self._transport.send("session/devicePresent", [dp])

                # Start new read loop (catches handshake responses)
                self._read_task = asyncio.create_task(self._read_loop())

                # Wait for handshake
                try:
                    await asyncio.wait_for(
                        self._session.ready_event.wait(),
                        timeout=self._connect_timeout,
                    )
                except builtins.TimeoutError:
                    await self._cancel_tasks()
                    await self._transport.close()
                    logger.warning(
                        "Reconnect attempt %d: handshake timeout",
                        attempt,
                    )
                    delay = min(delay * 2, self._reconnect_max_delay)
                    continue

                # Re-register all previously subscribed state keys
                registered = list(self._state_manager.registered_keys)
                if registered:
                    await self.register_states(registered)
                    logger.info(
                        "Re-registered %d state keys after reconnect",
                        len(registered),
                    )

                # Success — start ping loop and mark connected
                self._connected = True
                self._reconnect_attempt = 0
                self._ping_task = asyncio.create_task(self._ping_loop())

                if self._on_connected:
                    self._on_connected()

                logger.info(
                    "Reconnected to %s (%s)",
                    self._session.host_name,
                    self.host,
                )
                return

            except asyncio.CancelledError:
                logger.info("Reconnect cancelled during attempt")
                await self._transport.close()
                return
            except Exception:
                logger.exception(
                    "Reconnect attempt %d failed",
                    attempt,
                )
                await self._transport.close()
                delay = min(delay * 2, self._reconnect_max_delay)

        logger.info("Auto-reconnect disabled, giving up")

    def _dispatch(self, wrapper: dict[str, Any]) -> None:
        """Route incoming message by URI."""
        # Text frames (ping responses etc)
        if "_text" in wrapper:
            return

        uri = wrapper.get("URI", "")
        messages = wrapper.get("messages", [])
        if not uri:
            return

        logger.debug("Received %s (%d messages)", uri, len(messages))

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            # Session messages
            result = self._session.handle_message(uri, msg)
            if result is not None:
                # Session consumed it; send any response messages
                if result:
                    asyncio.create_task(self._transport.send(URI_AUTH_REQUEST, result))
                continue

            # State messages
            prefix = uri.split("/")[0] if "/" in uri else uri
            if prefix in ("state", "dis"):
                state_key = msg.get("state", "")
                value = msg.get("value")
                if state_key:
                    self._state_manager.handle_update(state_key, value)
            elif prefix == "service":
                request_id = msg.get("requestId", "")
                error_code = msg.get("errorCode", 0)
                if error_code:
                    logger.warning(
                        "Service error requestId=%s errorCode=%d: %s",
                        request_id,
                        error_code,
                        msg.get("errorMessage", ""),
                    )
                else:
                    logger.debug("Service OK requestId=%s", request_id)
