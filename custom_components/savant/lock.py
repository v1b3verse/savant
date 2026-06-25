"""Savant lock platform — door lock entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.config import Room
from pysavant.services.lock import lock as svc_lock
from pysavant.services.lock import unlock as svc_unlock

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)

# Lock state key pattern — door locks are per-room
_LOCK_STATE_KEY_FMT = "{zone}.RoomDoorLocksAreOpen"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant locks from the house configuration.

    Discovers zones that support door locking. Currently uses room-level
    lock state (one lock entity per room that has security capabilities).
    """
    coordinator: SavantCoordinator = entry.runtime_data
    cfg = coordinator.house_config
    if cfg is None:
        logger.warning("House config not available — cannot set up locks")
        return

    entities: list[SavantLock] = []
    for room in cfg.rooms:
        # Rooms with security capabilities may have door locks
        # Create a lock entity for each room
        if room.has_security:
            entities.append(SavantLock(coordinator, room))

    async_add_entities(entities)


class SavantLock(CoordinatorEntity[SavantCoordinator], LockEntity):
    """Representation of a Savant door lock."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SavantCoordinator,
        room: Room,
    ) -> None:
        super().__init__(coordinator)
        self._room = room
        self._zone = room.name

        self._attr_unique_id = f"savant_lock_{room.room_id}"
        self._attr_name = f"{room.name} Lock"
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
    def _state_key(self) -> str:
        return _LOCK_STATE_KEY_FMT.format(zone=self._zone)

    @property
    def is_locked(self) -> bool | None:
        val = self.coordinator.client.state_manager.get(self._state_key)
        if val is None:
            return None
        # Savant: "RoomDoorLocksAreOpen" — inverted logic
        return not bool(val)

    # ── Control ───────────────────────────────────────────────────────────────

    async def async_lock(self, **kwargs: Any) -> None:
        req = svc_lock(self._zone)
        await self.coordinator.send_service_request(req)

    async def async_unlock(self, **kwargs: Any) -> None:
        req = svc_unlock(self._zone)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-read state only when our state key changed."""
        val = self.coordinator.client.state_manager.get(self._state_key)
        if val == self._last_value:
            return
        self._last_value = val
        self.async_write_ha_state()
