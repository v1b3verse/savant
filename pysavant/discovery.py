"""mDNS discovery for Savant hosts."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

from pysavant.exceptions import TimeoutError

logger = logging.getLogger(__name__)

MDNS_SERVICE_TYPE = "_savant-control._tcp.local."


@dataclass
class SavantHost:
    hostname: str = ""
    port: int = 0
    host_uid: str = ""
    home_id: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


async def discover(timeout: float = 5.0) -> list[SavantHost]:
    """Browse mDNS for Savant hosts. Returns all found within timeout."""
    hosts: list[SavantHost] = []
    found_event = asyncio.Event()

    def on_service_state_change(
        zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
    ) -> None:
        if state_change != ServiceStateChange.Added:
            return
        info = zeroconf.get_service_info(service_type, name)
        if info is None:
            return

        props = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in info.properties.items()
        }

        addresses = info.parsed_scoped_addresses()
        if not addresses:
            return

        host = SavantHost(
            hostname=addresses[0],
            port=info.port or 5000,
            host_uid=str(props.get("hostUID", "")),
            home_id=str(props.get("homeId", "")),
            properties=props,
        )
        hosts.append(host)
        logger.info("Discovered Savant host: %s:%d", host.hostname, host.port)
        found_event.set()

    azc = AsyncZeroconf()
    browser = ServiceBrowser(azc.zeroconf, MDNS_SERVICE_TYPE, handlers=[on_service_state_change])

    try:
        await asyncio.sleep(timeout)
    finally:
        browser.cancel()
        await azc.async_close()

    return hosts


async def discover_one(timeout: float = 5.0) -> SavantHost:
    """Return the first discovered host, or raise TimeoutError."""
    hosts = await discover(timeout=timeout)
    if not hosts:
        raise TimeoutError(f"No Savant hosts found within {timeout}s")
    return hosts[0]
