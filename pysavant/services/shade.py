"""Shade/cover service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import REQ_SET_SHADE_LEVEL, REQ_SHADE_STOP, SVC_ENV_SHADE


def set_level(zone: str, level: int) -> ServiceRequest:
    """Set shade level (0=closed, 100=open)."""
    if not 0 <= level <= 100:
        raise ValueError(f"Shade level must be 0-100, got {level}")
    return ServiceRequest(
        service_type=SVC_ENV_SHADE,
        request=REQ_SET_SHADE_LEVEL,
        zone=zone,
        component="Shades",
        logical_component="Lighting_controller",
        request_args={"ShadeLevel": level},
    )


def stop(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_SHADE,
        request=REQ_SHADE_STOP,
        zone=zone,
        component="Shades",
        logical_component="Lighting_controller",
    )
