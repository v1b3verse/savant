"""Climate/HVAC service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import (
    REQ_SET_COOL_POINT,
    REQ_SET_HEAT_POINT,
    REQ_SET_SINGLE_SETPOINT,
    SVC_ENV_HVAC,
)


def set_cool_point(zone: str, temp: float) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_HVAC,
        request=REQ_SET_COOL_POINT,
        zone=zone,
        component="HVAC",
        logical_component="HVAC_controller",
        request_args={"temperature": temp},
    )


def set_heat_point(zone: str, temp: float) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_HVAC,
        request=REQ_SET_HEAT_POINT,
        zone=zone,
        component="HVAC",
        logical_component="HVAC_controller",
        request_args={"temperature": temp},
    )


def set_single_setpoint(zone: str, temp: float) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_HVAC,
        request=REQ_SET_SINGLE_SETPOINT,
        zone=zone,
        component="HVAC",
        logical_component="HVAC_controller",
        request_args={"temperature": temp},
    )


def hvac_state_key(zone: str, prop: str) -> str:
    """Build an HVAC state key like '{zone}.HVAC_controller.{prop}'."""
    return f"{zone}.HVAC_controller.{prop}"
