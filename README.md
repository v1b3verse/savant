# Savant Home Automation

Python library and Home Assistant integration for Savant smart home systems.

## Components

- **pysavant** — Standalone asyncio library for controlling Savant systems over local WebSocket
- **custom_components/savant** — Home Assistant custom integration
- **savant-cli** — Command-line tool

## Installation

```bash
pip install -e ".[dev,cli]"
```

## Usage

```python
async with SavantClient(host="192.168.1.100", user="admin", password="pass") as client:
    await client.register_states(["global.ActiveZones"])
    # State updates arrive via callbacks
```

## Development

```bash
pytest                    # run all tests
ruff check .              # lint
mypy pysavant/            # type check
```
