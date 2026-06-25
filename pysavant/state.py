"""State subscription manager with pub/sub and caching."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from collections.abc import Callable
from typing import Any

from pysavant.models import StateRegister

logger = logging.getLogger(__name__)

Callback = Callable[[str, Any], Any]


class StateManager:
    """Manages state subscriptions, caching, and callback dispatch."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._registered: set[str] = set()
        self._subscribers: list[tuple[str, Callback]] = []

    @property
    def registered_keys(self) -> set[str]:
        return set(self._registered)

    @property
    def active_zones(self) -> list[str]:
        """Parse global.ActiveZones comma-separated value."""
        raw = self._cache.get("global.ActiveZones", "")
        if not raw or not isinstance(raw, str):
            return []
        return [z.strip() for z in raw.split(",") if z.strip()]

    def register(self, keys: list[str]) -> list[dict[str, Any]]:
        """Prepare StateRegister dicts to send. Tracks registered keys."""
        msgs = []
        for key in keys:
            self._registered.add(key)
            msgs.append(StateRegister(state=key).to_dict())
        return msgs

    def unregister(self, keys: list[str]) -> list[dict[str, Any]]:
        """Prepare StateUnregister dicts. Removes from tracked set."""
        msgs = []
        for key in keys:
            self._registered.discard(key)
            msgs.append(StateRegister(state=key).to_dict())
        return msgs

    def handle_update(self, key: str, value: Any) -> None:
        """Update cache and fire matching callbacks."""
        self._cache[key] = value
        self._fire_callbacks(key, value)

    def handle_update_batch(self, updates: list[dict[str, Any]]) -> None:
        """Process a list of state update dicts."""
        for update in updates:
            key = update.get("state", "")
            value = update.get("value")
            if key:
                self.handle_update(key, value)

    def subscribe(self, key_pattern: str, callback: Callback) -> Callable[[], None]:
        """Subscribe to state updates matching a glob pattern.

        Returns an unsubscribe function.
        """
        entry = (key_pattern, callback)
        self._subscribers.append(entry)

        def unsubscribe() -> None:
            try:
                self._subscribers.remove(entry)
            except ValueError:
                pass

        return unsubscribe

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value from cache."""
        return self._cache.get(key, default)

    def get_all(self) -> dict[str, Any]:
        """Return full cache snapshot."""
        return dict(self._cache)

    def _fire_callbacks(self, key: str, value: Any) -> None:
        for pattern, callback in self._subscribers:
            if fnmatch.fnmatch(key, pattern):
                try:
                    result = callback(key, value)
                    if asyncio.iscoroutine(result):
                        # Schedule async callback
                        loop = asyncio.get_event_loop()
                        loop.create_task(result)
                except Exception:
                    logger.exception("Error in state callback for %s", key)
