"""Tests for pysavant.services.climate."""

from pysavant.protocol import SVC_ENV_HVAC
from pysavant.services.climate import (
    hvac_state_key,
    set_cool_point,
    set_heat_point,
    set_single_setpoint,
)


class TestClimate:
    def test_set_cool_point(self):
        req = set_cool_point("Bedroom", 72.0)
        assert req.service_type == SVC_ENV_HVAC
        assert req.request == "__SetCoolPoint"
        assert req.zone == "Bedroom"
        assert req.request_args == {"temperature": 72.0}

    def test_set_heat_point(self):
        req = set_heat_point("Bedroom", 68.0)
        assert req.request == "__SetHeatPoint"
        assert req.request_args == {"temperature": 68.0}

    def test_set_single_setpoint(self):
        req = set_single_setpoint("Bedroom", 70.0)
        assert req.request == "__SetSingleSetPoint"

    def test_hvac_state_key(self):
        assert (
            hvac_state_key("Kitchen", "ThermostatCurrentSetPoint_1")
            == "Kitchen.HVAC_controller.ThermostatCurrentSetPoint_1"
        )
