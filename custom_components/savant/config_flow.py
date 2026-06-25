"""Config flow for Savant integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from pysavant.client import SavantClient
from pysavant.discovery import discover as discover_hosts, SavantHost
from pysavant.exceptions import AuthenticationError, SavantError, TimeoutError

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

STEP_CREDENTIALS_SCHEMA = vol.Schema(
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
        """Handle manual configuration (default)."""
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

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Discover Savant hosts on the local network via UDP probe."""
        errors: dict[str, str] = {}

        if user_input is not None and not self._discovery_info:
            # User selected a host from the list
            try:
                hosts = await discover_hosts(timeout=5.0)
            except TimeoutError:
                errors["base"] = "no_hosts_found"
            except Exception:
                logger.exception("Discovery error")
                errors["base"] = "discovery_failed"
            else:
                host_info = self._find_host(hosts, user_input)
                if host_info is not None:
                    self._set_discovery_info(host_info)
                    return await self.async_step_discovery_confirm()
                errors["base"] = "host_disappeared"

        if not self._discovery_info:
            # Run discovery
            try:
                hosts = await discover_hosts(timeout=5.0)
            except TimeoutError:
                errors["base"] = "no_hosts_found"
                hosts = []
            except Exception:
                logger.exception("Discovery error")
                errors["base"] = "discovery_failed"
                hosts = []

            if hosts:
                return self._show_discovery_results(hosts)

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"error": errors.get("base", "")},
        )

    def _show_discovery_results(self, hosts: list[SavantHost]) -> ConfigFlowResult:
        """Show a list of discovered hosts."""
        host_options: dict[str, str] = {}
        for h in hosts:
            label = f"{h.hostname}:{h.port}"
            if h.properties.get("hostName"):
                label = f"{h.properties['hostName']} ({label})"
            host_options[f"{h.hostname}:{h.port}"] = label

        schema = vol.Schema(
            {vol.Required("selected_host"): vol.In(host_options)}
        )

        return self.async_show_form(
            step_id="discovery",
            data_schema=schema,
            errors={},
            description_placeholders={"count": str(len(hosts))},
        )

    def _find_host(self, hosts: list[SavantHost], user_input: dict) -> SavantHost | None:
        """Find a host matching the user's selection."""
        selected = user_input.get("selected_host", "")
        host_part = selected.split(":")[0]
        port_part = selected.split(":")[1] if ":" in selected else ""
        for h in hosts:
            if h.hostname == host_part and (
                not port_part or str(h.port) == port_part
            ):
                return h
        return None

    def _set_discovery_info(self, host: SavantHost) -> None:
        """Store discovered host info for the confirm step."""
        self._discovery_info = {
            CONF_HOST: host.hostname,
            CONF_PORT: host.port,
            CONF_HOST_UID: host.host_uid,
            CONF_HOME_ID: host.home_id,
        }
        self.context["title_placeholders"] = {
            "host_name": host.properties.get("hostName", "Savant"),
        }

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery with optional credentials."""
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
            step_id="discovery_confirm",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "host": self._discovery_info.get(CONF_HOST, "?"),
            },
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
        """Test connection and return session info.

        Also downloads the house configuration to verify full access.
        """
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
            await client.get_config()
            return {
                "host_name": client.session.host_name,
                CONF_HOST_TOKEN: client.session.host_token,
                CONF_SECRET_KEY: client.session.secret_key,
                CONF_HOST_UID: client.session.host_uid,
            }
        finally:
            await client.disconnect()
