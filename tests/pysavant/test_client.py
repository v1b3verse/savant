"""Tests for pysavant.client — SavantClient with FakeTransport."""

import asyncio

import pytest

from pysavant.client import SavantClient
from pysavant.exceptions import TimeoutError
from pysavant.models import ServiceRequest
from pysavant.protocol import SessionState
from tests.conftest import FakeTransport


def _device_recognized(auth_needed: bool = False) -> dict:
    return {
        "URI": "session/deviceRecognized",
        "messages": [
            {
                "authorized": True,
                "authentication": auth_needed,
                "protocolVersion": 2,
                "buildNumber": 100,
                "hostName": "TestHost",
                "hostUID": "host-uid-1",
            }
        ],
    }


def _auth_response(authorized: bool = True) -> dict:
    return {
        "URI": "session/authenticationResponse",
        "messages": [
            {
                "authorized": authorized,
                "hostToken": "new-token",
                "secretKey": "new-secret",
                "errorCode": 0 if authorized else 3,
                "errorReason": "" if authorized else "bad password",
            }
        ],
    }


class TestClientConnect:
    async def test_connect_no_auth(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        # Enqueue a ConnectionError to break the read loop after handshake
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", transport=ft)
        await client.connect()

        assert client.is_connected
        assert client.session.state == SessionState.READY
        assert client.session.host_name == "TestHost"

        # Verify DevicePresent was sent
        assert len(ft.sent) >= 1
        uri, msgs = ft.sent[0]
        assert uri == "session/devicePresent"
        assert len(msgs) == 1

        await client.disconnect()

    async def test_connect_with_auth(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=True))
        ft.enqueue_response(_auth_response(authorized=True))
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", user="admin", password="pass", transport=ft)
        await client.connect()

        assert client.is_connected
        assert client.session.state == SessionState.READY
        assert client.session.host_token == "new-token"
        assert client.session.secret_key == "new-secret"

        await client.disconnect()

    async def test_connect_timeout(self):
        ft = FakeTransport()
        # Don't enqueue any response — will timeout
        client = SavantClient(host="test", connect_timeout=0.1, transport=ft)
        with pytest.raises(TimeoutError, match="Handshake did not complete"):
            await client.connect()


class TestClientDisconnect:
    async def test_disconnect_idempotent(self):
        ft = FakeTransport()
        client = SavantClient(host="test", transport=ft)
        await client.disconnect()
        await client.disconnect()

    async def test_callbacks(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        ft.enqueue_error(Exception("done"))

        connected = []
        disconnected = []

        client = SavantClient(
            host="test",
            transport=ft,
            on_connected=lambda: connected.append(True),
            on_disconnected=lambda: disconnected.append(True),
        )
        await client.connect()
        assert connected == [True]

        await client.disconnect()
        assert len(disconnected) >= 1


class TestClientStateRegistration:
    async def test_register_states(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", transport=ft)
        await client.connect()

        await client.register_states(["global.ActiveZones", "zone.Brightness"])
        # Find the state/register send
        state_sends = [(u, m) for u, m in ft.sent if u == "state/register"]
        assert len(state_sends) == 1
        assert len(state_sends[0][1]) == 2

        await client.disconnect()


class TestClientServiceRequest:
    async def test_send_service_request(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", transport=ft)
        await client.connect()

        req = ServiceRequest(
            service_type="SVC_ENV_LIGHTING",
            request="__RoomOn",
            zone="Kitchen",
            request_id="test-id",
        )
        await client.send_service_request(req)

        svc_sends = [(u, m) for u, m in ft.sent if u == "service/request"]
        assert len(svc_sends) == 1
        assert svc_sends[0][1][0]["zone"] == "Kitchen"

        await client.disconnect()


class TestClientDispatch:
    async def test_state_updates_reach_state_manager(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        ft.enqueue_response(
            {
                "URI": "state/update",
                "messages": [{"state": "zone.Brightness", "value": 75}],
            }
        )
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", transport=ft)
        await client.connect()
        # Give read loop time to process
        await asyncio.sleep(0.05)

        assert client.state_manager.get("zone.Brightness") == 75

        await client.disconnect()

    async def test_context_manager(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized(auth_needed=False))
        ft.enqueue_error(Exception("done"))

        async with SavantClient(host="test", transport=ft) as client:
            assert client.is_connected
        assert not client.is_connected
