"""Savant scene platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pysavant.services.scene import apply_scene

from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant scenes."""
    # Scenes are discovered dynamically via DIS requests
    # For now, this is a placeholder — scenes will be populated
    # after the coordinator fetches the scene list
    pass


class SavantScene(Scene):
    """Representation of a Savant scene."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SavantCoordinator, scene_id: str, name: str) -> None:
        self._coordinator = coordinator
        self._scene_id = scene_id
        self._attr_unique_id = f"savant_scene_{scene_id}"
        self._attr_name = name

    async def async_activate(self, **kwargs: Any) -> None:
        req = apply_scene(self._scene_id)
        await self._coordinator.send_dis_request(req)
