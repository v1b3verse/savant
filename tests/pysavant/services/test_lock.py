"""Tests for pysavant.services.lock."""

from pysavant.protocol import SVC_ENV_DOORLOCK
from pysavant.services.lock import lock, unlock


class TestLock:
    def test_lock(self):
        req = lock("Front Door")
        assert req.service_type == SVC_ENV_DOORLOCK
        assert req.request == "__Lock"
        assert req.zone == "Front Door"

    def test_unlock(self):
        req = unlock("Front Door")
        assert req.request == "__Unlock"
