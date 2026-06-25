"""Savant cover (shade) platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.shade import set_level, stop

from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant covers."""
    coordinator: SavantCoordinator = entry.runtime_data

    zones = coordinator.client.state_manager.active_zones
    entities = [SavantCover(coordinator, zone) for zone in zones]

    if entities:
        keys = []
        for entity in entities:
            keys.extend(entity.state_keys)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantCover(CoordinatorEntity[SavantCoordinator], CoverEntity):
    """Representation of a Savant shade."""

    _attr_device_class = CoverDeviceClass.SHADE
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
    )
    _attr_has_entity_name = True

    def __init__(self, coordinator: SavantCoordinator, zone: str) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"savant_cover_{zone}"
        self._attr_name = f"{zone} Shades"

    @property
    def state_keys(self) -> list[str]:
        return [f"{self._zone}.ShadeLevel"]

    @property
    def current_cover_position(self) -> int | None:
        val = self.coordinator.client.state_manager.get(f"{self._zone}.ShadeLevel")
        return int(val) if val is not None else None

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs.get("position")
        if position is not None:
            req = set_level(self._zone, int(position))
            await self.coordinator.send_service_request(req)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        req = stop(self._zone)
        await self.coordinator.send_service_request(req)

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.async_set_cover_position(position=100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.async_set_cover_position(position=0)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
