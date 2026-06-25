"""Savant climate platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.climate import (
    hvac_state_key,
    set_single_setpoint,
)

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant climate entities."""
    coordinator: SavantCoordinator = hass.data[DOMAIN][entry.entry_id]

    zones = coordinator.client.state_manager.active_zones
    entities = [SavantClimate(coordinator, zone) for zone in zones]

    if entities:
        keys = []
        for entity in entities:
            keys.extend(entity.state_keys)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantClimate(CoordinatorEntity[SavantCoordinator], ClimateEntity):
    """Representation of a Savant thermostat."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]

    def __init__(self, coordinator: SavantCoordinator, zone: str) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"savant_climate_{zone}"
        self._attr_name = f"{zone} HVAC"

    @property
    def state_keys(self) -> list[str]:
        return [
            hvac_state_key(self._zone, "ThermostatCurrentSetPoint_1"),
            hvac_state_key(self._zone, "ThermostatCurrentSetPoint_2"),
            hvac_state_key(self._zone, "ThermostatCurrentTemperature"),
            hvac_state_key(self._zone, "ThermostatCurrentHumidity"),
            hvac_state_key(self._zone, "ThermostatOperatingState"),
        ]

    @property
    def current_temperature(self) -> float | None:
        val = self.coordinator.client.state_manager.get(
            hvac_state_key(self._zone, "ThermostatCurrentTemperature")
        )
        return float(val) if val is not None else None

    @property
    def current_humidity(self) -> float | None:
        val = self.coordinator.client.state_manager.get(
            hvac_state_key(self._zone, "ThermostatCurrentHumidity")
        )
        return float(val) if val is not None else None

    @property
    def target_temperature(self) -> float | None:
        val = self.coordinator.client.state_manager.get(
            hvac_state_key(self._zone, "ThermostatCurrentSetPoint_1")
        )
        return float(val) if val is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        state = self.coordinator.client.state_manager.get(
            hvac_state_key(self._zone, "ThermostatOperatingState")
        )
        if state is None or state == 0:
            return HVACMode.OFF
        return HVACMode.HEAT_COOL

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        req = set_single_setpoint(self._zone, float(temp))
        await self.coordinator.send_service_request(req)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        # Savant HVAC mode is primarily controlled by the thermostat itself
        logger.debug("Set HVAC mode %s for %s (not directly supported)", hvac_mode, self._zone)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
