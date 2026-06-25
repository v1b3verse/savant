"""Savant lock platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.lock import lock as svc_lock
from pysavant.services.lock import unlock as svc_unlock

from .const import DOMAIN
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant locks."""
    coordinator: SavantCoordinator = hass.data[DOMAIN][entry.entry_id]

    zones = coordinator.client.state_manager.active_zones
    entities = [SavantLock(coordinator, zone) for zone in zones]

    if entities:
        keys = []
        for entity in entities:
            keys.extend(entity.state_keys)
        await coordinator.register_state_keys(keys)

    async_add_entities(entities)


class SavantLock(CoordinatorEntity[SavantCoordinator], LockEntity):
    """Representation of a Savant lock."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SavantCoordinator, zone: str) -> None:
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"savant_lock_{zone}"
        self._attr_name = f"{zone} Lock"

    @property
    def state_keys(self) -> list[str]:
        return [f"{self._zone}.RoomDoorLocksAreOpen"]

    @property
    def is_locked(self) -> bool | None:
        # Savant: "RoomDoorLocksAreOpen" — inverted logic
        val = self.coordinator.client.state_manager.get(f"{self._zone}.RoomDoorLocksAreOpen")
        if val is None:
            return None
        return not bool(val)

    async def async_lock(self, **kwargs: Any) -> None:
        req = svc_lock(self._zone)
        await self.coordinator.send_service_request(req)

    async def async_unlock(self, **kwargs: Any) -> None:
        req = svc_unlock(self._zone)
        await self.coordinator.send_service_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
