"""Tests for pysavant.discovery."""

import pytest

from pysavant.discovery import MDNS_SERVICE_TYPE, SavantHost, discover, discover_one
from pysavant.exceptions import TimeoutError


class TestSavantHost:
    def test_defaults(self):
        host = SavantHost()
        assert host.hostname == ""
        assert host.port == 0
        assert host.properties == {}

    def test_creation(self):
        host = SavantHost(
            hostname="192.168.1.100",
            port=5000,
            host_uid="uid1",
            home_id="home1",
            properties={"version": "2.0"},
        )
        assert host.hostname == "192.168.1.100"
        assert host.port == 5000
        assert host.host_uid == "uid1"


class TestMDNSServiceType:
    def test_service_type(self):
        assert MDNS_SERVICE_TYPE == "_savant-control._tcp.local."


class TestDiscoverOne:
    async def test_timeout_raises(self):
        """With no real Savant hosts on network, should timeout quickly."""
        with pytest.raises(TimeoutError):
            await discover_one(timeout=0.1)


class TestDiscover:
    async def test_returns_empty_list_on_timeout(self):
        """With no real hosts, returns empty list."""
        result = await discover(timeout=0.1)
        assert result == []
