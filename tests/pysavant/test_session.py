"""Tests for pysavant.session — handshake state machine."""

import pytest

from pysavant.exceptions import AuthenticationError, SessionError
from pysavant.protocol import SessionState
from pysavant.session import Session


class TestSessionInit:
    def test_initial_state_disconnected(self):
        s = Session()
        assert s.state == SessionState.DISCONNECTED
        assert s.is_ready is False

    def test_stores_credentials(self):
        s = Session(user="admin", password="pass", host_token="tok", secret_key="sec")
        assert s.user == "admin"
        assert s.password == "pass"
        assert s.host_token == "tok"
        assert s.secret_key == "sec"


class TestBuildDevicePresent:
    def test_returns_dict(self):
        s = Session(host_uid="host1", home_id="home1")
        dp = s.build_device_present()
        assert dp["hostUID"] == "host1"
        assert dp["homeId"] == "home1"
        assert dp["messageFormat"] == 1
        assert dp["protocolVersion"] == "2.0"
        assert dp["device"]["UID"]  # non-empty UUID


class TestBuildAuthRequest:
    def test_user_pass(self):
        s = Session(user="admin", password="pass")
        ar = s.build_auth_request()
        assert ar["user"] == "admin"
        assert ar["password"] == "pass"

    def test_token_auth(self):
        s = Session(host_token="tok123")
        ar = s.build_auth_request()
        assert ar["hostToken"] == "tok123"
        assert "user" not in ar


class TestHandleDeviceRecognized:
    def test_no_auth_needed_goes_ready(self):
        s = Session()
        result = s.handle_message(
            "session/deviceRecognized",
            {
                "authorized": True,
                "authentication": False,
                "protocolVersion": 2,
                "buildNumber": 100,
                "hostName": "MyHost",
            },
        )
        assert s.state == SessionState.READY
        assert s.is_ready is True
        assert s.host_name == "MyHost"
        assert s.protocol_version == 2
        assert s.build_number == 100
        assert result == []
        assert s.ready_event.is_set()

    def test_auth_required_returns_auth_request(self):
        s = Session(user="admin", password="pass")
        result = s.handle_message(
            "session/deviceRecognized",
            {
                "authorized": True,
                "authentication": True,
                "hostName": "SecureHost",
            },
        )
        assert s.state == SessionState.AUTH_REQUIRED
        assert s.is_ready is False
        assert len(result) == 1
        assert result[0]["user"] == "admin"

    def test_not_authorized_raises(self):
        s = Session()
        with pytest.raises(AuthenticationError, match="rejected"):
            s.handle_message(
                "session/deviceRecognized",
                {
                    "authorized": False,
                    "authentication": False,
                },
            )

    def test_auth_required_no_creds_raises(self):
        s = Session()  # no user/password/token
        with pytest.raises(SessionError, match="no credentials"):
            s.handle_message(
                "session/deviceRecognized",
                {
                    "authorized": True,
                    "authentication": True,
                },
            )

    def test_stores_host_uid_from_response(self):
        s = Session()
        s.handle_message(
            "session/deviceRecognized",
            {
                "authorized": True,
                "authentication": False,
                "hostUID": "new-uid",
            },
        )
        assert s.host_uid == "new-uid"


class TestHandleAuthResponse:
    def test_successful_auth(self):
        s = Session(user="admin", password="pass")
        # First go through device recognized
        s.handle_message(
            "session/deviceRecognized",
            {
                "authorized": True,
                "authentication": True,
            },
        )
        assert s.state == SessionState.AUTH_REQUIRED

        result = s.handle_message(
            "session/authenticationResponse",
            {
                "authorized": True,
                "hostToken": "new_token",
                "secretKey": "new_secret",
            },
        )
        assert s.state == SessionState.READY
        assert s.is_ready is True
        assert s.host_token == "new_token"
        assert s.secret_key == "new_secret"
        assert result == []

    def test_auth_failure_raises(self):
        s = Session(user="admin", password="wrong")
        s.handle_message(
            "session/deviceRecognized",
            {
                "authorized": True,
                "authentication": True,
            },
        )

        with pytest.raises(AuthenticationError, match="bad password") as exc_info:
            s.handle_message(
                "session/authenticationResponse",
                {
                    "authorized": False,
                    "errorCode": 3,
                    "errorReason": "bad password",
                },
            )
        assert exc_info.value.error_code == 3
        assert exc_info.value.error_reason == "bad password"


class TestHandleUnknownURI:
    def test_unknown_uri_returns_none(self):
        s = Session()
        result = s.handle_message("state/update", {"state": "x", "value": 1})
        assert result is None

    def test_service_uri_returns_none(self):
        s = Session()
        result = s.handle_message("service/result", {"requestId": "abc"})
        assert result is None
