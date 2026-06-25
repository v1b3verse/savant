"""Savant fan platform."""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.fan import set_level, turn_off

from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)

# Savant fans: 3 speeds (low=1, med=2, high=3)
SPEED_COUNT = 3


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant fans."""
    coordinator: SavantCoordinator = entry.runtime_data

    zones = coordinator.client.state_manager.active_zones
    entities = [SavantFan(coordinator, zone) for zone in zones]

    if entities:
        keys = []
        for entity in entities:
            keys.extend(entity.state_keys)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantFan(CoordinatorEntity[SavantCoordinator], FanEntity):
    """Representation of a Savant fan."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = SPEED_COUNT

    def __init__(self, coordinator: SavantCoordinator, zone: str) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"savant_fan_{zone}"
        self._attr_name = f"{zone} Fan"

    @property
    def state_keys(self) -> list[str]:
        return [
            f"{self._zone}.RoomFansAreOn",
            f"{self._zone}.Fan_controller.FanLevel",
        ]

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.client.state_manager.get(f"{self._zone}.RoomFansAreOn")
        if val is None:
            return None
        return bool(val)

    @property
    def percentage(self) -> int | None:
        val = self.coordinator.client.state_manager.get(f"{self._zone}.Fan_controller.FanLevel")
        if val is None:
            return None
        # Convert Savant 0-3 to HA percentage
        level = int(val)
        if level == 0:
            return 0
        return math.ceil(level * 100 / SPEED_COUNT)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            req = turn_off(self._zone)
        else:
            # Convert HA percentage to Savant 1-3
            level = max(1, math.ceil(percentage * SPEED_COUNT / 100))
            req = set_level(self._zone, level)
        await self.coordinator.send_service_request(req)

    async def async_turn_on(self, percentage: int | None = None, **kwargs: Any) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            req = set_level(self._zone, SPEED_COUNT)  # High
            await self.coordinator.send_service_request(req)

    async def async_turn_off(self, **kwargs: Any) -> None:
        req = turn_off(self._zone)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
