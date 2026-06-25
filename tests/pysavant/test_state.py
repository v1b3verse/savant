"""Tests for pysavant.state — StateManager."""

from pysavant.state import StateManager


class TestStateManagerRegister:
    def test_register_returns_dicts(self):
        sm = StateManager()
        msgs = sm.register(["global.ActiveZones", "zone.Brightness"])
        assert len(msgs) == 2
        assert msgs[0] == {"state": "global.ActiveZones"}
        assert msgs[1] == {"state": "zone.Brightness"}

    def test_register_tracks_keys(self):
        sm = StateManager()
        sm.register(["key1", "key2"])
        assert sm.registered_keys == {"key1", "key2"}

    def test_unregister_removes_keys(self):
        sm = StateManager()
        sm.register(["key1", "key2"])
        msgs = sm.unregister(["key1"])
        assert len(msgs) == 1
        assert sm.registered_keys == {"key2"}


class TestStateManagerCache:
    def test_handle_update_caches(self):
        sm = StateManager()
        sm.handle_update("key", 42)
        assert sm.get("key") == 42

    def test_get_default(self):
        sm = StateManager()
        assert sm.get("missing") is None
        assert sm.get("missing", "default") == "default"

    def test_get_all(self):
        sm = StateManager()
        sm.handle_update("a", 1)
        sm.handle_update("b", 2)
        assert sm.get_all() == {"a": 1, "b": 2}

    def test_handle_update_batch(self):
        sm = StateManager()
        sm.handle_update_batch(
            [
                {"state": "a", "value": 1},
                {"state": "b", "value": "hello"},
                {"state": "c", "value": True},
            ]
        )
        assert sm.get("a") == 1
        assert sm.get("b") == "hello"
        assert sm.get("c") is True

    def test_batch_skips_empty_keys(self):
        sm = StateManager()
        sm.handle_update_batch([{"state": "", "value": 1}])
        assert sm.get_all() == {}


class TestStateManagerSubscribe:
    def test_exact_match(self):
        sm = StateManager()
        received = []
        sm.subscribe("key1", lambda k, v: received.append((k, v)))
        sm.handle_update("key1", "val1")
        sm.handle_update("key2", "val2")
        assert received == [("key1", "val1")]

    def test_glob_pattern(self):
        sm = StateManager()
        received = []
        sm.subscribe("zone.*", lambda k, v: received.append((k, v)))
        sm.handle_update("zone.brightness", 50)
        sm.handle_update("zone.temp", 72)
        sm.handle_update("global.ready", True)
        assert len(received) == 2

    def test_unsubscribe(self):
        sm = StateManager()
        received = []
        unsub = sm.subscribe("key", lambda k, v: received.append(v))
        sm.handle_update("key", 1)
        unsub()
        sm.handle_update("key", 2)
        assert received == [1]

    def test_unsubscribe_idempotent(self):
        sm = StateManager()
        unsub = sm.subscribe("key", lambda k, v: None)
        unsub()
        unsub()  # should not raise

    def test_callback_exception_logged(self):
        sm = StateManager()

        def bad_callback(k, v):
            raise ValueError("boom")

        sm.subscribe("key", bad_callback)
        # Should not raise, just log
        sm.handle_update("key", 1)

    def test_multiple_subscribers(self):
        sm = StateManager()
        r1, r2 = [], []
        sm.subscribe("key", lambda k, v: r1.append(v))
        sm.subscribe("key", lambda k, v: r2.append(v))
        sm.handle_update("key", 42)
        assert r1 == [42]
        assert r2 == [42]


class TestActiveZones:
    def test_parses_csv(self):
        sm = StateManager()
        sm.handle_update("global.ActiveZones", "Kitchen,Living Room,Bedroom")
        assert sm.active_zones == ["Kitchen", "Living Room", "Bedroom"]

    def test_empty_string(self):
        sm = StateManager()
        sm.handle_update("global.ActiveZones", "")
        assert sm.active_zones == []

    def test_not_set(self):
        sm = StateManager()
        assert sm.active_zones == []

    def test_trims_whitespace(self):
        sm = StateManager()
        sm.handle_update("global.ActiveZones", " Kitchen , Bedroom ")
        assert sm.active_zones == ["Kitchen", "Bedroom"]
