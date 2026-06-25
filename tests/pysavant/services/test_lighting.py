"""Tests for pysavant.services.lighting."""

import pytest

from pysavant.protocol import SVC_ENV_LIGHTING
from pysavant.services.lighting import set_brightness, turn_off, turn_on


class TestLighting:
    def test_turn_on(self):
        req = turn_on("Kitchen")
        assert req.service_type == SVC_ENV_LIGHTING
        assert req.request == "__RoomSetBrightness"
        assert req.zone == "Kitchen"
        assert req.component == "Lights"
        assert req.request_args == {"BrightnessLevel": 100, "USE_LAST_DIMMER_VALUE": 1}

    def test_turn_off(self):
        req = turn_off("Kitchen")
        assert req.request == "__RoomSetBrightness"
        assert req.request_args == {"BrightnessLevel": 0, "USE_LAST_DIMMER_VALUE": 1}

    def test_set_brightness(self):
        req = set_brightness("Kitchen", 75)
        assert req.request == "__RoomSetBrightness"
        assert req.request_args == {"BrightnessLevel": 75, "USE_LAST_DIMMER_VALUE": 0}

    def test_set_brightness_bounds(self):
        set_brightness("z", 0)  # ok
        set_brightness("z", 100)  # ok

    def test_set_brightness_invalid(self):
        with pytest.raises(ValueError):
            set_brightness("z", -1)
        with pytest.raises(ValueError):
            set_brightness("z", 101)

    def test_serializes_correctly(self):
        req = turn_on("Living Room")
        d = req.to_dict()
        assert d["serviceID"] == SVC_ENV_LIGHTING
        assert d["zone"] == "Living Room"
        assert d["component"] == "Lights"
        assert d["logicalComponent"] == "Lighting_controller"
