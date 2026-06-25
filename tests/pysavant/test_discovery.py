"""Tests for pysavant.discovery — UDP probe protocol."""

import msgpack
import pytest

from pysavant.discovery import PROBE_PORT, PROBE_SERVICE, SavantHost, _ProbeProtocol
from pysavant.exceptions import TimeoutError


class TestProbeConstants:
    def test_probe_port(self):
        assert PROBE_PORT == 9101

    def test_probe_service(self):
        assert PROBE_SERVICE == "_control_.ws"


class TestSavantHost:
    def test_defaults(self):
        host = SavantHost()
        assert host.hostname == ""
        assert host.port == 0
        assert host.properties == {}

    def test_creation(self):
        host = SavantHost(
            hostname="192.168.1.100",
            port=9108,
            host_uid="uid1",
            home_id="home1",
            properties={"version": "2.0", "scheme": "wss"},
        )
        assert host.hostname == "192.168.1.100"
        assert host.port == 9108
        assert host.scheme == "wss"

    def test_scheme_default(self):
        host = SavantHost(hostname="test")
        assert host.scheme == "wss"


class TestProbeProtocol:
    def test_collect_empty(self):
        proto = _ProbeProtocol()
        assert proto.collect() == []

    def test_parse_valid_response(self):
        proto = _ProbeProtocol()
        payload = msgpack.packb({
            "UID": "host-abc",
            "homeID": "home-xyz",
            "port": 9108,
            "name": "Savant Host",
            "scheme": "wss",
        })
        proto.datagram_received(payload, ("10.0.0.1", 9101))
        hosts = proto.collect()
        assert len(hosts) == 1
        assert hosts[0].hostname == "10.0.0.1"
        assert hosts[0].port == 9108
        assert hosts[0].host_uid == "host-abc"
        assert hosts[0].home_id == "home-xyz"

    def test_parse_with_home_id_lowercase(self):
        proto = _ProbeProtocol()
        payload = msgpack.packb({
            "UID": "host-abc",
            "homeId": "home-xyz",
            "port": 5000,
        })
        proto.datagram_received(payload, ("10.0.0.1", 9101))
        hosts = proto.collect()
        assert len(hosts) == 1
        assert hosts[0].home_id == "home-xyz"

    def test_parse_ignores_too_short(self):
        proto = _ProbeProtocol()
        proto.datagram_received(b"too short", ("10.0.0.1", 9101))
        assert proto.collect() == []

    def test_parse_ignores_invalid_msgpack(self):
        proto = _ProbeProtocol()
        proto.datagram_received(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff", ("10.0.0.1", 9101))
        assert proto.collect() == []

    def test_parse_ignores_non_dict(self):
        proto = _ProbeProtocol()
        payload = msgpack.packb([1, 2, 3])
        proto.datagram_received(payload, ("10.0.0.1", 9101))
        assert proto.collect() == []

    def test_multiple_responses(self):
        proto = _ProbeProtocol()
        p1 = msgpack.packb({"UID": "host-1", "port": 5000})
        p2 = msgpack.packb({"UID": "host-2", "port": 9108})
        proto.datagram_received(p1, ("10.0.0.1", 9101))
        proto.datagram_received(p2, ("10.0.0.2", 9101))
        hosts = proto.collect()
        assert len(hosts) == 2

    def test_properties_populated(self):
        proto = _ProbeProtocol()
        payload = msgpack.packb({
            "UID": "h1",
            "name": "MyHost",
            "buildNumber": 42,
            "online": True,
        })
        proto.datagram_received(payload, ("10.0.0.1", 9101))
        hosts = proto.collect()
        assert hosts[0].properties["name"] == "MyHost"
        assert hosts[0].properties["buildNumber"] == 42
        assert hosts[0].properties["online"] is True


from unittest.mock import patch
from pysavant.discovery import discover_one  # noqa: E402


class TestDiscoverOne:
    @patch("pysavant.discovery._get_local_subnets", return_value=[("203.0.113.0", 24)])
    async def test_timeout_raises(self, mock_subnets):
        with pytest.raises(TimeoutError):
            await discover_one(timeout=0.1)
