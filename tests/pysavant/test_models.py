"""Tests for pysavant.models."""

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


class TestDeviceInfo:
    def test_to_dict(self):
        info = DeviceInfo(uid="ABC123", os_type="Linux", app="test")
        d = info.to_dict()
        assert d["UID"] == "ABC123"
        assert d["OS"] == "Linux"
        assert d["app"] == "test"

    def test_roundtrip(self):
        info = DeviceInfo(uid="X", os_type="Android", app="savant", version="2.0")
        restored = DeviceInfo.from_dict(info.to_dict())
        assert restored.uid == info.uid
        assert restored.os_type == info.os_type
        assert restored.app == info.app
        assert restored.version == info.version


class TestDevicePresent:
    def test_to_dict_camel_case(self):
        dp = DevicePresent(host_uid="host1", home_id="home1", message_format=1)
        d = dp.to_dict()
        assert d["hostUID"] == "host1"
        assert d["homeId"] == "home1"
        assert d["messageFormat"] == 1
        assert "device" in d

    def test_roundtrip(self):
        dp = DevicePresent(
            device=DeviceInfo(uid="dev1"),
            host_uid="host1",
            home_id="home1",
            protocol_version="2.0",
        )
        restored = DevicePresent.from_dict(dp.to_dict())
        assert restored.host_uid == "host1"
        assert restored.device.uid == "dev1"


class TestDeviceResponse:
    def test_from_dict(self):
        data = {
            "authorized": True,
            "authentication": False,
            "protocolVersion": 2,
            "buildNumber": 100,
            "hostName": "MyHost",
            "hostUID": "uid123",
        }
        resp = DeviceResponse.from_dict(data)
        assert resp.authorized is True
        assert resp.authentication is False
        assert resp.protocol_version == 2
        assert resp.build_number == 100
        assert resp.host_name == "MyHost"

    def test_roundtrip(self):
        resp = DeviceResponse(authorized=True, host_name="Test", build_number=42)
        restored = DeviceResponse.from_dict(resp.to_dict())
        assert restored.authorized is True
        assert restored.host_name == "Test"
        assert restored.build_number == 42


class TestAuthRequest:
    def test_omits_empty_fields(self):
        ar = AuthRequest(user="admin", password="pass")
        d = ar.to_dict()
        assert d == {"user": "admin", "password": "pass"}
        assert "pinCode" not in d
        assert "hostToken" not in d

    def test_token_auth(self):
        ar = AuthRequest(host_token="tok123")
        d = ar.to_dict()
        assert d == {"hostToken": "tok123"}

    def test_roundtrip(self):
        ar = AuthRequest(user="u", password="p", pin_code="1234")
        restored = AuthRequest.from_dict(ar.to_dict())
        assert restored.user == "u"
        assert restored.password == "p"
        assert restored.pin_code == "1234"


class TestAuthResponse:
    def test_from_dict(self):
        data = {
            "authorized": True,
            "hostToken": "new_token",
            "secretKey": "secret",
            "errorCode": 0,
            "permissions": {"admin": True},
        }
        resp = AuthResponse.from_dict(data)
        assert resp.authorized is True
        assert resp.host_token == "new_token"
        assert resp.secret_key == "secret"
        assert resp.permissions == {"admin": True}

    def test_roundtrip(self):
        resp = AuthResponse(authorized=False, error_code=5, error_reason="bad password")
        restored = AuthResponse.from_dict(resp.to_dict())
        assert restored.authorized is False
        assert restored.error_code == 5
        assert restored.error_reason == "bad password"


class TestMessageWrapper:
    def test_to_dict_uses_uri_key(self):
        mw = MessageWrapper(uri="state/update", messages=[{"state": "x", "value": 1}])
        d = mw.to_dict()
        assert d["URI"] == "state/update"
        assert len(d["messages"]) == 1

    def test_from_dict(self):
        mw = MessageWrapper.from_dict({"URI": "test/uri", "messages": [{"a": 1}]})
        assert mw.uri == "test/uri"
        assert mw.messages == [{"a": 1}]


class TestStateRegister:
    def test_to_dict(self):
        sr = StateRegister(state="global.ActiveZones")
        assert sr.to_dict() == {"state": "global.ActiveZones"}

    def test_roundtrip(self):
        sr = StateRegister(state="zone.Brightness")
        restored = StateRegister.from_dict(sr.to_dict())
        assert restored.state == sr.state


class TestStateUpdate:
    def test_string_value(self):
        su = StateUpdate(state="key", value="val")
        d = su.to_dict()
        assert d == {"state": "key", "value": "val"}

    def test_int_value(self):
        su = StateUpdate(state="key", value=42)
        restored = StateUpdate.from_dict(su.to_dict())
        assert restored.value == 42

    def test_bool_value(self):
        su = StateUpdate(state="key", value=True)
        restored = StateUpdate.from_dict(su.to_dict())
        assert restored.value is True


class TestServiceRequest:
    def test_auto_uuid(self):
        sr = ServiceRequest(service_type="SVC_ENV_LIGHTING", request="__RoomOn", zone="Kitchen")
        assert sr.request_id  # non-empty
        assert len(sr.request_id) == 36  # UUID format

    def test_to_dict(self):
        sr = ServiceRequest(
            service_type="SVC_ENV_LIGHTING",
            request="__RoomSetBrightness",
            zone="Kitchen",
            component="Lights",
            logical_component="Lighting_controller",
            request_args={"brightness": 50},
        )
        d = sr.to_dict()
        assert d["serviceType"] == "SVC_ENV_LIGHTING"
        assert d["request"] == "__RoomSetBrightness"
        assert d["zone"] == "Kitchen"
        assert d["component"] == "Lights"
        assert d["logicalComponent"] == "Lighting_controller"
        assert d["requestArgs"] == {"brightness": 50}

    def test_omits_empty_optional_fields(self):
        sr = ServiceRequest(service_type="SVC", request="req", zone="z")
        d = sr.to_dict()
        assert "component" not in d
        assert "logicalComponent" not in d
        assert "variantID" not in d
        assert "alias" not in d

    def test_roundtrip(self):
        sr = ServiceRequest(
            service_type="SVC_ENV_LIGHTING",
            request="__RoomOn",
            zone="Living Room",
            request_id="fixed-id",
        )
        restored = ServiceRequest.from_dict(sr.to_dict())
        assert restored.service_type == sr.service_type
        assert restored.request_id == "fixed-id"


class TestServiceResult:
    def test_from_dict(self):
        data = {"requestId": "abc", "results": {"ok": True}, "errorCode": 0, "errorMessage": ""}
        sr = ServiceResult.from_dict(data)
        assert sr.request_id == "abc"
        assert sr.results == {"ok": True}
        assert sr.error_code == 0


class TestDISRequest:
    def test_auto_uuid(self):
        dr = DISRequest(app="dashboard", request="getScenes")
        assert dr.request_id
        assert len(dr.request_id) == 36

    def test_to_dict_omits_empty_args(self):
        dr = DISRequest(app="dashboard", request="getScenes")
        d = dr.to_dict()
        assert "requestArgs" not in d

    def test_to_dict_includes_args(self):
        dr = DISRequest(app="dashboard", request="getScenes", request_args={"filter": "all"})
        d = dr.to_dict()
        assert d["requestArgs"] == {"filter": "all"}

    def test_roundtrip(self):
        dr = DISRequest(app="dashboard", request="getScenes", request_id="fixed")
        restored = DISRequest.from_dict(dr.to_dict())
        assert restored.app == "dashboard"
        assert restored.request_id == "fixed"
