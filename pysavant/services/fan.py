"""Fan service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import REQ_ROOM_OFF, REQ_SET_FAN_LEVEL, SVC_ENV_FAN


def set_level(zone: str, level: int) -> ServiceRequest:
    """Set fan level (0=off, 1=low, 2=medium, 3=high)."""
    if level not in (0, 1, 2, 3):
        raise ValueError(f"Fan level must be 0-3, got {level}")
    return ServiceRequest(
        service_type=SVC_ENV_FAN,
        request=REQ_SET_FAN_LEVEL,
        zone=zone,
        component="Fans",
        logical_component="Fan_controller",
        request_args={"fanLevel": level},
    )


def turn_off(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_FAN,
        request=REQ_ROOM_OFF,
        zone=zone,
        component="Fans",
        logical_component="Fan_controller",
    )
