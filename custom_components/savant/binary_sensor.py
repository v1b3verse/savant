"""Savant binary sensor platform — security zone contact/motion/smoke sensors."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.config import Room, SecurityEntity

from .const import (
    BINARY_SENSOR_DEFAULT_CLASS,
    BINARY_SENSOR_PREFIX_CLASSES,
    DOMAIN,
)
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


def _classify_security_entity(name: str) -> BinarySensorDeviceClass:
    """Determine device class from entity name prefix.

    Uses the configurable mapping in const.py, falling back to
    BINARY_SENSOR_DEFAULT_CLASS.
    """
    for prefix, device_class in BINARY_SENSOR_PREFIX_CLASSES.items():
        if name.startswith(prefix):
            return device_class
    return BINARY_SENSOR_DEFAULT_CLASS


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant binary sensors from the house configuration.

    Discovers security zone entities where zone_number > 0.
    Partition entries (zone_number == 0) are keypads, not sensors.
    """
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up binary sensors")
        return

    entities: list[SavantBinarySensor] = []
    for room in cfg.rooms:
        for se in room.security:
            # Partition entries are keypads, not sensors
            if se.zone_number == 0:
                continue
            entities.append(SavantBinarySensor(coordinator, room, se))

    async_add_entities(entities)


class SavantBinarySensor(CoordinatorEntity[SavantCoordinator], BinarySensorEntity):
    """Representation of a Savant security zone sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: SecurityEntity,
    ) -> None:
        super().__init__(coordinator)
        self._room = room
        self._entity = entity

        # Multiple zones in the same room can have sensors with the same
        # name (e.g. two "MG.007D" entities with different zone_number).
        # Include zone_number + a suffix from the state key for uniqueness.
        prop = ""
        if entity.state_name:
            key_part = entity.state_name.rsplit(".", 1)[-1]
            m = re.match(r"^([A-Za-z]+)(?:_\d+)?$", key_part)
            if m:
                prop = m.group(1)
        suffix = f"_{prop}" if prop else ""
        self._attr_unique_id = (
            f"savant_binary_sensor_{room.room_id}"
            f"_z{entity.zone_number}{suffix}"
        )
        self._attr_name = entity.name
        self._attr_device_class = _classify_security_entity(entity.name)
        self._last_value: object = None

    # ── Device registry ───────────────────────────────────────────────────────

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"savant_room_{self._room.name}")},
            "name": self._room.display_name,
            "manufacturer": "Savant",
            "model": "Room Controller",
        }

    # ── State ─────────────────────────────────────────────────────────────────

    @property
    def is_on(self) -> bool | None:
        state_name = self._entity.state_name
        if not state_name:
            return None
        val = self.coordinator.client.state_manager.get(state_name)
        if val is None:
            return None
        # Server may send "Open" (string) or True (bool) — handle both
        if isinstance(val, str):
            return val.lower() == "open"
        return bool(val)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our state key changed."""
        state_name = self._entity.state_name
        if not state_name:
            return
        val = self.coordinator.client.state_manager.get(state_name)
        if val == self._last_value:
            return
        self._last_value = val
        self.async_write_ha_state()
