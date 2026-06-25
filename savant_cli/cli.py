"""CLI tool for Savant home automation."""

from __future__ import annotations

import asyncio
import json
import sys

import click

from pysavant.client import SavantClient
from pysavant.config import HouseConfig, InfrastructureDevice
from pysavant.discovery import discover as _discover_hosts
from pysavant.protocol import DEFAULT_PORT
from pysavant.services import lighting
from pysavant.services.switch import dimmer_set, switch_off, switch_on


@click.group()
@click.option("--host", envvar="SAVANT_HOST", help="Savant host IP address")
@click.option("--port", default=DEFAULT_PORT, envvar="SAVANT_PORT", help="WebSocket port")
@click.option("--user", envvar="SAVANT_USER", default="", help="Username")
@click.option("--password", envvar="SAVANT_PASSWORD", default="", help="Password")
@click.option("--token", envvar="SAVANT_TOKEN", default="", help="Host token for re-auth")
@click.option("--secret", envvar="SAVANT_SECRET", default="", help="Secret key")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(
    ctx: click.Context,
    host: str | None,
    port: int,
    user: str,
    password: str,
    token: str,
    secret: str,
    as_json: bool,
) -> None:
    """Savant home automation CLI."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port
    ctx.obj["user"] = user
    ctx.obj["password"] = password
    ctx.obj["token"] = token
    ctx.obj["secret"] = secret
    ctx.obj["json"] = as_json


def _make_client(ctx: click.Context) -> SavantClient:
    host = ctx.obj["host"]
    if not host:
        click.echo("Error: --host is required (set SAVANT_HOST env or use --host)", err=True)
        sys.exit(1)
    return SavantClient(
        host=host,
        port=ctx.obj["port"],
        user=ctx.obj["user"],
        password=ctx.obj["password"],
        host_token=ctx.obj["token"],
        secret_key=ctx.obj["secret"],
    )


# ── Connection ────────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def connect(ctx: click.Context) -> None:
    """Test connection to the Savant host."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            click.echo(f"Connected to {client.host}:{client.port}")
            click.echo(f"  Host:      {client.session.host_name}")
            click.echo(f"  Host UID:  {client.session.host_uid}")
            click.echo(f"  Host home: {client.session.home_id}")

    asyncio.run(_run())


# ── Discovery ─────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--timeout", default=5.0, help="Discovery timeout in seconds")
def discover(timeout: float) -> None:
    """Scan for Savant hosts on the network."""

    async def _run() -> None:
        hosts = await _discover_hosts(timeout=timeout)
        if not hosts:
            click.echo("No Savant hosts found.")
            return
        for h in hosts:
            click.echo(f"{h.hostname}:{h.port}  uid={h.host_uid}  home={h.home_id}")

    asyncio.run(_run())


# ── Lighting control ──────────────────────────────────────────────────────────


def _find_entity_zone(cfg: HouseConfig, address: str) -> str | None:
    """Look up an entity's zone name by KNX group address."""
    for d in cfg.infrastructure:
        if d.address == address:
            return d.zone
    for room in cfg.rooms:
        for _e in room.lights:
            a = (_e.addresses or "").split(",")[0]
            if a == address:
                return room.name
        for _e in room.shades:  # type: ignore[assignment]
            a = (_e.addresses or "").split(",")[0]
            if a == address:
                return room.name
        for _e in room.hvac:  # type: ignore[assignment]
            a = (_e.addresses or "").split(",")[0]
            if a == address:
                return room.name
        for _e in room.fans:  # type: ignore[assignment]
            a = (_e.addresses or "").split(",")[0]
            if a == address:
                return room.name
        for sec in room.security:
            if str(sec.zone_number) == address:
                return room.name
    return None


@cli.command()
@click.argument("zone", required=False, default=None)
@click.argument("level", type=int, default=None)
@click.option("--addr", "addr", default=None, help="Target individual entity by KNX group address")
@click.pass_context
def light(ctx: click.Context, zone: str | None, level: int | None, addr: str | None) -> None:
    """Set brightness to LEVEL (0-100).

    Without ``--addr``:

        savant-cli light "007 Living" 50    -> zone-level, all lights in room

    With ``--addr``:

        savant-cli light --addr 141 50       -> individual entity by KNX address
    """

    async def _run() -> None:
        async with _make_client(ctx) as client:
            # Resolve effective zone and level (--addr may shift positional args)
            eff_zone = zone
            eff_level = level
            if addr is not None and eff_level is None and eff_zone is not None:
                try:
                    eff_level = int(eff_zone)
                    eff_zone = None
                except (ValueError, TypeError):
                    pass

            if addr is not None:
                if eff_level is None:
                    click.echo("Missing LEVEL argument", err=True)
                    return
                cfg = await client.get_config()
                zone_name = _find_entity_zone(cfg, addr)
                if zone_name is None:
                    click.echo(f"No entity with address {addr} found", err=True)
                    return
                req = dimmer_set(zone=zone_name, address=addr, level=eff_level)
                await client.send_service_request(req)
                click.echo(f"Set addr={addr} (zone={zone_name}) brightness to {eff_level}")
            else:
                if eff_zone is None or eff_level is None:
                    click.echo("Missing ZONE or LEVEL argument", err=True)
                    return
                req = lighting.set_brightness(eff_zone, eff_level)
                await client.send_service_request(req)
                click.echo(f"Set {eff_zone} brightness to {eff_level}")

    asyncio.run(_run())


@cli.command()
@click.argument("zone")
@click.pass_context
def on(ctx: click.Context, zone: str) -> None:
    """Turn on lights in ZONE."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            req = lighting.turn_on(zone)
            await client.send_service_request(req)
            click.echo(f"Turned on {zone}")

    asyncio.run(_run())


@cli.command()
@click.argument("zone")
@click.pass_context
def off(ctx: click.Context, zone: str) -> None:
    """Turn off lights in ZONE."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            req = lighting.turn_off(zone)
            await client.send_service_request(req)
            click.echo(f"Turned off {zone}")

    asyncio.run(_run())


# ── State ─────────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("key")
@click.pass_context
def state(ctx: click.Context, key: str) -> None:
    """Subscribe to state KEY and print its value."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            received = asyncio.Event()

            def on_update(k: str, v: object) -> None:
                click.echo(f"{k} = {v}")
                received.set()

            client.state_manager.subscribe(key, on_update)
            await client.register_states([key])
            try:
                await asyncio.wait_for(received.wait(), timeout=10.0)
            except TimeoutError:
                click.echo(f"No update received for {key} within 10s", err=True)

    asyncio.run(_run())


def _collect_all_state_keys(cfg: HouseConfig) -> list[str]:
    """Collect every state key the Android app subscribes to.

    Reads ``stateName`` from the SQLite database for simple entities
    (lights, fans), then generates the additional programmatic states
    for HVAC (setpoints, modes), security (partition status, arming),
    and other entity types, following the patterns in the decompiled
    ``SavantEntities.getStates()`` methods.
    """
    keys: set[str] = set()

    def _first_addr(raw: str) -> str:
        """Extract first non-null address from the addresses CSV field."""
        parts = (raw or "").split(",")
        for p in parts:
            p = p.strip()
            if p and p != "(null)":
                return p
        return ""

    # ── global ──
    keys.add("global.ActiveZones")
    keys.add("global.ActiveScene")

    # ── Lights ──
    for room in cfg.rooms:
        for le in room.lights:
            if le.state_name:
                keys.add(le.state_name)
    for d in cfg.infrastructure:
        if d.state_name:
            keys.add(d.state_name)

    # ── HVAC — full set as in HVACEntity.getStates() ──
    hvac_properties = [
        "ThermostatCurrentCoolPoint",
        "ThermostatCurrentHeatPoint",
        "ThermostatCurrentSetPoint",
        "ThermostatCurrentRemoteTemperature",
        "ThermostatCurrentHumiditySetPoint",
        "ThermostatCurrentHumidifyPoint",
        "ThermostatCurrentDehumidifyPoint",
        "ThermostatHumidityMode",
        "IsThermostatHumidityModeOn",
        "IsThermostatHumidityModeOff",
        "ThermostatCurrentHumidity",
        "IsThermostatCurrentFanModeAuto",
        "IsThermostatCurrentFanModeOn",
        "ThermostatFanMode",
        "ThermostatFanStatus",
        "IsThermostatFanStopped",
        "IsThermostatFanRunning",
        "ThermostatHVACState",
        "IsCurrentHVACModeAuto",
        "IsCurrentHVACModeCool",
        "IsCurrentHVACModeHeat",
        "IsCurrentHVACModeEmergencyHeat",
        "IsCurrentHVACModeOff",
        "RelativeHumidityMode",
        "ThermostatMode",
        "ThermostatTempUnit",
        "IsGRelayEnergized",
        "IsY1RelayEnergized",
        "IsW1RelayEnergized",
        "IsY2RelayEnergized",
    ]
    for room in cfg.rooms:
        for he in room.hvac:
            if he.state_name:
                keys.add(he.state_name)
            addr = _first_addr(he.addresses)
            if not addr:
                continue
            scope = "KNX.HVAC_controller."
            for prop in hvac_properties:
                keys.add(f"{scope}{prop}_{addr}")

    # ── Fans ──
    for room in cfg.rooms:
        for fe in room.fans:
            if fe.state_name:
                keys.add(fe.state_name)

    # ── Security — as in SecurityEntity.getStates() ──
    partition_properties = [
        "CurrentPartitionStatus",
        "PartitionArmingStatus",
        "IsPartitionReady",
        "IsPartitionAlarmActive",
        "ExitDelaySeconds",
        "ExitDelayArmingType",
        "PartitionSmartPinArmingStatus",
        "ZonesToBypassTotal",
        "ZonesToBypassRemaining",
        "ZonesBypassedInPartition",
        "ZonesFaultedInPartition",
        "ZonesUnknownFailureInPartition",
    ]
    zone_properties = [
        "ZoneSummary",
        "IsZoneBypassed",
    ]
    for room in cfg.rooms:
        for se in room.security:
            if se.state_name:
                keys.add(se.state_name)
            scope = "Security System.Security_system."
            if se.zone_number == 0:
                for prop in partition_properties:
                    keys.add(f"{scope}{prop}_{se.partition_number}")
            else:
                for prop in zone_properties:
                    keys.add(f"{scope}{prop}_{se.zone_number}")

    return sorted(keys)


@cli.command()
@click.pass_context
def listen(ctx: click.Context) -> None:
    """Subscribe to all state updates and print them in real time.

    Connects, downloads the house config to discover all state keys, then
    subscribes to every entity's state (lights, HVAC, fans, security,
    infrastructure) and prints each update as it arrives.

    Press Ctrl+C to stop.
    """

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

            keys = _collect_all_state_keys(cfg)

            click.echo(f"Subscribing to {len(keys)} state keys...")
            if ctx.obj.get("as_json"):
                click.echo(json.dumps({"event": "subscribed", "keys": len(keys)}))

            # Print every state update as it arrives
            client.state_manager.subscribe("*", lambda k, v: click.echo(f"{k} = {v}"))

            await client.register_states(keys)

            click.echo("── Current state dump ────────────────────────────")
            # Wait briefly so the initial burst prints before the separator
            await asyncio.sleep(3.0)
            click.echo("── Now listening for changes (Ctrl+C to stop) ────")

            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.pass_context
def zones(ctx: click.Context) -> None:
    """List active zones."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            received = asyncio.Event()

            def on_update(k: str, v: object) -> None:
                received.set()

            client.state_manager.subscribe("global.ActiveZones", on_update)
            await client.register_states(["global.ActiveZones"])
            try:
                await asyncio.wait_for(received.wait(), timeout=10.0)
            except TimeoutError:
                click.echo("No zone data received within 10s", err=True)
                return

            zones_val = client.state_manager.active_zones
            if not zones_val:
                click.echo("No active zones")
                return
            for z in zones_val:
                click.echo(z)

    asyncio.run(_run())


# ── Config / Discovery ────────────────────────────────────────────────────────


def _print_as_json(obj: object, ctx: click.Context) -> None:
    """Print object as JSON if --json flag is set, otherwise do nothing."""
    if ctx.obj.get("json"):
        click.echo(json.dumps(obj, indent=2, default=str))


def _make_entity_dict(entity: object) -> dict[str, object]:
    """Convert a dataclass entity to a plain dict for JSON output."""
    from dataclasses import fields
    return {f.name: getattr(entity, f.name) for f in fields(entity)}  # type: ignore[arg-type]


@cli.command()
@click.option("--raw", is_flag=True, help="Show raw SQLite table contents")
@click.pass_context
def config(ctx: click.Context, raw: bool) -> None:
    """Download and show house configuration (rooms, services, entities)."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            with click.progressbar(length=1, label="Downloading config") as bar:
                cfg = await client.get_config()
                bar.update(1)

        if ctx.obj.get("json"):
            dump = {
                "rooms": [
                    {
                        "name": r.name,
                        "room_id": r.room_id,
                        "group": r.group,
                        "capabilities": {
                            "lights": r.has_lights,
                            "shades": r.has_shades,
                            "hvac": r.has_hvac,
                            "fans": r.has_fans,
                            "security": r.has_security,
                            "cameras": r.has_cameras,
                            "av": r.has_av,
                        },
                        "lights": [_make_entity_dict(e) for e in r.lights],
                        "shades": [_make_entity_dict(e) for e in r.shades],
                        "hvac": [_make_entity_dict(e) for e in r.hvac],
                        "fans": [_make_entity_dict(e) for e in r.fans],
                        "security": [_make_entity_dict(e) for e in r.security],
                    }
                    for r in cfg.rooms
                ],
                "zone_services": [
                    {
                        "zone": z.zone_name,
                        "component": z.component,
                        "logical_component": z.logical_component,
                        "service_type": z.service_type,
                    }
                    for z in cfg.zones
                ],
            }
            click.echo(json.dumps(dump, indent=2, default=str))
            return

        click.echo(f"\nHouse configuration: {len(cfg.rooms)} rooms, {len(cfg.zones)} zone services")

        if raw:
            for tbl_name, rows in cfg.raw_tables.items():
                click.echo(f"\n── {tbl_name} ({len(rows)} rows) ──")
                if not rows:
                    continue
                cols = list(rows[0].keys())
                click.echo("  " + " | ".join(cols))
                for row in rows[:5]:
                    click.echo("  " + " | ".join(str(row.get(c, ""))[:50] for c in cols))
                if len(rows) > 5:
                    click.echo(f"  ... ({len(rows) - 5} more)")

    asyncio.run(_run())


@cli.command()
@click.option("--group", "group_filter", help="Filter by room group")
@click.pass_context
def rooms(ctx: click.Context, group_filter: str | None) -> None:
    """List rooms with capabilities and entity counts."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

        if ctx.obj.get("json"):
            data = [
                {
                    "name": r.name,
                    "group": r.group,
                    "capabilities": {
                        "lights": r.has_lights,
                        "shades": r.has_shades,
                        "hvac": r.has_hvac,
                        "fans": r.has_fans,
                        "security": r.has_security,
                    },
                    "entity_counts": {
                        "lights": len(r.lights),
                        "shades": len(r.shades),
                        "hvac": len(r.hvac),
                        "fans": len(r.fans),
                        "security": len(r.security),
                    },
                }
                for r in cfg.rooms
                if not group_filter or r.group == group_filter
            ]
            click.echo(json.dumps(data, indent=2))
            return

        prev_group = None
        room_count = 0
        for room in cfg.rooms:
            if group_filter and room.group != group_filter:
                continue
            room_count += 1
            if room.group and room.group != prev_group:
                click.echo(f"\n── {room.group} ──")
                prev_group = room.group

            parts = []
            if room.has_lights:
                parts.append(f"{len(room.lights)} lights")
            if room.has_shades:
                parts.append(f"{len(room.shades)} shades")
            if room.has_hvac:
                parts.append(f"{len(room.hvac)} HVAC")
            if room.has_fans:
                parts.append(f"{len(room.fans)} fans")
            if room.has_security:
                parts.append(f"{len(room.security)} security")
            click.echo(f"  {room.name:30s} [{', '.join(parts)}]")

        click.echo(f"\n{room_count} rooms")

    asyncio.run(_run())


@cli.command()
@click.argument("room_name")
@click.pass_context
def room(ctx: click.Context, room_name: str) -> None:
    """Show detailed info for a specific room."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

        r = cfg.get_room(name=room_name)
        if r is None:
            # Try case-insensitive match
            r = next((r for r in cfg.rooms if r.name.lower() == room_name.lower()), None)
        if r is None:
            click.echo(f"Room '{room_name}' not found", err=True)
            return

        if ctx.obj.get("json"):
            data = {
                "name": r.name,
                "room_id": r.room_id,
                "group": r.group,
                "capabilities": {
                    "lights": r.has_lights,
                    "shades": r.has_shades,
                    "hvac": r.has_hvac,
                    "fans": r.has_fans,
                    "security": r.has_security,
                    "cameras": r.has_cameras,
                    "av": r.has_av,
                },
                "lights": [_make_entity_dict(e) for e in r.lights],
                "shades": [_make_entity_dict(e) for e in r.shades],
                "hvac": [_make_entity_dict(e) for e in r.hvac],
                "fans": [_make_entity_dict(e) for e in r.fans],
                "security": [_make_entity_dict(e) for e in r.security],
            }
            click.echo(json.dumps(data, indent=2, default=str))
            return

        group_info = f" ({r.group})" if r.group else ""
        click.echo(f"\n{r.name}{group_info}")
        click.echo(f"  Room ID: {r.room_id}")
        caps = []
        for attr, label in [
            ("has_lights", "Lights"),
            ("has_shades", "Shades"),
            ("has_hvac", "HVAC"),
            ("has_fans", "Fans"),
            ("has_security", "Security"),
            ("has_cameras", "Cameras"),
            ("has_av", "A/V"),
        ]:
            if getattr(r, attr, False):
                caps.append(label)
        if caps:
            click.echo(f"  Capabilities: {', '.join(caps)}")

        if r.lights:
            click.echo(f"\n  Lights ({len(r.lights)}):")
            for ent in r.lights:
                dim = " dimmer" if ent.is_dimmer else ""
                click.echo(f"    {ent.name:40s}  state={ent.state_name}{dim}")
        if r.shades:
            click.echo(f"\n  Shades ({len(r.shades)}):")
            for s in r.shades:
                click.echo(f"    {s.name:40s}  state={s.state_name}")
        if r.hvac:
            click.echo(f"\n  HVAC ({len(r.hvac)}):")
            for h in r.hvac:
                modes = []
                if h.has_heat:
                    modes.append("heat")
                if h.has_cool:
                    modes.append("cool")
                click.echo(f"    {h.name:40s}  modes={','.join(modes)}  state={h.state_name}")
        if r.fans:
            click.echo(f"\n  Fans ({len(r.fans)}):")
            for fan_ent in r.fans:
                click.echo(f"    {fan_ent.name:40s}  state={fan_ent.state_name}")

    asyncio.run(_run())


@cli.command()
@click.argument("entity_type", type=click.Choice(["lights", "shades", "hvac", "fans", "security"]))
@click.option("--room", "room_filter", help="Filter by room name")
@click.pass_context
def entities(ctx: click.Context, entity_type: str, room_filter: str | None) -> None:
    """List entities of a given type (lights|shades|hvac|fans|security)."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

        type_map = {
            "lights": ("lights", ["name", "state_name", "is_dimmer", "addresses"]),
            "shades": ("shades", ["name", "state_name", "addresses"]),
            "hvac": ("hvac", ["name", "state_name", "has_heat", "has_cool", "addresses"]),
            "fans": ("fans", ["name", "state_name", "addresses"]),
            "security": ("security", ["name", "partition_number", "zone_number"]),
        }
        attr_name, cols = type_map[entity_type]

        rows = []
        for room in cfg.rooms:
            if room_filter and room.name.lower() != room_filter.lower():
                continue
            for entity in getattr(room, attr_name):
                rows.append((room.name, entity))

        total = len(rows)
        if ctx.obj.get("json"):
            data = [
                {"room": room_name, **{c: getattr(e, c, "") for c in cols}}
                for room_name, e in rows
            ]
            click.echo(json.dumps(data, indent=2))
            return

        click.echo(f"\n{entity_type.capitalize()}: {total} entities")
        for room_name, e in rows:
            vals = ", ".join(f"{c}={getattr(e, c, '')}" for c in cols)
            click.echo(f"  {room_name:30s} {vals}")

    asyncio.run(_run())


@cli.command()
@click.argument("device_type", type=click.Choice([
    "pump", "valve", "heating", "towel", "fan",
    "garage", "relay", "hvac_switch", "other", "all",
]))
@click.pass_context
def devices(ctx: click.Context, device_type: str) -> None:
    """List all devices divided by category.

    Use "all" for everything (lights, shades, HVAC, fans, security,
    plus infrastructure: pumps, valves, ventilation, heating, towels,
    garage, relays). Or pick a specific category.
    """

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

        is_all = device_type == "all"

        if not is_all:
            # Filtered to one infrastructure category
            infra = [d for d in cfg.infrastructure if d.category == device_type]
            if ctx.obj.get("json"):
                data = [
                    {"name": d.name, "category": d.category, "state": d.state_name,
                     "address": d.address, "is_dimmer": d.is_dimmer, "zone": d.zone}
                    for d in infra
                ]
                click.echo(json.dumps(data, indent=2))
                return
            for d in infra:
                dtype = "dimmer" if d.is_dimmer else "switch"
                click.echo(f"  {d.name:45s} addr={d.address:3s} [{dtype}]")
            click.echo(f"\n{len(infra)} devices")
            return

        # ── all: collect room-level + infrastructure ──
        from collections import defaultdict

        room_cats: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)

        for room in cfg.rooms:
            for l_ent in room.lights:
                a = (l_ent.addresses or "").split(",")[0]
                dim = "dimmer" if l_ent.is_dimmer else "switch"
                room_cats["Lights"].append((room.name, l_ent.name, f"addr={a}", dim))
            for s_ent in room.shades:
                a = (s_ent.addresses or "").split(",")[0]
                room_cats["Shades"].append((room.name, s_ent.name, f"addr={a}", ""))
            for h_ent in room.hvac:
                a = (h_ent.addresses or "").split(",")[0]
                modes = "heat/cool" if h_ent.has_heat and h_ent.has_cool \
                    else ("heat" if h_ent.has_heat else "cool")
                room_cats["HVAC"].append((room.name, h_ent.name, f"addr={a}", modes))
            for f_ent in room.fans:
                a = (f_ent.addresses or "").split(",")[0]
                extra = f_ent.state_name
                room_cats["Fans"].append((room.name, f_ent.name, f"addr={a}", extra))
            for sec_ent in room.security:
                extra = f"p{sec_ent.partition_number}"
                room_cats["Security"].append(
                    (room.name, sec_ent.name, f"zone={sec_ent.zone_number}", extra))

        infra_cat_map = {
            "pump": "Pumps", "valve": "Valves", "fan": "Ventilation",
            "heating": "Radiant floor", "towel": "Towel warmers",
            "garage": "Garage doors", "hvac_switch": "HVAC switches",
            "relay": "Spare relays", "other": "Other",
        }
        infra_grouped: dict[str, list[InfrastructureDevice]] = defaultdict(list)
        for d in cfg.infrastructure:
            infra_grouped[d.category].append(d)

        if ctx.obj.get("json"):
            json_out: list[dict[str, object]] = []
            for cat, rows in room_cats.items():
                for z, n, addr, extra in rows:
                    row: dict[str, object] = {"category": cat, "name": n,
                                            "zone": z, "address": addr}
                    if extra:
                        row["info"] = extra
                    json_out.append(row)
            for cat, rows in infra_grouped.items():  # type: ignore[assignment]
                for d in rows:  # type: ignore[assignment]
                    json_out.append({
                        "category": infra_cat_map.get(cat, cat), "name": d.name,
                        "address": d.address, "is_dimmer": d.is_dimmer, "zone": d.zone,
                    })
            click.echo(json.dumps(json_out, indent=2))
            return

        total = 0
        for cat_label in ["Lights", "Shades", "HVAC", "Fans", "Security"]:
            rows = room_cats.get(cat_label, [])
            if not rows:
                continue
            click.echo(f"\n── {cat_label} ({len(rows)}) ──")
            for z, n, a, x in rows:
                line = f"  {z:30s} {n:40s} {a:10s}"
                if x:
                    line += f" [{x}]"
                click.echo(line)
            total += len(rows)

        for cat in ["pump", "valve", "fan", "heating", "towel",
                    "garage", "hvac_switch", "relay", "other"]:
            dev_rows = infra_grouped.get(cat, [])
            if not dev_rows:
                continue
            label = infra_cat_map.get(cat, cat)
            click.echo(f"\n── {label} ({len(dev_rows)}) ──")
            for d in dev_rows:
                dtype = "dimmer" if d.is_dimmer else "switch"
                click.echo(f"  {d.name:45s} addr={d.address:3s} [{dtype}]")
            total += len(dev_rows)

        click.echo(f"\n{total} devices total")

    asyncio.run(_run())


@cli.command()
@click.argument("entity_name", required=False, default=None)
@click.argument("state", type=click.Choice(["on", "off"]), default=None)
@click.option("--addr", "addr", default=None, help="Target by KNX group address instead of name")
@click.pass_context
def switch(
    ctx: click.Context, entity_name: str | None,
    state: str | None, addr: str | None,
) -> None:
    """Turn an individual switch/relay entity ON or OFF.

    By name (case-insensitive, partial match):

        savant-cli switch "Bomba" on

    By KNX group address (stable, immune to renames):

        savant-cli switch --addr 6 on
    """

    # Click assigns positional args in order: entity_name first, state second.
    # When --addr is used without entity_name, Click puts "on"/"off" into
    # entity_name and state gets nothing. Detect and swap.
    if addr is not None and entity_name in ("on", "off") and state is None:
        state = entity_name
        entity_name = None

    if addr is not None:
        pass  # entity_name not needed
    elif entity_name is not None:
        pass  # normal name-based path
    else:
        raise click.UsageError("Either ENTITY_NAME or --addr is required")

    if state is None:
        raise click.UsageError("Missing STATE argument: on or off")

    # mypy narrows: entity_name is str when addr is None at this point
    assert entity_name is not None or addr is not None

    async def _run() -> None:
        async with _make_client(ctx) as client:
            cfg = await client.get_config()

        if addr is not None:
            # ── Match by stable address ──
            matches: list[tuple[str, str, str]] = []  # (zone, name, address)
            for d in cfg.infrastructure:
                if d.address == addr:
                    matches.append((d.zone, d.name, d.address))
            # Also search room entities by address
            if not matches:
                for room in cfg.rooms:
                    for e in room.lights:
                        a = (e.addresses or "").split(",")[0]
                        if a == addr:
                            matches.append((room.name, e.name, a))
            if not matches:
                click.echo(f"No entity with address {addr} found", err=True)
                return
            zone_name, ent_name, ent_addr = matches[0]
        else:
            # ── Match by name (case-insensitive, partial) ──
            assert entity_name is not None  # ensured by outer validation
            name_lower = entity_name.lower()
            matches = []
            for d in cfg.infrastructure:
                if name_lower in d.name.lower():
                    matches.append((d.zone, d.name, d.address))
            for room in cfg.rooms:
                for e in room.lights:
                    if not e.is_dimmer and name_lower in e.name.lower():
                        a = (e.addresses or "").split(",")[0]
                        matches.append((room.name, e.name, a))

            if not matches:
                click.echo(f"No entity matching '{entity_name}' found", err=True)
                return

            if len(matches) > 1:
                click.echo(f"Multiple matches for '{entity_name}':")
                for zone_name_, ent_name_, _ in matches:
                    click.echo(f"  {ent_name_:45s} zone={zone_name_}")
                click.echo("Add --addr with the exact address to disambiguate")
                return

            zone_name, ent_name, ent_addr = matches[0]

        if state == "on":
            req = switch_on(zone=zone_name, address=ent_addr)
        else:
            req = switch_off(zone=zone_name, address=ent_addr)

        async with _make_client(ctx) as client:
            await client.send_service_request(req)

        click.echo(f"{state.upper()} {ent_name}  (addr={ent_addr}, zone={zone_name})")

    asyncio.run(_run())


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """System status overview — connection + config summary."""

    async def _run() -> None:
        client = _make_client(ctx)
        await client.connect()

        # Fetch config
        cfg = await client.get_config()

        # Subscribe to a few global states for live data
        live_states: dict[str, object] = {}

        def on_system(k: str, v: object) -> None:
            live_states[k] = v

        client.state_manager.subscribe("global.SystemHasStarted", on_system)
        client.state_manager.subscribe("global.SystemIsReady", on_system)
        client.state_manager.subscribe("global.ActiveZones", on_system)
        await client.register_states([
            "global.SystemHasStarted",
            "global.SystemIsReady",
            "global.ActiveZones",
        ])

        # Wait a moment for state updates
        await asyncio.sleep(2.0)

        if ctx.obj.get("json"):
            data = {
                "host": client.host,
                "port": client.port,
                "host_name": client.session.host_name,
                "host_uid": client.session.host_uid,
                "home_id": client.session.home_id,
                "system_started": live_states.get("global.SystemHasStarted"),
                "system_ready": live_states.get("global.SystemIsReady"),
                "active_zones": live_states.get("global.ActiveZones"),
                "rooms": len(cfg.rooms),
                "entities": {
                    "lights": sum(len(r.lights) for r in cfg.rooms),
                    "shades": sum(len(r.shades) for r in cfg.rooms),
                    "hvac": sum(len(r.hvac) for r in cfg.rooms),
                    "fans": sum(len(r.fans) for r in cfg.rooms),
                    "security": sum(len(r.security) for r in cfg.rooms),
                },
            }
            click.echo(json.dumps(data, indent=2))
            await client.disconnect()
            return

        click.echo("\n── System Status ──────────────────────────")
        click.echo(f"  Host:        {client.host}:{client.port}")
        click.echo(f"  Name:        {client.session.host_name}")
        click.echo(f"  UID:         {client.session.host_uid}")
        click.echo(f"  Home ID:     {client.session.home_id}")
        click.echo(f"  Started:     {live_states.get('global.SystemHasStarted', '?')}")
        click.echo(f"  Ready:       {live_states.get('global.SystemIsReady', '?')}")
        click.echo(f"  ActiveZones: {live_states.get('global.ActiveZones', '?')}")

        click.echo(f"\n── Configuration ({len(cfg.rooms)} rooms) ────")
        total = {
            "lights": sum(len(r.lights) for r in cfg.rooms),
            "shades": sum(len(r.shades) for r in cfg.rooms),
            "hvac": sum(len(r.hvac) for r in cfg.rooms),
            "fans": sum(len(r.fans) for r in cfg.rooms),
            "security": sum(len(r.security) for r in cfg.rooms),
        }
        click.echo(f"  Lights:   {total['lights']}")
        click.echo(f"  Shades:   {total['shades']}")
        click.echo(f"  HVAC:     {total['hvac']}")
        click.echo(f"  Fans:     {total['fans']}")
        click.echo(f"  Security: {total['security']}")
        click.echo(f"  Services: {len(cfg.zones)}")
        click.echo(f"  Infrastructure: {len(cfg.infrastructure)} devices")

        await client.disconnect()

    asyncio.run(_run())


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
