"""Lighting service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import REQ_ROOM_SET_BRIGHTNESS, SVC_ENV_LIGHTING


def turn_on(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request=REQ_ROOM_SET_BRIGHTNESS,
        zone=zone,
        component="Lights",
        logical_component="Lighting_controller",
        request_args={"BrightnessLevel": 100, "USE_LAST_DIMMER_VALUE": 1},
    )


def turn_off(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request=REQ_ROOM_SET_BRIGHTNESS,
        zone=zone,
        component="Lights",
        logical_component="Lighting_controller",
        request_args={"BrightnessLevel": 0, "USE_LAST_DIMMER_VALUE": 1},
    )


def set_brightness(zone: str, level: int) -> ServiceRequest:
    """Set brightness level (0-100)."""
    if not 0 <= level <= 100:
        raise ValueError(f"Brightness must be 0-100, got {level}")
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request=REQ_ROOM_SET_BRIGHTNESS,
        zone=zone,
        component="Lights",
        logical_component="Lighting_controller",
        request_args={"BrightnessLevel": level, "USE_LAST_DIMMER_VALUE": 0},
    )
