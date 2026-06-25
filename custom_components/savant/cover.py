"""Savant cover platform — individual shade entities."""

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

from pysavant.config import Room, ShadeEntity
from pysavant.services.shade import close_cover, open_cover, set_level, stop

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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant covers (shades) from the house configuration."""
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up covers")
        return

    entities: list[SavantCover] = []
    for room in cfg.rooms:
        for se in room.shades:
            addr = _first_address(se.addresses)
            if not addr:
                continue
            entities.append(SavantCover(coordinator, room, se, addr))

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

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
        entity: ShadeEntity,
        address: str,
    ) -> None:
        """Initialize the shade entity.

        Shade state_name is often null in the database. The actual
        state key is derived from the zone's service configuration,
        falling back to a standard pattern.
        """
        super().__init__(coordinator)
        self._room = room
        self._entity = entity
        self._address = address
        self._zone = room.name

        self._attr_unique_id = f"savant_cover_{room.name}_{address}"
        self._attr_name = entity.name

        # Determine the actual state key for position
        self._position_key = self._resolve_position_key()
        self._last_position: object = None

    # ── Device registry ───────────────────────────────────────────────────────

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, f"savant_room_{self._room.name}")},
            "name": self._room.display_name,
            "manufacturer": "Savant",
            "model": "Room Controller",
        }

    # ── State key resolution ──────────────────────────────────────────────────

    def _resolve_position_key(self) -> str:
        """Determine the state key for shade position.

        First checks the entity's state_name from config.
        If null, derives the key using the component/logical_component
        from the zone's service configuration.
        """
        if self._entity.state_name:
            return self._entity.state_name

        scope = self.coordinator._find_shade_state_scope(self._room.name)
        return f"{scope}CurrentPosition_{self._address}"

    # ── HA cover properties ───────────────────────────────────────────────────

    @property
    def current_cover_position(self) -> int | None:
        val = self.coordinator.client.state_manager.get(self._position_key)
        if val is None:
            return None
        return int(val)

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    # ── Control ───────────────────────────────────────────────────────────────

    async def async_open_cover(self, **kwargs: Any) -> None:
        req = open_cover(self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_close_cover(self, **kwargs: Any) -> None:
        req = close_cover(self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        req = stop(self._zone, address=self._address)
        await self.coordinator.send_service_request(req)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position = kwargs.get("position")
        if position is not None:
            req = set_level(self._zone, int(position), address=self._address)
            await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our position key changed."""
        val = self.coordinator.client.state_manager.get(self._position_key)
        if val == self._last_position:
            return
        self._last_position = val
        self.async_write_ha_state()
