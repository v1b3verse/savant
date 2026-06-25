"""Tests for pysavant.exceptions."""

from pysavant.exceptions import (
    AuthenticationError,
    ConnectionError,
    ProtocolError,
    SavantError,
    SessionError,
    TimeoutError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_savant_error(self):
        for exc_cls in [
            ConnectionError,
            AuthenticationError,
            SessionError,
            TimeoutError,
            ProtocolError,
        ]:
            assert issubclass(exc_cls, SavantError)

    def test_savant_error_is_exception(self):
        assert issubclass(SavantError, Exception)

    def test_authentication_error_fields(self):
        err = AuthenticationError("bad creds", error_code=42, error_reason="invalid password")
        assert str(err) == "bad creds"
        assert err.error_code == 42
        assert err.error_reason == "invalid password"

    def test_authentication_error_defaults(self):
        err = AuthenticationError()
        assert err.error_code == 0
        assert err.error_reason == ""

    def test_exceptions_are_catchable(self):
        try:
            raise ConnectionError("offline")
        except SavantError as e:
            assert str(e) == "offline"
