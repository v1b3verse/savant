"""Scene service request builders (DIS-based)."""

from pysavant.models import DISRequest


def apply_scene(scene_id: str) -> DISRequest:
    return DISRequest(
        app="dashboard",
        request="applyScene",
        request_args={"sceneId": scene_id},
    )


def fetch_scenes() -> DISRequest:
    return DISRequest(
        app="dashboard",
        request="getScenes",
    )


def remove_scene(scene_id: str) -> DISRequest:
    return DISRequest(
        app="dashboard",
        request="removeScene",
        request_args={"sceneId": scene_id},
    )
