"""The Savant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from pysavant.client import SavantClient

from .const import (
    CONF_HOME_ID,
    CONF_HOST_TOKEN,
    CONF_HOST_UID,
    CONF_SECRET_KEY,
    DEFAULT_PORT,
    DOMAIN,
)
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.FAN,
    Platform.LOCK,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Savant from a config entry."""
    client = SavantClient(
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        user=entry.data.get("user", ""),
        password=entry.data.get(CONF_PASSWORD, ""),
        host_token=entry.data.get(CONF_HOST_TOKEN, ""),
        secret_key=entry.data.get(CONF_SECRET_KEY, ""),
        host_uid=entry.data.get(CONF_HOST_UID, ""),
        home_id=entry.data.get(CONF_HOME_ID, ""),
    )

    await client.connect()

    coordinator = SavantCoordinator(hass, client)
    await coordinator.async_setup()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Savant config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: SavantCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok
