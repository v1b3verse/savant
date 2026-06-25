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

STEP_MANUAL_SCHEMA = vol.Schema(
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
        """First step — run network discovery and show results (or manual form)."""
        # Run discovery once; cache so we don't scan every POST
        if not self._discovery_info and user_input is None:
            hosts = await self._run_discovery()
            if hosts:
                return self._show_discovery_results(hosts)

        # If user picked a host from discovery
        if user_input and "selected_host" in user_input:
            host = self._parse_selected_host(user_input["selected_host"])
            if host:
                self._set_discovery_info(host)
                return await self.async_step_credentials()

        # Otherwise show manual form
        return await self.async_step_manual(user_input)

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manual host entry."""
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
            step_id="manual",
            data_schema=STEP_MANUAL_SCHEMA,
            errors=errors,
            description_placeholders={"host": ""},
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter credentials for a discovered host."""
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
            step_id="credentials",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "host": self._discovery_info.get(CONF_HOST, "?"),
            },
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _run_discovery(self) -> list[SavantHost]:
        """Run UDP network discovery and return found hosts."""
        try:
            hosts = await discover_hosts(timeout=5.0)
            if hosts:
                logger.info("Discovered %d Savant host(s) on network", len(hosts))
            return hosts
        except TimeoutError:
            logger.info("No Savant hosts discovered (timeout)")
            return []
        except Exception:
            logger.exception("Discovery error")
            return []

    def _show_discovery_results(self, hosts: list[SavantHost]) -> ConfigFlowResult:
        """Show discovered hosts with a link to manual entry."""
        host_options: dict[str, str] = {}
        for h in hosts:
            label = f"{h.hostname}:{h.port}"
            if h.properties.get("hostName"):
                label = f"{h.properties['hostName']} ({label})"
            host_options[f"{h.hostname}:{h.port}"] = label

        host_options["manual"] = "Zadat ručně / Manual entry"

        schema = vol.Schema(
            {vol.Required("selected_host"): vol.In(host_options)}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors={},
            description_placeholders={
                "count": str(len(hosts)),
            },
        )

    def _parse_selected_host(self, selected: str) -> SavantHost | None:
        """Parse a 'host:port' selection string into a SavantHost."""
        if ":" not in selected:
            return None
        host_part, port_part = selected.rsplit(":", 1)
        try:
            return SavantHost(hostname=host_part, port=int(port_part))
        except (ValueError, TypeError):
            return None

    def _set_discovery_info(self, host: SavantHost) -> None:
        """Store discovered host info for the credentials step."""
        self._discovery_info = {
            CONF_HOST: host.hostname,
            CONF_PORT: host.port,
            CONF_HOST_UID: host.host_uid,
            CONF_HOME_ID: host.home_id,
        }
        self.context["title_placeholders"] = {
            "host_name": host.properties.get("hostName", "Savant"),
        }

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
