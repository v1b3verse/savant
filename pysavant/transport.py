"""WebSocket transport with msgpack binary and JSON text encoding support."""

from __future__ import annotations

import asyncio
import builtins
import gzip
import json
import logging
import ssl
from collections.abc import Callable
from typing import Any

import aiohttp
import msgpack

from pysavant.exceptions import ConnectionError, ProtocolError, TimeoutError
from pysavant.models import MessageWrapper
from pysavant.protocol import DEFAULT_PORT, RECEIVE_TIMEOUT

logger = logging.getLogger(__name__)


def encode_message(data: dict[str, Any]) -> bytes:
    """Encode a dict to msgpack bytes using compatible encoding.

    Uses use_bin_type=False (compatible mode) because the Savant host's
    msgpack parser expects the older format where strings are raw bytes
    (no str/bin distinction).
    """
    result: bytes = msgpack.packb(data, use_bin_type=False)
    return result


def decode_payload(data: bytes) -> dict[str, Any]:
    """Decode a binary payload (possibly gzip-compressed) from msgpack to dict."""
    if not data:
        raise ProtocolError("Empty frame")

    payload = data
    # Detect gzip: 0x1F 0x8B magic bytes
    if len(data) > 1 and data[0] == 0x1F and data[1] == 0x8B:
        try:
            payload = gzip.decompress(data)
        except Exception as e:
            raise ProtocolError(f"gzip decompress failed: {e}") from e

    try:
        result = msgpack.unpackb(payload, raw=False)
    except Exception as e:
        raise ProtocolError(f"msgpack decode failed: {e}") from e

    return normalize_keys(result)  # type: ignore[no-any-return]


def normalize_keys(obj: Any) -> Any:
    """Recursively convert msgpack map keys to str."""
    if isinstance(obj, dict):
        return {str(k): normalize_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_keys(item) for item in obj]
    return obj


ENCODING_MSGPACK = "msgpack"
ENCODING_JSON = "json"


class Transport:
    """WebSocket transport for Savant protocol."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._write_lock = asyncio.Lock()
        self._closed = False
        self._binary_handler: Callable[[bytes], None] | None = None

    def set_binary_handler(self, handler: Callable[[bytes], None] | None) -> None:
        """Register a callback for raw binary frames (config download etc.)."""
        self._binary_handler = handler

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed and not self._closed

    async def connect(self, host: str, port: int = DEFAULT_PORT) -> None:
        """Connect to Savant host via WSS."""
        url = f"wss://{host}:{port}/"
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            self._session = aiohttp.ClientSession()
            self._ws = await self._session.ws_connect(
                url,
                protocols=["rpm-protocol"],
                ssl=ssl_ctx,
                timeout=aiohttp.ClientWSTimeout(ws_close=10.0),
            )
        except Exception as e:
            if self._session:
                await self._session.close()
                self._session = None
            raise ConnectionError(f"Failed to connect to {url}: {e}") from e

        logger.info("Connected to %s", url)

    async def send(self, uri: str, messages: list[dict[str, Any]]) -> None:
        """Send a MessageWrapper as a binary msgpack frame."""
        if not self.is_connected:
            raise ConnectionError("Not connected")

        wrapper = MessageWrapper(uri=uri, messages=messages)
        data = encode_message(wrapper.to_dict())

        async with self._write_lock:
            assert self._ws is not None
            await self._ws.send_bytes(data)

        logger.debug("Sent %s (%d messages, %d bytes)", uri, len(messages), len(data))

    async def send_text(self, text: str) -> None:
        """Send a text frame (used for ping)."""
        if not self.is_connected:
            raise ConnectionError("Not connected")

        async with self._write_lock:
            assert self._ws is not None
            await self._ws.send_str(text)

    async def receive(self, timeout: float = RECEIVE_TIMEOUT) -> dict[str, Any]:
        """Read and decode the next frame. Raises TimeoutError after timeout.

        Handles both:
        - BINARY frames: decoded as msgpack (possibly gzip-compressed)
        - TEXT frames: parsed as JSON (Savant host responds in JSON)
        """
        if not self.is_connected:
            raise ConnectionError("Not connected")

        assert self._ws is not None
        try:
            msg = await asyncio.wait_for(self._ws.receive(), timeout=timeout)
        except builtins.TimeoutError:
            raise TimeoutError(f"No message received within {timeout}s")

        if msg.type == aiohttp.WSMsgType.BINARY:
            # Raw binary transfer packets (file download) aren't valid msgpack
            if self._binary_handler is not None:
                try:
                    decoded = decode_payload(msg.data)
                    return decoded
                except ProtocolError:
                    self._binary_handler(bytes(msg.data))
                    return {"_binary": True}
            return decode_payload(msg.data)
        elif msg.type == aiohttp.WSMsgType.TEXT:
            try:
                return json.loads(msg.data)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, ValueError):
                logger.debug("Received non-JSON text frame: %s", msg.data)
                return {"_text": msg.data}
        elif msg.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSING,
            aiohttp.WSMsgType.CLOSED,
        ):
            raise ConnectionError("WebSocket closed")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            raise ConnectionError(f"WebSocket error: {self._ws.exception()}")
        else:
            raise ProtocolError(f"Unexpected message type: {msg.type}")

    async def close(self) -> None:
        """Gracefully close the transport. Idempotent."""
        if self._closed:
            return
        self._closed = True

        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()

        self._ws = None
        self._session = None
        logger.info("Transport closed")
