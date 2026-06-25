"""Push-based coordinator wrapping SavantClient."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from pysavant.client import SavantClient
from pysavant.models import DISRequest, ServiceRequest

from .const import DOMAIN

logger = logging.getLogger(__name__)


class SavantCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Push-based coordinator — no polling. State pushed via WebSocket."""

    def __init__(
        self, hass: HomeAssistant, client: SavantClient, entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=None,  # No polling
            config_entry=entry,
        )
        self.client = client
        self._registered_keys: set[str] = set()

    async def async_setup(self) -> None:
        """Connect and set up state subscriptions."""
        self.client.state_manager.subscribe("*", self._on_state_update)

    @callback
    def _on_state_update(self, key: str, value: Any) -> None:
        """Handle state update from Savant — push to HA."""
        self.async_set_updated_data(self.client.state_manager.get_all())

    async def register_state_keys(self, keys: list[str]) -> None:
        """Register additional state keys for monitoring."""
        new_keys = [k for k in keys if k not in self._registered_keys]
        if new_keys:
            await self.client.register_states(new_keys)
            self._registered_keys.update(new_keys)

    async def send_service_request(self, req: ServiceRequest) -> None:
        """Send a service request via the client."""
        await self.client.send_service_request(req)

    async def send_dis_request(self, req: DISRequest) -> None:
        """Send a DIS request via the client."""
        await self.client.send_dis_request(req)

    async def async_shutdown(self) -> None:
        """Disconnect the client."""
        await self.client.disconnect()
