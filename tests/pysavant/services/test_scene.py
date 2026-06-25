"""Tests for pysavant.services.scene."""

from pysavant.services.scene import apply_scene, fetch_scenes, remove_scene


class TestScene:
    def test_apply_scene(self):
        req = apply_scene("scene-123")
        assert req.app == "dashboard"
        assert req.request == "applyScene"
        assert req.request_args == {"sceneId": "scene-123"}

    def test_fetch_scenes(self):
        req = fetch_scenes()
        assert req.app == "dashboard"
        assert req.request == "getScenes"
        d = req.to_dict()
        assert "requestArgs" not in d

    def test_remove_scene(self):
        req = remove_scene("scene-456")
        assert req.request == "removeScene"
        assert req.request_args == {"sceneId": "scene-456"}
