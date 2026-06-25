"""Savant light platform — individual dimmer and on/off light entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.config import LightEntity as SavantLightEntity
from pysavant.config import Room
from pysavant.services.switch import dimmer_set

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


def _first_address(raw: str) -> str:
    """Extract the first non-null address from the comma-separated field."""
    parts = (raw or "").split(",")
    for p in parts:
        p = p.strip()
        if p and p != "(null)":
            return p
    return ""


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant lights from the downloaded house configuration."""
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up lights")
        return

    entities: list[SavantLight] = []

    for room in cfg.rooms:
        for le in room.lights:
            addr = _first_address(le.addresses)
            if not addr:
                continue
            # Only dimmer lights go to the Light platform;
            # on/off (non-dimmer) lights go to the Switch platform
            if not le.is_dimmer:
                continue
            entities.append(SavantLight(coordinator, room, le, addr))

    async_add_entities(entities)


class SavantLight(CoordinatorEntity[SavantCoordinator], LightEntity):
    """Representation of a Savant individual light/dimmer entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: SavantLightEntity,
        address: str,
    ) -> None:
        """Initialize the light entity.

        Args:
            coordinator: The Savant coordinator.
            room: The room this light belongs to.
            entity: The light entity config from the SQLite database.
            address: The KNX group address for this entity.
        """
        super().__init__(coordinator)
        self._room = room
        self._entity = entity
        self._address = address
        self._zone = room.name

        # Use address as unique identifier — room names can change across
        # config downloads (e.g. "003 Office" → "Office"), which would
        # orphan entities in HA.
        self._attr_unique_id = f"savant_light_{address}"
        self._attr_name = entity.name
        self._attr_icon = "mdi:lightbulb"

        if entity.is_dimmer:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        # Track last seen state value so we only write HA state when it
        # actually changes. Without this, ANY state update from the coordinator
        # (even for unrelated entities) causes us to re-read the (possibly stale)
        # KNX value and override HA's optimistic UI state.
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

    # ── State keys used by this entity ────────────────────────────────────────

    @property
    def state_name(self) -> str:
        return self._entity.state_name

    # ── HA light properties ───────────────────────────────────────────────────

    @property
    def is_on(self) -> bool | None:
        state_name = self.state_name
        if not state_name:
            return None
        val = self.coordinator.client.state_manager.get(state_name)
        if val is None:
            return None
        return int(val) > 0

    @property
    def brightness(self) -> int | None:
        if not self._entity.is_dimmer:
            return None
        state_name = self.state_name
        if not state_name:
            return None
        val = self.coordinator.client.state_manager.get(state_name)
        if val is None:
            return None
        # Savant uses 0–100, HA uses 0–255
        return round(int(val) * 255 / 100)

    # ── Control ───────────────────────────────────────────────────────────────

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            level = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
        else:
            level = 100
        # Always use DimmerSet (not SwitchOn) — SwitchOn+Address1 is not
        # supported by this server; only DimmerSet handles per-address.
        req = dimmer_set(zone=self._zone, level=level, address=self._address)
        await self.coordinator.send_service_request(req)
        # Optimistic update: set state immediately so user sees instant
        # response. When KNX feedback arrives later (5-10s), the value
        # will match _last_state_value and the guard in
        # _handle_coordinator_update will skip the write — no flicker.
        self.coordinator.client.state_manager.handle_update(
            self.state_name, level
        )
        self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        # DimmerSet with level=0 instead of SwitchOff for per-address control
        req = dimmer_set(zone=self._zone, level=0, address=self._address)
        await self.coordinator.send_service_request(req)
        # Optimistic update: set state immediately.
        self.coordinator.client.state_manager.handle_update(
            self.state_name, 0
        )
        self._handle_coordinator_update()

    # ── Coordinator update ────────────────────────────────────────────────────

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our specific state key changed.

        Without this guard, ANY state update from the coordinator (even
        for unrelated entities) causes this entity to re-read its KNX
        value from the state cache and write it to HA — overriding HA's
        optimistic UI state before the KNX device has reported back.
        """
        state_name = self.state_name
        if not state_name:
            return
        val = self.coordinator.client.state_manager.get(state_name)
        if val == self._last_state_value:
            return
        self._last_state_value = val
        self.async_write_ha_state()
