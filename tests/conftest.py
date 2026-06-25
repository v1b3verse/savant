"""Shared test fixtures."""

from __future__ import annotations

import asyncio
import builtins
from typing import Any

import pytest


class FakeTransport:
    """Test double for Transport. Records sends, plays back responses."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, list[dict[str, Any]]]] = []
        self._queue: asyncio.Queue[dict[str, Any] | Exception] = asyncio.Queue()
        self._closed = False

    @property
    def is_connected(self) -> bool:
        return not self._closed

    async def connect(self, host: str, port: int = 5000) -> None:
        pass

    async def send(self, uri: str, messages: list[dict[str, Any]]) -> None:
        self.sent.append((uri, messages))

    async def send_text(self, text: str) -> None:
        self.sent.append(("_text", [{"text": text}]))

    async def receive(self, timeout: float = 30.0) -> dict[str, Any]:
        try:
            item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except builtins.TimeoutError:
            from pysavant.exceptions import TimeoutError

            raise TimeoutError("FakeTransport: queue empty")
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self) -> None:
        self._closed = True

    def enqueue_response(self, wrapper: dict[str, Any]) -> None:
        """Add a response to be returned by receive()."""
        self._queue.put_nowait(wrapper)

    def enqueue_error(self, exc: Exception) -> None:
        """Add an exception to be raised by receive()."""
        self._queue.put_nowait(exc)


@pytest.fixture
def fake_transport() -> FakeTransport:
    return FakeTransport()
