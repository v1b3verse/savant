"""Savant sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.climate import hvac_state_key

from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant sensors."""
    coordinator: SavantCoordinator = entry.runtime_data

    zones = coordinator.client.state_manager.active_zones
    entities: list[SavantSensor] = []

    for zone in zones:
        entities.append(
            SavantSensor(
                coordinator,
                zone,
                key_suffix="ThermostatCurrentTemperature",
                name_suffix="Temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                unit=UnitOfTemperature.FAHRENHEIT,
            )
        )
        entities.append(
            SavantSensor(
                coordinator,
                zone,
                key_suffix="ThermostatCurrentHumidity",
                name_suffix="Humidity",
                device_class=SensorDeviceClass.HUMIDITY,
                unit=PERCENTAGE,
            )
        )

    if entities:
        keys = []
        for entity in entities:
            keys.append(entity.state_key)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantSensor(CoordinatorEntity[SavantCoordinator], SensorEntity):
    """Representation of a Savant sensor (temperature, humidity, etc.)."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: SavantCoordinator,
        zone: str,
        key_suffix: str,
        name_suffix: str,
        device_class: SensorDeviceClass,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._key_suffix = key_suffix
        self._attr_unique_id = f"savant_sensor_{zone}_{key_suffix}"
        self._attr_name = f"{zone} {name_suffix}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit

    @property
    def state_key(self) -> str:
        return hvac_state_key(self._zone, self._key_suffix)

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.client.state_manager.get(self.state_key)
        return float(val) if val is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
