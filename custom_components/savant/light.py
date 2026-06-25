"""Savant light platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.lighting import set_brightness, turn_off, turn_on

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant lights."""
    coordinator: SavantCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Register for active zones and discover lights
    await coordinator.register_state_keys(["global.ActiveZones"])

    zones = coordinator.client.state_manager.active_zones
    entities = [SavantLight(coordinator, zone) for zone in zones]

    if entities:
        # Register state keys for all light entities
        keys = []
        for entity in entities:
            keys.extend(entity.state_keys)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantLight(CoordinatorEntity[SavantCoordinator], LightEntity):
    """Representation of a Savant light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_has_entity_name = True

    def __init__(self, coordinator: SavantCoordinator, zone: str) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"savant_light_{zone}"
        self._attr_name = f"{zone} Lights"

    @property
    def state_keys(self) -> list[str]:
        return [
            f"{self._zone}.RoomLightsAreOn",
            f"{self._zone}.Lighting_controller.RoomBrightness",
        ]

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.client.state_manager.get(f"{self._zone}.RoomLightsAreOn")
        if val is None:
            return None
        return bool(val)

    @property
    def brightness(self) -> int | None:
        val = self.coordinator.client.state_manager.get(
            f"{self._zone}.Lighting_controller.RoomBrightness"
        )
        if val is None:
            return None
        # Savant uses 0-100, HA uses 0-255
        return round(int(val) * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            # Convert HA 0-255 to Savant 0-100
            level = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            req = set_brightness(self._zone, level)
        else:
            req = turn_on(self._zone)
        await self.coordinator.send_service_request(req)

    async def async_turn_off(self, **kwargs: Any) -> None:
        req = turn_off(self._zone)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
