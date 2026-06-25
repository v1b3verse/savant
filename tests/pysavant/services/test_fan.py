"""Tests for pysavant.services.fan."""

import pytest

from pysavant.protocol import SVC_ENV_FAN
from pysavant.services.fan import set_level, turn_off


class TestFan:
    def test_set_level(self):
        req = set_level("Bedroom", 2)
        assert req.service_type == SVC_ENV_FAN
        assert req.request == "__SetFanLevel"
        assert req.request_args == {"fanLevel": 2}

    def test_set_level_valid_values(self):
        for level in (0, 1, 2, 3):
            req = set_level("z", level)
            assert req.request_args["fanLevel"] == level

    def test_set_level_invalid(self):
        with pytest.raises(ValueError):
            set_level("z", 4)
        with pytest.raises(ValueError):
            set_level("z", -1)

    def test_turn_off(self):
        req = turn_off("Bedroom")
        assert req.request == "__RoomOff"
        assert req.service_type == SVC_ENV_FAN
