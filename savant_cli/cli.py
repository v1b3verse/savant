"""CLI tool for Savant home automation."""

from __future__ import annotations

import asyncio
import sys

import click

from pysavant.client import SavantClient
from pysavant.discovery import discover
from pysavant.protocol import DEFAULT_PORT
from pysavant.services import lighting


@click.group()
@click.option("--host", envvar="SAVANT_HOST", help="Savant host IP address")
@click.option("--port", default=DEFAULT_PORT, envvar="SAVANT_PORT", help="WebSocket port")
@click.option("--user", envvar="SAVANT_USER", default="", help="Username")
@click.option("--password", envvar="SAVANT_PASSWORD", default="", help="Password")
@click.option("--token", envvar="SAVANT_TOKEN", default="", help="Host token for re-auth")
@click.option("--secret", envvar="SAVANT_SECRET", default="", help="Secret key")
@click.pass_context
def cli(
    ctx: click.Context,
    host: str | None,
    port: int,
    user: str,
    password: str,
    token: str,
    secret: str,
) -> None:
    """Savant home automation CLI."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port
    ctx.obj["user"] = user
    ctx.obj["password"] = password
    ctx.obj["token"] = token
    ctx.obj["secret"] = secret


def _make_client(ctx: click.Context) -> SavantClient:
    host = ctx.obj["host"]
    if not host:
        click.echo("Error: --host is required", err=True)
        sys.exit(1)
    return SavantClient(
        host=host,
        port=ctx.obj["port"],
        user=ctx.obj["user"],
        password=ctx.obj["password"],
        host_token=ctx.obj["token"],
        secret_key=ctx.obj["secret"],
    )


@cli.command("discover")
@click.option("--timeout", default=5.0, help="Discovery timeout in seconds")
def discover_cmd(timeout: float) -> None:
    """Scan for Savant hosts on the network."""

    async def _run() -> None:
        hosts = await discover(timeout=timeout)
        if not hosts:
            click.echo("No Savant hosts found.")
            return
        for h in hosts:
            click.echo(f"{h.hostname}:{h.port} uid={h.host_uid} home={h.home_id}")

    asyncio.run(_run())


@cli.command("light")
@click.argument("zone")
@click.argument("level", type=int)
@click.pass_context
def light_cmd(ctx: click.Context, zone: str, level: int) -> None:
    """Set light brightness for ZONE to LEVEL (0-100)."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            req = lighting.set_brightness(zone, level)
            await client.send_service_request(req)
            click.echo(f"Set {zone} brightness to {level}")

    asyncio.run(_run())


@cli.command("on")
@click.argument("zone")
@click.pass_context
def on_cmd(ctx: click.Context, zone: str) -> None:
    """Turn on lights in ZONE."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            req = lighting.turn_on(zone)
            await client.send_service_request(req)
            click.echo(f"Turned on {zone}")

    asyncio.run(_run())


@cli.command("off")
@click.argument("zone")
@click.pass_context
def off_cmd(ctx: click.Context, zone: str) -> None:
    """Turn off lights in ZONE."""

    async def _run() -> None:
        async with _make_client(ctx) as client:
            req = lighting.turn_off(zone)
            await client.send_service_request(req)
            click.echo(f"Turned off {zone}")

    asyncio.run(_run())


@cli.command("state")
@click.argument("key")
@click.pass_context
def state_cmd(ctx: click.Context, key: str) -> None:
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


@cli.command("zones")
@click.pass_context
def zones_cmd(ctx: click.Context) -> None:
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

            zones = client.state_manager.active_zones
            if not zones:
                click.echo("No active zones")
                return
            for zone in zones:
                click.echo(zone)

    asyncio.run(_run())


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
