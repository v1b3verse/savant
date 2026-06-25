"""Tests for the Savant coordinator logic (no HA dependency)."""

import asyncio

from pysavant.client import SavantClient
from tests.conftest import FakeTransport


def _device_recognized() -> dict:
    return {
        "URI": "session/deviceRecognized",
        "messages": [
            {
                "authorized": True,
                "authentication": False,
                "protocolVersion": 2,
                "buildNumber": 100,
                "hostName": "TestHost",
            }
        ],
    }


class TestCoordinatorStateFlow:
    """Test that state updates flow through client → state_manager correctly."""

    async def test_state_subscription_and_update(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized())
        # Don't enqueue state update yet — set up subscription first

        client = SavantClient(host="test", transport=ft)
        await client.connect()

        received = []
        client.state_manager.subscribe("Kitchen.*", lambda k, v: received.append((k, v)))
        await client.register_states(["Kitchen.RoomLightsAreOn"])

        # Now enqueue the state update after subscription is in place
        ft.enqueue_response(
            {
                "URI": "state/update",
                "messages": [{"state": "Kitchen.RoomLightsAreOn", "value": True}],
            }
        )
        ft.enqueue_error(Exception("done"))

        await asyncio.sleep(0.05)

        assert client.state_manager.get("Kitchen.RoomLightsAreOn") is True
        assert len(received) == 1
        assert received[0] == ("Kitchen.RoomLightsAreOn", True)

        await client.disconnect()

    async def test_multiple_zone_updates(self):
        ft = FakeTransport()
        ft.enqueue_response(_device_recognized())
        ft.enqueue_response(
            {
                "URI": "state/update",
                "messages": [
                    {"state": "global.ActiveZones", "value": "Kitchen,Bedroom,Living Room"},
                ],
            }
        )
        ft.enqueue_error(Exception("done"))

        client = SavantClient(host="test", transport=ft)
        await client.connect()
        await client.register_states(["global.ActiveZones"])

        await asyncio.sleep(0.05)

        assert client.state_manager.active_zones == ["Kitchen", "Bedroom", "Living Room"]

        await client.disconnect()
