"""Protocol constants for Savant WebSocket communication."""

from enum import IntEnum


class SessionState(IntEnum):
    """Session handshake states."""

    DISCONNECTED = 0
    CONNECTED = 1
    AUTH_REQUIRED = 2
    READY = 3


# Session URIs
URI_DEVICE_PRESENT = "session/devicePresent"
URI_DEVICE_RECOGNIZED = "session/deviceRecognized"
URI_AUTH_REQUEST = "session/authenticationRequest"
URI_AUTH_RESPONSE = "session/authenticationResponse"

# State URIs
URI_STATE_REGISTER = "state/register"
URI_STATE_UNREGISTER = "state/unregister"
URI_STATE_UPDATE = "state/update"
URI_STATE_SET = "state/set"

# Service URIs
URI_SERVICE_REQUEST = "service/request"
URI_SERVICE_RESULT = "service/result"

# DIS URIs (format: dis/{app}/request)
URI_DIS_REQUEST_FMT = "dis/{app}/request"
URI_DIS_RESPONSE_FMT = "dis/{app}/response"

# Service type constants
SVC_ENV_LIGHTING = "SVC_ENV_LIGHTING"
SVC_ENV_HVAC = "SVC_ENV_HVAC"
SVC_ENV_SHADE = "SVC_ENV_SHADE"
SVC_ENV_FAN = "SVC_FAN"
SVC_ENV_DOORLOCK = "SVC_DOOR_LOCK"
SVC_ENV_CLIMATE = "SVC_ENV_CLIMATE"
SVC_AV_AUDIO = "SVC_AV_AUDIO"
SVC_AV_VIDEO = "SVC_AV_VIDEO"
SVC_AV_MEDIA = "SVC_AV_MEDIA"
SVC_SECURITY = "SVC_SECURITY"
SVC_GARAGE_DOOR = "SVC_GARAGE_DOOR"
SVC_FIREPLACE = "SVC_FIREPLACE"
SVC_POOL_SPA = "SVC_POOL_SPA"
SVC_IRRIGATION = "SVC_IRRIGATION"
SVC_SCENE_GEN = "SVC_SCENE_GEN"
SVC_POWER = "SVC_POWER"
SVC_ENV_DAYLIGHT_MIX = "SVC_ENV_DAYLIGHT_MIX"

# Common service request names
REQ_ROOM_ON = "__RoomOn"
REQ_ROOM_OFF = "__RoomOff"
REQ_ROOM_SET_BRIGHTNESS = "__RoomSetBrightness"
REQ_ROOM_RAISE = "__RoomRaise"
REQ_ROOM_LOWER = "__RoomLower"
REQ_ACTIVATE_SCENE = "__ActivateScene"
REQ_SET_COOL_POINT = "__SetCoolPoint"
REQ_SET_HEAT_POINT = "__SetHeatPoint"
REQ_SET_SINGLE_SETPOINT = "__SetSingleSetPoint"
REQ_SET_SHADE_LEVEL = "__SetShadeLevel"
REQ_SHADE_STOP = "__ShadeStop"
REQ_SET_FAN_LEVEL = "__SetFanLevel"
REQ_LOCK = "__Lock"
REQ_UNLOCK = "__Unlock"

# Well-known global state keys
STATE_SYSTEM_HAS_STARTED = "global.SystemHasStarted"
STATE_SYSTEM_IS_READY = "global.SystemIsReady"
STATE_ACTIVE_ZONES = "global.ActiveZones"

# Network defaults
DEFAULT_PORT = 5000
PING_INTERVAL = 1.0
RECEIVE_TIMEOUT = 30.0
CONNECT_TIMEOUT = 15.0

# Protocol defaults
MESSAGE_FORMAT = 1
PROTOCOL_VERSION = "2.0"
