"""Session handshake state machine for Savant protocol.

Pure logic, zero I/O. handle_message() consumes decoded dicts and returns
dicts to send (or None). Trivially testable.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from pysavant.exceptions import AuthenticationError, SessionError
from pysavant.models import AuthRequest, AuthResponse, DeviceInfo, DevicePresent, DeviceResponse
from pysavant.protocol import (
    MESSAGE_FORMAT,
    PROTOCOL_VERSION,
    URI_DEVICE_RECOGNIZED,
    SessionState,
)

logger = logging.getLogger(__name__)


class Session:
    """Manages the handshake state machine.

    Disconnected(0) → Connected(1) → AuthRequired(2) → Ready(3)
    """

    def __init__(
        self,
        user: str = "",
        password: str = "",
        host_token: str = "",
        secret_key: str = "",
        host_uid: str = "",
        home_id: str = "",
    ) -> None:
        self._state = SessionState.DISCONNECTED
        self.user = user
        self.password = password
        self.host_token = host_token
        self.secret_key = secret_key
        self.host_uid = host_uid
        self.home_id = home_id

        # Populated after handshake
        self.host_name: str = ""
        self.protocol_version: int = 0
        self.build_number: int = 0

        self.ready_event = asyncio.Event()

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def is_ready(self) -> bool:
        return self._state == SessionState.READY

    def build_device_present(self) -> dict[str, Any]:
        """Build the DevicePresent message dict to send."""
        client_uid = uuid.uuid4().hex.upper()
        dp = DevicePresent(
            device=DeviceInfo(uid=client_uid),
            message_format=MESSAGE_FORMAT,
            protocol_version=PROTOCOL_VERSION,
            configuration_id=str(uuid.uuid4()),
            host_uid=self.host_uid,
            home_id=self.home_id,
        )
        return dp.to_dict()

    def build_auth_request(self) -> dict[str, Any]:
        """Build the AuthRequest message dict to send."""
        ar = AuthRequest(
            user=self.user,
            password=self.password,
            host_token=self.host_token,
        )
        return ar.to_dict()

    def handle_message(self, uri: str, msg: dict[str, Any]) -> list[dict[str, Any]] | None:
        """Process a session message. Returns messages to send, or None if not consumed.

        Raises AuthenticationError on auth failures.
        """
        if uri == URI_DEVICE_RECOGNIZED:
            return self._handle_device_recognized(msg)
        elif uri == "session/authenticationResponse":
            return self._handle_auth_response(msg)
        return None

    def _handle_device_recognized(self, msg: dict[str, Any]) -> list[dict[str, Any]]:
        resp = DeviceResponse.from_dict(msg)
        self._state = SessionState.CONNECTED

        self.protocol_version = resp.protocol_version
        self.build_number = resp.build_number
        self.host_name = resp.host_name
        if resp.host_uid:
            self.host_uid = resp.host_uid

        logger.info(
            "deviceRecognized: authorized=%s authentication=%s host=%s",
            resp.authorized,
            resp.authentication,
            resp.host_name,
        )

        if resp.authentication:
            # Auth is available — proceed to authenticate
            self._state = SessionState.AUTH_REQUIRED
            if not self.user and not self.host_token:
                raise SessionError(
                    "Authentication required but no credentials provided"
                )
            return [self.build_auth_request()]

        if resp.authorized:
            # No auth needed — go straight to Ready
            self._set_ready()
            return []

        # Not authorized and no auth available — rejected
        raise AuthenticationError("Host rejected device (authorized=false)")

    def _handle_auth_response(self, msg: dict[str, Any]) -> list[dict[str, Any]]:
        resp = AuthResponse.from_dict(msg)

        logger.info(
            "authResponse: authorized=%s errorCode=%d",
            resp.authorized,
            resp.error_code,
        )

        if not resp.authorized:
            raise AuthenticationError(
                f"Authentication failed: {resp.error_reason}",
                error_code=resp.error_code,
                error_reason=resp.error_reason,
            )

        if resp.host_token:
            self.host_token = resp.host_token
        if resp.secret_key:
            self.secret_key = resp.secret_key

        self._set_ready()
        return []

    def reset(self) -> None:
        """Reset session state for reconnect. Clears ready_event, keeps credentials."""
        self._state = SessionState.DISCONNECTED
        self.ready_event = asyncio.Event()
        self.host_name = ""
        self.protocol_version = 0
        self.build_number = 0
        logger.info("Session reset for reconnect")

    def _set_ready(self) -> None:
        self._state = SessionState.READY
        self.ready_event.set()
        logger.info("Session ready")
