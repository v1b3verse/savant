"""Savant sensor platform — temperature and humidity sensors from HVAC entities."""

from __future__ import annotations

import logging
from typing import Any

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

from pysavant.config import HVACEntity as SavantHVACEntity
from pysavant.config import Room

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


def _first_address(raw: str) -> str:
    parts = (raw or "").split(",")
    for p in parts:
        p = p.strip()
        if p and p != "(null)":
            return p
    return ""


def _hvac_state_key(addr: str, prop: str) -> str:
    return f"KNX.HVAC_controller.{prop}_{addr}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant sensors from the house configuration."""
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up sensors")
        return

    entities: list[SavantSensor] = []

    for room in cfg.rooms:
        for he in room.hvac:
            addr = _first_address(he.addresses)
            if not addr:
                continue

            # Temperature sensor for each HVAC entity
            temp_unit = (
                UnitOfTemperature.CELSIUS if he.is_celsius
                else UnitOfTemperature.FAHRENHEIT
            )
            entities.append(
                SavantSensor(
                    coordinator=coordinator,
                    room=room,
                    entity=he,
                    address=addr,
                    key_suffix="ThermostatCurrentTemperature",
                    name_suffix="Temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    unit=temp_unit,
                )
            )

            # Humidity sensor for each HVAC entity (if supported by server)
            entities.append(
                SavantSensor(
                    coordinator=coordinator,
                    room=room,
                    entity=he,
                    address=addr,
                    key_suffix="ThermostatCurrentHumidity",
                    name_suffix="Humidity",
                    device_class=SensorDeviceClass.HUMIDITY,
                    unit=PERCENTAGE,
                )
            )

    async_add_entities(entities)


class SavantSensor(CoordinatorEntity[SavantCoordinator], SensorEntity):
    """Representation of a Savant sensor (temperature, humidity, etc.)."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: SavantHVACEntity,
        address: str,
        key_suffix: str,
        name_suffix: str,
        device_class: SensorDeviceClass,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._room = room
        self._entity = entity
        self._address = address
        self._key_suffix = key_suffix

        self._attr_unique_id = f"savant_sensor_{room.name}_{address}_{key_suffix}"
        self._attr_name = f"{entity.name} {name_suffix}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
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
    def state_key(self) -> str:
        return _hvac_state_key(self._address, self._key_suffix)

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.client.state_manager.get(self.state_key)
        return float(val) if val is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our state key changed."""
        val = self.coordinator.client.state_manager.get(self.state_key)
        if val == self._last_value:
            return
        self._last_value = val
        self.async_write_ha_state()
