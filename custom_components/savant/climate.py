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

        self._attr_unique_id = f"savant_climate_{address}"
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
        self._last_mode_auto: object = None
        self._last_mode_cool: object = None
        self._last_mode_heat: object = None
        self._last_mode_off: object = None

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

    @property
    def _hvac_mode_auto_key(self) -> str:
        return _hvac_state_key(self._address, "IsCurrentHVACModeAuto")

    @property
    def _hvac_mode_cool_key(self) -> str:
        return _hvac_state_key(self._address, "IsCurrentHVACModeCool")

    @property
    def _hvac_mode_heat_key(self) -> str:
        return _hvac_state_key(self._address, "IsCurrentHVACModeHeat")

    @property
    def _hvac_mode_off_key(self) -> str:
        return _hvac_state_key(self._address, "IsCurrentHVACModeOff")

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
        """Return the thermostat set mode (not the running HVAC state).

        The Savant host exposes the set mode via boolean state keys:
          IsCurrentHVACModeAuto, IsCurrentHVACModeCool,
          IsCurrentHVACModeHeat, IsCurrentHVACModeOff.

        ThermostatHVACState (the "running" HVAC state) is a different
        value — "Idle", "Cooling", "Heating" — and must not be conflated
        with the set mode.
        """
        sm = self.coordinator.client.state_manager

        # Check boolean mode states first (these are the authoritative
        # indicator of the thermostat's set mode).
        if sm.get(self._hvac_mode_off_key, 0) == 1:
            return HVACMode.OFF
        if sm.get(self._hvac_mode_heat_key, 0) == 1:
            return HVACMode.HEAT
        if sm.get(self._hvac_mode_cool_key, 0) == 1:
            return HVACMode.COOL
        if sm.get(self._hvac_mode_auto_key, 0) == 1:
            return HVACMode.HEAT_COOL

        # Fallback: check ThermostatHVACState (the running state)
        val = sm.get(self._hvac_state_key)
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
        # On some hosts the KNX bus is written via state/set rather
        # than service/request. The official ServiceRequest path is
        # silently ignored by this host.
        await self.coordinator.set_state(self._setpoint_key, int(round(temp)))
        # Optimistic update: show the new setpoint immediately
        self.coordinator.client.state_manager.handle_update(
            self._setpoint_key, int(round(temp))
        )
        self._handle_coordinator_update()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode via state/set on the mode boolean keys."""
        # Clear all mode flags first, then set the requested one
        off_val = 1 if hvac_mode == HVACMode.OFF else 0
        heat_val = 1 if hvac_mode == HVACMode.HEAT else 0
        cool_val = 1 if hvac_mode == HVACMode.COOL else 0
        auto_val = 1 if hvac_mode == HVACMode.HEAT_COOL else 0

        await self.coordinator.set_state(self._hvac_mode_off_key, off_val)
        await self.coordinator.set_state(self._hvac_mode_heat_key, heat_val)
        await self.coordinator.set_state(self._hvac_mode_cool_key, cool_val)
        await self.coordinator.set_state(self._hvac_mode_auto_key, auto_val)

        # Optimistic update
        sm = self.coordinator.client.state_manager
        sm.handle_update(self._hvac_mode_off_key, off_val)
        sm.handle_update(self._hvac_mode_heat_key, heat_val)
        sm.handle_update(self._hvac_mode_cool_key, cool_val)
        sm.handle_update(self._hvac_mode_auto_key, auto_val)
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when one of our tracked state keys changed."""
        sm = self.coordinator.client.state_manager
        temp = sm.get(self._temperature_key)
        setpoint = sm.get(self._setpoint_key)
        hvac = sm.get(self._hvac_state_key)
        humidity = sm.get(self._humidity_key)
        mode_auto = sm.get(self._hvac_mode_auto_key)
        mode_cool = sm.get(self._hvac_mode_cool_key)
        mode_heat = sm.get(self._hvac_mode_heat_key)
        mode_off = sm.get(self._hvac_mode_off_key)

        if (temp == self._last_temperature
                and setpoint == self._last_setpoint
                and hvac == self._last_hvac_state
                and humidity == self._last_humidity
                and mode_auto == self._last_mode_auto
                and mode_cool == self._last_mode_cool
                and mode_heat == self._last_mode_heat
                and mode_off == self._last_mode_off):
            return  # No change for this entity

        self._last_temperature = temp
        self._last_setpoint = setpoint
        self._last_hvac_state = hvac
        self._last_humidity = humidity
        self._last_mode_auto = mode_auto
        self._last_mode_cool = mode_cool
        self._last_mode_heat = mode_heat
        self._last_mode_off = mode_off
        self.async_write_ha_state()
