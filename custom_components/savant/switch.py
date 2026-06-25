"""Savant switch platform — infrastructure devices + on/off lights.

Infrastructure devices include pumps, valves, ventilation fans,
radiant floor heating, towel warmers, garage doors, HVAC switches,
and spare relays. Non-dimmer room lights are also exposed as switches
for simple on/off control.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.config import InfrastructureDevice, LightEntity, Room
from pysavant.services.switch import switch_off, switch_on

from .const import DOMAIN, INFRASTRUCTURE_DEVICE_CLASSES
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


def _first_address(raw: str) -> str:
    parts = (raw or "").split(",")
    for p in parts:
        p = p.strip()
        if p and p != "(null)":
            return p
    return ""


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant switches from the house configuration.

    Two sources:
    1. Infrastructure devices from hidden zones (pumps, valves, relays, etc.)
    2. Non-dimmer room lights (on/off only)
    """
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up switches")
        return

    entities: list[SavantSwitch] = []

    # 1. Infrastructure devices
    for infra in cfg.infrastructure:
        if not infra.address:
            continue
        entities.append(
            SavantInfrastructureSwitch(coordinator, infra)
        )

    # 2. Non-dimmer room lights
    for room in cfg.rooms:
        for le in room.lights:
            if le.is_dimmer:
                continue
            addr = _first_address(le.addresses)
            if not addr:
                continue
            entities.append(
                SavantLightSwitch(coordinator, room, le, addr)
            )

    async_add_entities(entities)


# ── Base switch ──────────────────────────────────────────────────────────────


class SavantSwitch(CoordinatorEntity[SavantCoordinator], SwitchEntity):
    """Base class for Savant switches."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SavantCoordinator,
        zone: str,
        name: str,
        unique_id: str,
        state_key: str,
        address: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._state_key = state_key
        self._address = address
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._last_state_value: object = None

    @property
    def is_on(self) -> bool | None:
        if not self._state_key:
            return None
        val = self.coordinator.client.state_manager.get(self._state_key)
        if val is None:
            return None
        return int(val) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        req = switch_on(zone=self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_turn_off(self, **kwargs: Any) -> None:
        req = switch_off(zone=self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our state key changed."""
        if not self._state_key:
            return
        val = self.coordinator.client.state_manager.get(self._state_key)
        if val == self._last_state_value:
            return
        self._last_state_value = val
        self.async_write_ha_state()


# ── Infrastructure switch ────────────────────────────────────────────────────


class SavantInfrastructureSwitch(SavantSwitch):
    """A switch for an infrastructure device (pump, valve, relay, etc.)."""

    def __init__(
        self,
        coordinator: SavantCoordinator,
        infra: InfrastructureDevice,
    ) -> None:
        device_class = INFRASTRUCTURE_DEVICE_CLASSES.get(
            infra.category, INFRASTRUCTURE_DEVICE_CLASSES["other"]
        )
        super().__init__(
            coordinator=coordinator,
            zone=infra.zone,
            name=infra.name,
            unique_id=f"savant_switch_{infra.zone}_{infra.address}",
            state_key=infra.state_name,
            address=infra.address,
        )
        self._infra = infra
        self._attr_device_class = device_class

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, "savant_infrastructure")},
            "name": "Infrastructure",
            "manufacturer": "Savant",
            "model": "Infrastructure Device",
        }


# ── Light-based switch (non-dimmer) ─────────────────────────────────────────


class SavantLightSwitch(SavantSwitch):
    """A switch for a non-dimmer room light (on/off only)."""

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: LightEntity,
        address: str,
    ) -> None:
        super().__init__(
            coordinator=coordinator,
            zone=room.name,
            name=entity.name,
            unique_id=f"savant_switch_{room.name}_{address}",
            state_key=entity.state_name,
            address=address,
        )
        self._room = room
        self._entity = entity

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"savant_room_{self._room.name}")},
            "name": self._room.display_name,
            "manufacturer": "Savant",
            "model": "Room Controller",
        }
