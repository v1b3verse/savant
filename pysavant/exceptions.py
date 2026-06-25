"""Exception hierarchy for pysavant."""


class SavantError(Exception):
    """Base exception for all pysavant errors."""


class ConnectionError(SavantError):
    """Failed to connect to Savant host."""


class AuthenticationError(SavantError):
    """Authentication failed."""

    def __init__(
        self, message: str = "Authentication failed", error_code: int = 0, error_reason: str = ""
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.error_reason = error_reason


class SessionError(SavantError):
    """Session-level protocol error."""


class TimeoutError(SavantError):
    """Operation timed out."""


class ProtocolError(SavantError):
    """Unexpected protocol data or framing error."""
