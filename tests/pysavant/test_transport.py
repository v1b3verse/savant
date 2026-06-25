"""Tests for pysavant.transport — pure functions and Transport class."""

import gzip

import msgpack
import pytest

from pysavant.exceptions import ConnectionError, ProtocolError
from pysavant.transport import Transport, decode_payload, encode_message, normalize_keys


class TestEncodeMessage:
    def test_encode_returns_bytes(self):
        result = encode_message({"URI": "test", "messages": []})
        assert isinstance(result, bytes)

    def test_encode_roundtrip_with_msgpack(self):
        original = {"URI": "state/update", "messages": [{"state": "x", "value": 42}]}
        encoded = encode_message(original)
        decoded = msgpack.unpackb(encoded, raw=False)
        assert decoded == original


class TestDecodePayload:
    def test_decode_plain_msgpack(self):
        data = msgpack.packb({"URI": "test", "messages": []}, use_bin_type=True)
        result = decode_payload(data)
        assert result["URI"] == "test"

    def test_decode_gzip_msgpack(self):
        inner = msgpack.packb({"URI": "compressed", "messages": [{"a": 1}]}, use_bin_type=True)
        compressed = gzip.compress(inner)
        result = decode_payload(compressed)
        assert result["URI"] == "compressed"
        assert result["messages"] == [{"a": 1}]

    def test_empty_frame_raises(self):
        with pytest.raises(ProtocolError, match="Empty frame"):
            decode_payload(b"")

    def test_invalid_msgpack_raises(self):
        with pytest.raises(ProtocolError, match="msgpack decode failed"):
            decode_payload(b"\xff\xff\xff")

    def test_invalid_gzip_raises(self):
        with pytest.raises(ProtocolError, match="gzip decompress failed"):
            decode_payload(b"\x1f\x8b\x00\x00")


class TestNormalizeKeys:
    def test_dict_keys_to_str(self):
        result = normalize_keys({b"key": "value", 123: "num"})
        assert result == {"b'key'": "value", "123": "num"}

    def test_nested_dict(self):
        result = normalize_keys({"outer": {"inner": 1}})
        assert result == {"outer": {"inner": 1}}

    def test_list_of_dicts(self):
        result = normalize_keys([{"a": 1}, {"b": 2}])
        assert result == [{"a": 1}, {"b": 2}]

    def test_scalar_passthrough(self):
        assert normalize_keys(42) == 42
        assert normalize_keys("hello") == "hello"
        assert normalize_keys(None) is None


class TestTransport:
    def test_not_connected_initially(self):
        t = Transport()
        assert t.is_connected is False

    async def test_send_when_not_connected_raises(self):
        t = Transport()
        with pytest.raises(ConnectionError, match="Not connected"):
            await t.send("test", [])

    async def test_send_text_when_not_connected_raises(self):
        t = Transport()
        with pytest.raises(ConnectionError, match="Not connected"):
            await t.send_text("ping")

    async def test_receive_when_not_connected_raises(self):
        t = Transport()
        with pytest.raises(ConnectionError, match="Not connected"):
            await t.receive()

    async def test_close_idempotent(self):
        t = Transport()
        await t.close()
        await t.close()  # should not raise
