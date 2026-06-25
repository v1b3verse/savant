"""Tests for pysavant.protocol constants."""

from pysavant.protocol import (
    CONNECT_TIMEOUT,
    DEFAULT_PORT,
    MESSAGE_FORMAT,
    PING_INTERVAL,
    PROTOCOL_VERSION,
    RECEIVE_TIMEOUT,
    REQ_ROOM_OFF,
    REQ_ROOM_ON,
    REQ_ROOM_SET_BRIGHTNESS,
    STATE_ACTIVE_ZONES,
    SVC_ENV_LIGHTING,
    URI_AUTH_REQUEST,
    URI_AUTH_RESPONSE,
    URI_DEVICE_PRESENT,
    URI_DEVICE_RECOGNIZED,
    URI_SERVICE_REQUEST,
    URI_STATE_REGISTER,
    URI_STATE_UPDATE,
    SessionState,
)


class TestSessionState:
    def test_values(self):
        assert SessionState.DISCONNECTED == 0
        assert SessionState.CONNECTED == 1
        assert SessionState.AUTH_REQUIRED == 2
        assert SessionState.READY == 3

    def test_is_int(self):
        assert isinstance(SessionState.READY, int)

    def test_ordering(self):
        assert SessionState.DISCONNECTED < SessionState.CONNECTED
        assert SessionState.CONNECTED < SessionState.AUTH_REQUIRED
        assert SessionState.AUTH_REQUIRED < SessionState.READY


class TestURIs:
    def test_session_uris(self):
        assert URI_DEVICE_PRESENT == "session/devicePresent"
        assert URI_DEVICE_RECOGNIZED == "session/deviceRecognized"
        assert URI_AUTH_REQUEST == "session/authenticationRequest"
        assert URI_AUTH_RESPONSE == "session/authenticationResponse"

    def test_state_uris(self):
        assert URI_STATE_REGISTER == "state/register"
        assert URI_STATE_UPDATE == "state/update"

    def test_service_uris(self):
        assert URI_SERVICE_REQUEST == "service/request"


class TestConstants:
    def test_defaults(self):
        assert DEFAULT_PORT == 5000
        assert PING_INTERVAL == 1.0
        assert RECEIVE_TIMEOUT == 30.0
        assert CONNECT_TIMEOUT == 15.0
        assert MESSAGE_FORMAT == 1
        assert PROTOCOL_VERSION == "2.0"

    def test_service_types(self):
        assert SVC_ENV_LIGHTING == "SVC_ENV_LIGHTING"

    def test_request_names(self):
        assert REQ_ROOM_ON == "__RoomOn"
        assert REQ_ROOM_OFF == "__RoomOff"
        assert REQ_ROOM_SET_BRIGHTNESS == "__RoomSetBrightness"

    def test_state_keys(self):
        assert STATE_ACTIVE_ZONES == "global.ActiveZones"
