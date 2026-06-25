"""UDP probe discovery for Savant hosts.

Uses the same protocol as the official Savant Android app:
sends a MessagePack probe to UDP port 9101 and parses host
responses.

The host may respond to broadcast or only to direct unicast.
This module tries broadcast first, then sweeps the local
subnet with unicast probes (matching the APK's
``mUnreliableMulticast`` fallback).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import msgpack

from pysavant.exceptions import TimeoutError

logger = logging.getLogger(__name__)

PROBE_PORT = 9101
PROBE_SERVICE = "_control_.ws"
MIN_RESPONSE_SIZE = 10


@dataclass
class SavantHost:
    """A Savant host discovered via UDP probe."""

    hostname: str = ""
    port: int = 0
    host_uid: str = ""
    home_id: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def scheme(self) -> str:
        return str(self.properties.get("scheme", "wss"))


async def discover(timeout: float = 5.0) -> list[SavantHost]:
    """Discover Savant hosts on the local network.

    Two-phase strategy:
      1. Broadcast probe (catches hosts that respond to broadcast).
      2. If no response after half the timeout, sweep local subnets
         with unicast probes (catches hosts that only respond to
         directed unicast).
    """
    loop = asyncio.get_running_loop()
    transport: asyncio.DatagramTransport | None = None
    protocol: _ProbeProtocol | None = None

    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _ProbeProtocol(),
            local_addr=("0.0.0.0", 0),
            allow_broadcast=True,
        )

        payload = msgpack.packb({"service": PROBE_SERVICE, "version": 1})

        # Phase 1 — broadcast on all local subnets
        subnets = _get_local_subnets()
        for network, prefix in subnets:
            bcast = _broadcast_for(network, prefix)
            if bcast:
                transport.sendto(payload, (bcast, PROBE_PORT))
                logger.debug("Sent UDP probe to broadcast %s:%d", bcast, PROBE_PORT)

        # Phase 2 — subnet sweep if no broadcast response
        await asyncio.sleep(timeout / 2)
        if protocol and protocol.has_responses():
            # Got something from broadcast — just wait for the rest
            await asyncio.sleep(timeout / 2)
        else:
            # Sweep subnets with unicast probes
            logger.debug("No broadcast response; sweeping subnets with unicast")
            for network, prefix in subnets:
                _sweep_subnet(transport, payload, network, prefix, PROBE_PORT)
            await asyncio.sleep(timeout / 2)

    finally:
        if transport is not None and not transport.is_closing():
            transport.close()

    if protocol is None:
        return []

    hosts = protocol.collect()
    if hosts:
        logger.info("Discovered %d Savant host(s)", len(hosts))
    return hosts


async def discover_one(timeout: float = 5.0) -> SavantHost:
    """Return the first discovered host, or raise TimeoutError."""
    hosts = await discover(timeout=timeout)
    if not hosts:
        raise TimeoutError(f"No Savant hosts found within {timeout}s")
    return hosts


# ── Network helpers ──────────────────────────────────────────────────────────


def _get_local_subnets() -> list[tuple[str, int]]:
    """Return (network, prefix) for non-virtual LAN interfaces."""
    subnets: list[tuple[str, int]] = []
    try:
        import subprocess  # noqa: S404

        result = subprocess.run(
            ["ip", "-4", "addr", "show"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line.startswith("inet "):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            cidr = parts[1]
            ip, prefix_str = cidr.split("/")
            prefix = int(prefix_str)
            # Skip loopback, Docker bridges, and other virtual interfaces
            if ip.startswith("127."):
                continue
            if prefix > 24:
                continue
            network = ip.rsplit(".", 1)[0] + ".0"
            subnets.append((network, prefix))
    except Exception:
        subnets = [("10.0.0.0", 8), ("192.168.1.0", 24)]
    return subnets or [("10.0.0.0", 8)]


def _broadcast_for(network: str, prefix: int) -> str | None:
    """Compute the broadcast address for a network/prefix."""
    try:
        if prefix >= 24:
            parts = network.split(".")
            parts[3] = "255"
            return ".".join(parts)
        return None
    except Exception:
        return None


def _sweep_subnet(
    transport: asyncio.DatagramTransport,
    payload: bytes,
    network: str,
    prefix: int,
    port: int,
) -> None:
    """Send a unicast probe to every address in the subnet.

    Matches the APK's ``mUnreliableMulticast`` fallback which iterates
    .1 through .254 when UDP broadcast is unreliable.
    """
    if prefix >= 24:
        base = ".".join(network.split(".")[:3])
        for last in range(1, 255):
            transport.sendto(payload, (f"{base}.{last}", port))
    else:
        base = ".".join(network.split(".")[:2])
        for third in range(0, 256):
            for last in (1, 254):
                transport.sendto(payload, (f"{base}.{third}.{last}", port))


# ── Asyncio protocol ────────────────────────────────────────────────────────


class _ProbeProtocol(asyncio.DatagramProtocol):
    """Handles UDP probe responses from Savant hosts."""

    def __init__(self) -> None:
        self._responses: list[tuple[bytes, tuple[str, int]]] = []
        self._transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self._transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) < MIN_RESPONSE_SIZE:
            return
        self._responses.append((data, addr))

    def error_received(self, exc: Exception) -> None:
        logger.warning("UDP probe error: %s", exc)

    def has_responses(self) -> bool:
        return len(self._responses) > 0

    def collect(self) -> list[SavantHost]:
        """Parse all collected responses into SavantHost objects."""
        hosts: list[SavantHost] = []

        for data, (source_ip, _) in self._responses:
            try:
                obj = msgpack.unpackb(data, raw=False)
            except Exception:
                continue

            if not isinstance(obj, dict):
                continue

            host_uid = str(obj.get("UID", ""))
            home_id = str(obj.get("homeID", "") or obj.get("homeId", ""))
            port = int(obj.get("port", 0))

            host = SavantHost(
                hostname=source_ip,
                port=port,
                host_uid=host_uid,
                home_id=home_id,
                properties={
                    k: str(v) if not isinstance(v, (int, float, bool)) else v
                    for k, v in obj.items()
                },
            )
            hosts.append(host)

        return hosts
