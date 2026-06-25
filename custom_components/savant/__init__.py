"""The Savant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from pysavant.client import SavantClient
from pysavant.exceptions import AuthenticationError, SavantError

from .const import (
    CONF_HOME_ID,
    CONF_HOST_TOKEN,
    CONF_HOST_UID,
    CONF_SECRET_KEY,
    DEFAULT_PORT,
)
from .coordinator import SavantCoordinator

logger = logging.getLogger(__name__)

type SavantConfigEntry = ConfigEntry[SavantCoordinator]

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


async def async_setup_entry(hass: HomeAssistant, entry: SavantConfigEntry) -> bool:
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

    try:
        await client.connect()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except SavantError as err:
        raise ConfigEntryNotReady(f"Cannot connect to Savant host: {err}") from err

    coordinator = SavantCoordinator(hass, client, entry)
    await coordinator.async_setup()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SavantConfigEntry) -> bool:
    """Unload a Savant config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()

    return unload_ok
