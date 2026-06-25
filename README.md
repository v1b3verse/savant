# Savant Home Automation

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#)

Python library and Home Assistant integration for [Savant](https://www.savant.com/) smart home systems. Communicates directly with the Savant Smart Host over the local network — no cloud dependency.

---

## Components

| Component | Description |
|-----------|-------------|
| `savant` (HA) | Home Assistant custom integration — lights, climate, covers, fans, locks, switches, sensors, scenes |
| `savant-cli` | Click-based CLI for discovery, control, and debugging |
| `pysavant` | Async Python library — WebSocket connection, auth, state subscriptions, device control |

---

## Home Assistant Integration

A full-featured custom integration with push-based state updates (no polling).

### Installation

Copy `custom_components/savant/` into your Home Assistant `config/custom_components/` directory:

```bash
mkdir -p config/custom_components
cp -r custom_components/savant config/custom_components/
```

Restart Home Assistant and add the integration via **Settings → Devices & Services → Add Integration → Savant**.

The config flow supports **manual setup** (host, port, username, password) and **mDNS discovery** (auto-detected hosts appear in the integrations panel).

### Supported Platforms

| Platform | Entities |
|----------|----------|
| **Light** | Per-address dimmers with brightness control |
| **Climate** | Per-address thermostats — setpoint, mode, temperature + humidity sensors |
| **Cover** | Per-address shades — open, close, stop, set position |
| **Fan** | Per-address fans — speed control (off/low/med/high) |
| **Lock** | Room-level door locks |
| **Switch** | Infrastructure devices — pumps, valves, relays, towel warmers, non-dimmer lights |
| **Sensor** | Temperature and humidity per-HVAC-entity |
| **Binary Sensor** | Security zones — motion, door, smoke, garage door sensors |
| **Scene** | Savant scenes via DIS protocol |

### How It Works

1. **Connects** to the Savant host over local WSS (port 9108)
2. **Downloads** the house configuration (`uiconfig.tar.gz` → SQLite database)
3. **Discovers** all rooms, entities, and services from the database
4. **Subscribes** to every entity's state keys for real-time push updates
5. **Creates** Home Assistant entities per device — no polling, state changes arrive instantly via WebSocket push

---

## Command Line Tool

```bash
pip install ".[cli]"

savant-cli --help
```

| Command | Description |
|---------|-------------|
| `savant-cli discover` | Scan for Savant hosts via mDNS |
| `savant-cli connect` | Test connection |
| `savant-cli status` | System status overview |
| `savant-cli config` | Download and show house configuration |
| `savant-cli rooms` | List rooms with capabilities |
| `savant-cli room <name>` | Show detailed room info |
| `savant-cli entities <type>` | List entities (lights/hvac/shades/fans/security) |
| `savant-cli devices` | List all infrastructure devices |
| `savant-cli light <zone> <level>` | Set brightness (0–100) |
| `savant-cli on/off <zone>` | Toggle lights |
| `savant-cli switch <name> on/off` | Control individual relays |
| `savant-cli state <key>` | Subscribe to a state key |
| `savant-cli listen` | Subscribe to all states and print in real time |
| `savant-cli zones` | List active zones |

```bash
export SAVANT_HOST=192.168.1.100
export SAVANT_USER=admin
export SAVANT_PASSWORD=pass

savant-cli status
savant-cli rooms
savant-cli light "Living Room" 75
```

---

## pysavant Library

Standalone asyncio library with zero Home Assistant dependencies.

### Features

- **mDNS discovery** — find Savant hosts on the network
- **Local WebSocket** — direct WSS connection, no cloud required
- **Auto port fallback** — tries 5000 → 9108 → 8443
- **State subscriptions** — pub/sub with real-time push updates
- **Service control** — lighting, HVAC, shades, fans, locks, switches
- **Config download** — parses the SQLite database from the host into structured models
- **Reconnection** — exponential backoff with state re-registration

### Install

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev,cli]"
```

### Quick Start

```python
import asyncio
from pysavant.client import SavantClient


async def main():
    async with SavantClient(
        host="192.168.1.100",
        user="admin",
        password="pass",
    ) as client:
        client.state_manager.subscribe("*", lambda k, v: print(f"{k} = {v}"))
        await client.register_states(["global.ActiveZones"])
        await asyncio.sleep(10)


asyncio.run(main())
```

### mDNS Discovery

```python
from pysavant.discovery import discover

hosts = await discover(timeout=3.0)
for h in hosts:
    print(f"{h.hostname}:{h.port}  uid={h.host_uid}")
```

### Download House Configuration

```python
cfg = await client.get_config()

for room in cfg.rooms:
    print(f"{room.name} ({len(room.lights)} lights, {len(room.hvac)} HVAC)")
```

### Control Devices

```python
from pysavant.services.lighting import set_brightness
from pysavant.services.shade import open_cover
from pysavant.services.climate import set_single_setpoint

await client.send_service_request(set_brightness("Kitchen", 75))
await client.send_service_request(open_cover("Living Room"))
await client.send_service_request(set_single_setpoint("Main Floor", 72.0))
```

---

## Development

```bash
pip install -e ".[dev,cli]"

pytest                          # all tests
pytest tests/pysavant/          # library tests only
pytest tests/cli/               # CLI tests
pytest tests/integration/       # HA integration tests
pytest --cov=pysavant           # with coverage

ruff check .
ruff check --fix .
mypy pysavant/
```

---

## Project Structure

```
savant/
├── custom_components/savant/        # Home Assistant integration
│   ├── __init__.py                  # Platform setup
│   ├── config_flow.py               # Manual + zeroconf setup
│   ├── coordinator.py               # Push-based coordinator
│   ├── const.py                     # Integration constants
│   ├── light.py / climate.py / ...  # Entity platforms
│   └── manifest.json
├── savant_cli/                      # CLI tool
├── pysavant/                        # Core library (no HA deps)
│   ├── client.py                    # High-level async client
│   ├── session.py                   # Handshake state machine
│   ├── transport.py                 # WebSocket + msgpack/JSON
│   ├── protocol.py                  # Constants and URIs
│   ├── models.py                    # Dataclass models
│   ├── state.py                     # State subscription manager
│   ├── config.py                    # SQLite config parser
│   ├── discovery.py                 # mDNS service browser
│   └── services/                    # Service request builders
├── docs/                            # Protocol documentation
└── tests/                           # pytest suite
```

---

## License

MIT
