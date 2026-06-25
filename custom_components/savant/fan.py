"""Savant fan platform — individual fan entities."""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.config import FanEntity as SavantFanEntity
from pysavant.config import Room
from pysavant.services.fan import set_level, turn_off

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)

# Default speed count for Savant fans
DEFAULT_SPEED_COUNT = 3


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
    """Set up Savant fans from the house configuration."""
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up fans")
        return

    entities: list[SavantFan] = []
    for room in cfg.rooms:
        for fe in room.fans:
            addr = _first_address(fe.addresses)
            if not addr:
                continue
            entities.append(SavantFan(coordinator, room, fe, addr))

    async_add_entities(entities)


class SavantFan(CoordinatorEntity[SavantCoordinator], FanEntity):
    """Representation of a Savant fan."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = DEFAULT_SPEED_COUNT

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: SavantFanEntity,
        address: str,
    ) -> None:
        super().__init__(coordinator)
        self._room = room
        self._entity = entity
        self._address = address
        self._zone = room.name

        self._attr_unique_id = f"savant_fan_{address}"
        self._attr_name = entity.name
        self._last_state_value: object = None

    # ── Device registry ───────────────────────────────────────────────────────

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"savant_room_{self._room.name}")},
            "name": self._room.display_name,
            "manufacturer": "Savant",
            "model": "Room Controller",
        }

    # ── State key ─────────────────────────────────────────────────────────────

    @property
    def state_key(self) -> str:
        return self._entity.state_name

    # ── HA fan properties ─────────────────────────────────────────────────────

    @property
    def is_on(self) -> bool | None:
        state_name = self.state_key
        if not state_name:
            return None
        val = self.coordinator.client.state_manager.get(state_name)
        if val is None:
            return None
        return int(val) > 0

    @property
    def percentage(self) -> int | None:
        state_name = self.state_key
        if not state_name:
            return None
        val = self.coordinator.client.state_manager.get(state_name)
        if val is None:
            return None
        level = int(val)
        if level == 0:
            return 0
        return math.ceil(level * 100 / DEFAULT_SPEED_COUNT)

    # ── Control ───────────────────────────────────────────────────────────────

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            req = turn_off(self._zone, address=self._address)
        else:
            level = max(1, math.ceil(percentage * DEFAULT_SPEED_COUNT / 100))
            req = set_level(self._zone, level, address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_turn_on(
        self, percentage: int | None = None, **kwargs: Any
    ) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            req = set_level(self._zone, DEFAULT_SPEED_COUNT, address=self._address)
            await self.coordinator.send_service_request(req)

    async def async_turn_off(self, **kwargs: Any) -> None:
        req = turn_off(self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our state key changed."""
        state_name = self.state_key
        if not state_name:
            return
        val = self.coordinator.client.state_manager.get(state_name)
        if val == self._last_state_value:
            return
        self._last_state_value = val
        self.async_write_ha_state()
