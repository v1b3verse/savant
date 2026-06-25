"""Climate/HVAC service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import (
    REQ_SET_COOL_POINT,
    REQ_SET_HEAT_POINT,
    REQ_SET_SINGLE_SETPOINT,
    SVC_ENV_SINGLE_SETPOINT_HVAC,
)

# Component/logical/variant values match the SQLite
# ServiceImplementationServiceResources table — every HVAC
# entity in this deployment uses:
#   component=KNX, logical=HVAC_controller, variantID=1
_HVAC_COMPONENT = "KNX"
_HVAC_LOGICAL = "HVAC_controller"
_HVAC_VARIANT = "1"


def set_cool_point(
    zone: str, temp: float, address: str | None = None
) -> ServiceRequest:
    args: dict[str, object] = {"CoolPointTemperature": temp}
    return ServiceRequest(
        service_type=SVC_ENV_SINGLE_SETPOINT_HVAC,
        request=REQ_SET_COOL_POINT,
        zone=zone,
        component=_HVAC_COMPONENT,
        logical_component=_HVAC_LOGICAL,
        variant_id=_HVAC_VARIANT,
        request_args=args,
    )


def set_heat_point(
    zone: str, temp: float, address: str | None = None
) -> ServiceRequest:
    args: dict[str, object] = {"HeatPointTemperature": temp}
    return ServiceRequest(
        service_type=SVC_ENV_SINGLE_SETPOINT_HVAC,
        request=REQ_SET_HEAT_POINT,
        zone=zone,
        component=_HVAC_COMPONENT,
        logical_component=_HVAC_LOGICAL,
        variant_id=_HVAC_VARIANT,
        request_args=args,
    )


def set_single_setpoint(
    zone: str, temp: float, address: str | None = None
) -> ServiceRequest:
    args: dict[str, object] = {"SetPointTemperature": temp}
    return ServiceRequest(
        service_type=SVC_ENV_SINGLE_SETPOINT_HVAC,
        request=REQ_SET_SINGLE_SETPOINT,
        zone=zone,
        component=_HVAC_COMPONENT,
        logical_component=_HVAC_LOGICAL,
        variant_id=_HVAC_VARIANT,
        request_args=args,
    )


def hvac_state_key(zone: str, prop: str) -> str:
    """Build an HVAC state key like '{zone}.HVAC_controller.{prop}'."""
    return f"{zone}.HVAC_controller.{prop}"
