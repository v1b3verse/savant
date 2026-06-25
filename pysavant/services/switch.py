"""Service request builders for individual switch/relay entities.

Controls pumps, valves, ventilation relays, towel warmers,
radiant floor heating, and any other on/off infrastructure devices.
"""

from pysavant.models import ServiceRequest
from pysavant.protocol import SVC_ENV_LIGHTING


def switch_on(
    zone: str,
    address: str | None = None,
    component: str = "KNX",
    logical_component: str = "Lighting_controller",
    variant_id: str = "1",
) -> ServiceRequest:
    """Turn a switch entity on (BrightnessLevel=100, SwitchOn).

    If *address* is provided, it is included as ``Address1`` in the
    request arguments so only the KNX device at that group address
    receives the command.

    Note: the Savant app uses ``Address1`` (1-based), not ``Address0``,
    because ``getAddrScheme()`` returns 1 (ONE_RELATIVE) in the
    decompiled ``SavantEntities.java``.
    """
    args: dict[str, object] = {"BrightnessLevel": 100}
    if address is not None:
        args["Address1"] = address
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request="SwitchOn",
        zone=zone,
        component=component,
        logical_component=logical_component,
        variant_id=variant_id,
        request_args=args,
    )


def switch_off(
    zone: str,
    address: str | None = None,
    component: str = "KNX",
    logical_component: str = "Lighting_controller",
    variant_id: str = "1",
) -> ServiceRequest:
    """Turn a switch entity off (BrightnessLevel=0, SwitchOff).

    If *address* is provided, it is included as ``Address1`` in the
    request arguments so only the KNX device at that group address
    receives the command.
    """
    args: dict[str, object] = {"BrightnessLevel": 0}
    if address is not None:
        args["Address1"] = address
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request="SwitchOff",
        zone=zone,
        component=component,
        logical_component=logical_component,
        variant_id=variant_id,
        request_args=args,
    )


def dimmer_set(
    zone: str,
    level: int,
    address: str | None = None,
    component: str = "KNX",
    logical_component: str = "Lighting_controller",
    variant_id: str = "1",
) -> ServiceRequest:
    """Set a dimmer entity to a specific level (0-100).

    If *address* is provided, it is included as ``Address1`` so only
    the KNX device at that group address receives the command.
    """
    if not 0 <= level <= 100:
        raise ValueError(f"Level must be 0-100, got {level}")
    args: dict[str, object] = {"DimmerLevel": level}
    if address is not None:
        args["Address1"] = address
    return ServiceRequest(
        service_type=SVC_ENV_LIGHTING,
        request="DimmerSet",
        zone=zone,
        component=component,
        logical_component=logical_component,
        variant_id=variant_id,
        request_args=args,
    )
