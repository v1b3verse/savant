# Savant Home Automation — Python

## Project Structure
- `pysavant/` — Standalone asyncio library (zero HA dependencies)
- `custom_components/savant/` — Home Assistant custom integration
- `savant_cli/` — CLI tool (click-based)
- `tests/` — All tests (pytest + pytest-asyncio)

## Commands
- `pip install -e ".[dev,cli]"` — dev install
- `pytest` — run all tests
- `pytest tests/pysavant/` — library tests only
- `ruff check .` — lint
- `mypy pysavant/` — type check

## Conventions
- Python 3.12+, strict mypy, ruff linting
- TDD: write tests first, then implementation
- asyncio throughout, `async with` context managers
- Dataclasses with `to_dict()`/`from_dict()` for wire format (camelCase keys)
- Snake_case attributes in Python
- Port 5000 for WebSocket (not 8443)
- FakeTransport in tests/conftest.py for client testing
