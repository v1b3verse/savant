"""Savant climate platform — individual HVAC/thermostat entities."""

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

from pysavant.config import HVACEntity as SavantHVACEntity
from pysavant.config import Room
from pysavant.services.climate import set_single_setpoint

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
    """Build per-address HVAC state key.

    Pattern: KNX.HVAC_controller.{Property}_{addr}
    """
    return f"KNX.HVAC_controller.{prop}_{addr}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant climate entities from the house configuration."""
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up climate")
        return

    entities: list[SavantClimate] = []
    for room in cfg.rooms:
        for he in room.hvac:
            addr = _first_address(he.addresses)
            if not addr:
                continue
            entities.append(SavantClimate(coordinator, room, he, addr))

    async_add_entities(entities)


class SavantClimate(CoordinatorEntity[SavantCoordinator], ClimateEntity):
    """Representation of a Savant HVAC/thermostat entity."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: SavantHVACEntity,
        address: str,
    ) -> None:
        """Initialize the climate entity.

        Args:
            coordinator: The Savant coordinator.
            room: The room this HVAC belongs to.
            entity: The HVAC entity config from the SQLite database.
            address: The KNX group address for this entity.
        """
        super().__init__(coordinator)
        self._room = room
        self._entity = entity
        self._address = address
        self._zone = room.name

        self._attr_unique_id = f"savant_climate_{room.name}_{address}"
        self._attr_name = entity.name

        # Temperature unit from config
        if entity.is_celsius:
            self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        else:
            self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT

        # Temperature range from config
        self._attr_min_temp = entity.temp_min
        self._attr_max_temp = entity.temp_max

        # HVAC modes based on capabilities
        modes = [HVACMode.OFF]
        if entity.has_heat:
            modes.append(HVACMode.HEAT)
        if entity.has_cool:
            modes.append(HVACMode.COOL)
        if entity.has_auto:
            modes.append(HVACMode.HEAT_COOL)
        self._attr_hvac_modes = modes

        # Track last seen values for each tracked state key
        self._last_temperature: object = None
        self._last_setpoint: object = None
        self._last_hvac_state: object = None
        self._last_humidity: object = None

    # ── Device registry ───────────────────────────────────────────────────────

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"savant_room_{self._room.name}")},
            "name": self._room.display_name,
            "manufacturer": "Savant",
            "model": "Room Controller",
        }

    # ── State key helpers ─────────────────────────────────────────────────────

    @property
    def _temperature_key(self) -> str:
        return _hvac_state_key(self._address, "ThermostatCurrentTemperature")

    @property
    def _setpoint_key(self) -> str:
        return _hvac_state_key(self._address, "ThermostatCurrentSetPoint")

    @property
    def _hvac_state_key(self) -> str:
        return _hvac_state_key(self._address, "ThermostatHVACState")

    @property
    def _humidity_key(self) -> str:
        return _hvac_state_key(self._address, "ThermostatCurrentHumidity")

    # ── HA climate properties ─────────────────────────────────────────────────

    @property
    def current_temperature(self) -> float | None:
        val = self.coordinator.client.state_manager.get(self._temperature_key)
        return float(val) if val is not None else None

    @property
    def target_temperature(self) -> float | None:
        val = self.coordinator.client.state_manager.get(self._setpoint_key)
        return float(val) if val is not None else None

    @property
    def current_humidity(self) -> float | None:
        val = self.coordinator.client.state_manager.get(self._humidity_key)
        return float(val) if val is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        val = self.coordinator.client.state_manager.get(self._hvac_state_key)
        if val is None or val == 0 or val == "off":
            return HVACMode.OFF
        val_str = str(val).lower()
        if "heat" in val_str:
            return HVACMode.HEAT
        if "cool" in val_str:
            return HVACMode.COOL
        if "auto" in val_str:
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    # ── Control ───────────────────────────────────────────────────────────────

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        req = set_single_setpoint(self._zone, float(temp), address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        # HVAC mode control is primarily handled by the thermostat itself
        logger.debug(
            "Set HVAC mode %s for %s (may not be directly supported)",
            hvac_mode,
            self.entity_id,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when one of our tracked state keys changed."""
        temp = self.coordinator.client.state_manager.get(self._temperature_key)
        setpoint = self.coordinator.client.state_manager.get(self._setpoint_key)
        hvac = self.coordinator.client.state_manager.get(self._hvac_state_key)
        humidity = self.coordinator.client.state_manager.get(self._humidity_key)

        if (temp == self._last_temperature
                and setpoint == self._last_setpoint
                and hvac == self._last_hvac_state
                and humidity == self._last_humidity):
            return  # No change for this entity

        self._last_temperature = temp
        self._last_setpoint = setpoint
        self._last_hvac_state = hvac
        self._last_humidity = humidity
        self.async_write_ha_state()
