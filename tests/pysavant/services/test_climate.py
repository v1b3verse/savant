"""Tests for pysavant.services.climate."""

from pysavant.protocol import SVC_ENV_SINGLE_SETPOINT_HVAC
from pysavant.services.climate import (
    hvac_state_key,
    set_cool_point,
    set_heat_point,
    set_single_setpoint,
)


class TestClimate:
    def test_set_cool_point(self):
        req = set_cool_point("Bedroom", 72.0)
        assert req.service_type == SVC_ENV_SINGLE_SETPOINT_HVAC
        assert req.request == "SetCoolPointTemperature"
        assert req.zone == "Bedroom"
        assert req.component == "KNX"
        assert req.logical_component == "HVAC_controller"
        assert req.variant_id == "1"
        assert req.request_args == {"CoolPointTemperature": 72.0}

    def test_set_heat_point(self):
        req = set_heat_point("Bedroom", 68.0)
        assert req.service_type == SVC_ENV_SINGLE_SETPOINT_HVAC
        assert req.request == "SetHeatPointTemperature"
        assert req.component == "KNX"
        assert req.logical_component == "HVAC_controller"
        assert req.variant_id == "1"
        assert req.request_args == {"HeatPointTemperature": 68.0}

    def test_set_single_setpoint(self):
        req = set_single_setpoint("Bedroom", 70.0)
        assert req.service_type == SVC_ENV_SINGLE_SETPOINT_HVAC
        assert req.request == "SetSingleSetPointTemperature"
        assert req.component == "KNX"
        assert req.logical_component == "HVAC_controller"
        assert req.variant_id == "1"
        assert req.request_args == {"SetPointTemperature": 70.0}

    def test_hvac_state_key(self):
        assert (
            hvac_state_key("Kitchen", "ThermostatCurrentSetPoint_1")
            == "Kitchen.HVAC_controller.ThermostatCurrentSetPoint_1"
        )
