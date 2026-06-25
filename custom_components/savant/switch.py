"""Savant switch platform — scenes as toggleable switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pysavant.services.scene import apply_scene, remove_scene

from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant switches (scenes as toggles)."""
    # Scenes as switches will be populated dynamically
    pass


class SavantSwitch(CoordinatorEntity[SavantCoordinator], SwitchEntity):
    """Representation of a Savant scene as a toggleable switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SavantCoordinator,
        scene_id: str,
        name: str,
        state_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._scene_id = scene_id
        self._state_key = state_key
        self._attr_unique_id = f"savant_switch_{scene_id}"
        self._attr_name = name

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.client.state_manager.get(self._state_key)
        if val is None:
            return None
        return bool(val)

    async def async_turn_on(self, **kwargs: Any) -> None:
        req = apply_scene(self._scene_id)
        await self.coordinator.send_dis_request(req)

    async def async_turn_off(self, **kwargs: Any) -> None:
        req = remove_scene(self._scene_id)
        await self.coordinator.send_dis_request(req)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
