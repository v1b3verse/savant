"""pysavant — Async Python library for Savant home automation systems."""

__version__ = "0.1.0"

from pysavant.client import SavantClient
from pysavant.discovery import SavantHost, discover, discover_one
from pysavant.exceptions import (
    AuthenticationError,
    ConnectionError,
    ProtocolError,
    SavantError,
    SessionError,
    TimeoutError,
)
from pysavant.models import (
    AuthRequest,
    AuthResponse,
    DeviceInfo,
    DevicePresent,
    DeviceResponse,
    DISRequest,
    MessageWrapper,
    ServiceRequest,
    ServiceResult,
    StateRegister,
    StateUpdate,
)
from pysavant.protocol import SessionState
from pysavant.session import Session
from pysavant.state import StateManager

__all__ = [
    "__version__",
    "SavantClient",
    "Session",
    "StateManager",
    "SavantHost",
    "discover",
    "discover_one",
    "SavantError",
    "ConnectionError",
    "AuthenticationError",
    "SessionError",
    "TimeoutError",
    "ProtocolError",
    "SessionState",
    "DeviceInfo",
    "DevicePresent",
    "DeviceResponse",
    "AuthRequest",
    "AuthResponse",
    "MessageWrapper",
    "StateRegister",
    "StateUpdate",
    "ServiceRequest",
    "ServiceResult",
    "DISRequest",
]
