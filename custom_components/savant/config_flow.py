"""Config flow for Savant integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from pysavant.client import SavantClient
from pysavant.exceptions import AuthenticationError, SavantError

from .const import (
    CONF_HOME_ID,
    CONF_HOST_TOKEN,
    CONF_HOST_UID,
    CONF_SECRET_KEY,
    DEFAULT_PORT,
    DOMAIN,
)

logger = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional("user", default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
    }
)

STEP_ZEROCONF_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("user", default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
    }
)


class SavantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Savant."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle manual configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await self._test_connection(
                    host=user_input[CONF_HOST],
                    port=user_input.get(CONF_PORT, DEFAULT_PORT),
                    user=user_input.get("user", ""),
                    password=user_input.get(CONF_PASSWORD, ""),
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except SavantError:
                errors["base"] = "cannot_connect"
            except Exception:
                logger.exception("Unexpected error during connection test")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info.get(CONF_HOST_UID, user_input[CONF_HOST]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.get("host_name", user_input[CONF_HOST]),
                    data={**user_input, **info},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        host = str(discovery_info.host)
        port = discovery_info.port or DEFAULT_PORT
        properties = discovery_info.properties

        host_uid = properties.get("hostUID", "")
        home_id = properties.get("homeId", "")

        await self.async_set_unique_id(host_uid or host)
        self._abort_if_unique_id_configured()

        self._discovery_info = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_HOST_UID: host_uid,
            CONF_HOME_ID: home_id,
        }

        self.context["title_placeholders"] = {
            "host_name": properties.get("hostName", "Savant"),
            "host": host,
        }

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm zeroconf discovery with optional credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await self._test_connection(
                    host=self._discovery_info[CONF_HOST],
                    port=self._discovery_info[CONF_PORT],
                    user=user_input.get("user", ""),
                    password=user_input.get(CONF_PASSWORD, ""),
                    host_uid=self._discovery_info.get(CONF_HOST_UID, ""),
                    home_id=self._discovery_info.get(CONF_HOME_ID, ""),
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except SavantError:
                errors["base"] = "cannot_connect"
            except Exception:
                logger.exception("Unexpected error during connection test")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info.get("host_name", self._discovery_info[CONF_HOST]),
                    data={**self._discovery_info, **user_input, **info},
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=STEP_ZEROCONF_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connection(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        user: str = "",
        password: str = "",
        host_uid: str = "",
        home_id: str = "",
    ) -> dict[str, Any]:
        """Test connection and return session info."""
        client = SavantClient(
            host=host,
            port=port,
            user=user,
            password=password,
            host_uid=host_uid,
            home_id=home_id,
            connect_timeout=10.0,
        )
        try:
            await client.connect()
            return {
                "host_name": client.session.host_name,
                CONF_HOST_TOKEN: client.session.host_token,
                CONF_SECRET_KEY: client.session.secret_key,
                CONF_HOST_UID: client.session.host_uid,
            }
        finally:
            await client.disconnect()
