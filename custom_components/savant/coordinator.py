"""Push-based coordinator wrapping SavantClient.

Downloads the house configuration on setup, subscribes to all entity
state keys, and pushes updates to Home Assistant.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from pysavant.client import SavantClient
from pysavant.config import HouseConfig
from pysavant.models import DISRequest, ServiceRequest

from .const import (
    DOMAIN,
    HVAC_STATE_PROPERTIES,
    SECURITY_PARTITION_PROPERTIES,
    SECURITY_ZONE_PROPERTIES,
    SHADE_STATE_PROPERTIES,
)

logger = logging.getLogger(__name__)


class SavantCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Push-based coordinator — no polling. State pushed via WebSocket.

    On setup, the coordinator downloads the house configuration and
    subscribes to every entity's state keys so real-time KNX updates
    flow into Home Assistant automatically.
    """

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
        self.house_config: HouseConfig | None = None

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def async_setup(self) -> None:
        """Connect, download config, subscribe to all state keys."""
        # Subscribe to state updates first
        self.client.state_manager.subscribe("*", self._on_state_update)

        # Download the house configuration
        self.house_config = await self.client.get_config()
        logger.info(
            "Downloaded config: %d rooms, %d infrastructure devices",
            len(self.house_config.rooms),
            len(self.house_config.infrastructure),
        )

        # Collect and register all state keys
        all_keys = self._collect_all_state_keys()
        logger.info("Registering %d state keys", len(all_keys))
        await self.register_state_keys(all_keys)

        # Push initial state into HA
        self.async_set_updated_data(self.client.state_manager.get_all())

    # ── State key collection ───────────────────────────────────────────────────

    def _collect_all_state_keys(self) -> list[str]:
        """Collect every state key for all entities in the config."""
        cfg = self.house_config
        if cfg is None:
            return []

        keys: set[str] = set()

        # Global
        keys.add("global.ActiveZones")
        keys.add("global.ActiveScene")

        def _first_addr(raw: str) -> str:
            parts = (raw or "").split(",")
            for p in parts:
                p = p.strip()
                if p and p != "(null)":
                    return p
            return ""

        # ── Lights (room entities) ──
        for room in cfg.rooms:
            for le in room.lights:
                if le.state_name:
                    keys.add(le.state_name)

        # ── Lights (infrastructure / hidden-zone entities) ──
        for d in cfg.infrastructure:
            if d.state_name:
                keys.add(d.state_name)

        # ── HVAC ──
        for room in cfg.rooms:
            for he in room.hvac:
                if he.state_name:
                    keys.add(he.state_name)
                addr = _first_addr(he.addresses)
                if addr:
                    scope = "KNX.HVAC_controller."
                    for prop in HVAC_STATE_PROPERTIES:
                        keys.add(f"{scope}{prop}_{addr}")

        # ── Fans ──
        for room in cfg.rooms:
            for fe in room.fans:
                if fe.state_name:
                    keys.add(fe.state_name)

        # ── Shades ──
        for room in cfg.rooms:
            for shade in room.shades:
                if shade.state_name:
                    keys.add(shade.state_name)
                addr = _first_addr(shade.addresses)
                if addr:
                    scope = self._find_shade_state_scope(room.name)
                    for prop in SHADE_STATE_PROPERTIES:
                        keys.add(f"{scope}{prop}_{addr}")

        # ── Security ──
        for room in cfg.rooms:
            for se in room.security:
                if se.state_name:
                    keys.add(se.state_name)
                scope = "Security System.Security_system."
                if se.zone_number == 0:
                    for prop in SECURITY_PARTITION_PROPERTIES:
                        keys.add(f"{scope}{prop}_{se.partition_number}")
                else:
                    for prop in SECURITY_ZONE_PROPERTIES:
                        keys.add(f"{scope}{prop}_{se.zone_number}")

        return sorted(keys)

    def _find_shade_state_scope(self, room_name: str) -> str:
        """Derive the state key scope for shades in a room.

        Looks up the ZoneService entry for this room's shade service
        to determine the correct component/logical_component prefix.
        Falls back to 'KNX.Shade_controller.' if not found.
        """
        cfg = self.house_config
        if cfg is None:
            return "KNX.Shade_controller."
        for zs in cfg.zones:
            if zs.zone_name == room_name and "shade" in zs.service.lower():
                return f"{zs.component}.{zs.logical_component}."
        return "KNX.Shade_controller."

    # ── State update handler ───────────────────────────────────────────────────

    @callback
    def _on_state_update(self, key: str, value: Any) -> None:
        """Handle state update from Savant — push to HA."""
        self.async_set_updated_data(self.client.state_manager.get_all())

    # ── State key registration (de-duplicated) ─────────────────────────────────

    async def register_state_keys(self, keys: list[str]) -> None:
        """Register additional state keys for monitoring."""
        new_keys = [k for k in keys if k not in self._registered_keys]
        if new_keys:
            await self.client.register_states(new_keys)
            self._registered_keys.update(new_keys)

    # ── Service request helpers ────────────────────────────────────────────────

    async def send_service_request(self, req: ServiceRequest) -> None:
        """Send a service request via the client."""
        logger.warning(
            "Service request: type=%s request=%s zone=%s component=%s "
            "logical=%s args=%s",
            req.service_type, req.request, req.zone,
            req.component, req.logical_component, req.request_args,
        )
        await self.client.send_service_request(req)

    async def set_state(self, key: str, value: object) -> None:
        """Directly set a state value (state/set).

        On some hosts the HVAC KNX bus is written via state/set
        rather than service/request.
        """
        await self.client.set_state(key, value)

    async def send_dis_request(self, req: DISRequest) -> None:
        """Send a DIS request via the client."""
        await self.client.send_dis_request(req)

    # ── Shutdown ───────────────────────────────────────────────────────────────

    async def async_shutdown(self) -> None:
        """Disconnect the client."""
        await self.client.disconnect()
