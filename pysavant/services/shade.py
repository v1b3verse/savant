"""Shade/cover service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import REQ_SET_SHADE_LEVEL, REQ_SHADE_STOP, SVC_ENV_SHADE


def open_cover(zone: str, address: str | None = None) -> ServiceRequest:
    """Open shade fully."""
    return set_level(zone, 100, address=address)


def close_cover(zone: str, address: str | None = None) -> ServiceRequest:
    """Close shade fully."""
    return set_level(zone, 0, address=address)


def set_level(
    zone: str, level: int, address: str | None = None
) -> ServiceRequest:
    """Set shade level (0=closed, 100=open)."""
    if not 0 <= level <= 100:
        raise ValueError(f"Shade level must be 0-100, got {level}")
    args: dict[str, object] = {"ShadeLevel": level}
    if address is not None:
        args["Address1"] = address
    return ServiceRequest(
        service_type=SVC_ENV_SHADE,
        request=REQ_SET_SHADE_LEVEL,
        zone=zone,
        component="Shades",
        logical_component="Lighting_controller",
        request_args=args,
    )


def stop(zone: str, address: str | None = None) -> ServiceRequest:
    args: dict[str, object] = {}
    if address is not None:
        args["Address1"] = address
    return ServiceRequest(
        service_type=SVC_ENV_SHADE,
        request=REQ_SHADE_STOP,
        zone=zone,
        component="Shades",
        logical_component="Lighting_controller",
        request_args=args,
    )
