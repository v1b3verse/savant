"""Door lock service request builders."""

from pysavant.models import ServiceRequest
from pysavant.protocol import REQ_LOCK, REQ_UNLOCK, SVC_ENV_DOORLOCK


def lock(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_DOORLOCK,
        request=REQ_LOCK,
        zone=zone,
        component="DoorLocks",
        logical_component="DoorLock_controller",
    )


def unlock(zone: str) -> ServiceRequest:
    return ServiceRequest(
        service_type=SVC_ENV_DOORLOCK,
        request=REQ_UNLOCK,
        zone=zone,
        component="DoorLocks",
        logical_component="DoorLock_controller",
    )
