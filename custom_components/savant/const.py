"""Constants for the Savant integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass

DOMAIN = "savant"

CONF_HOST_TOKEN = "host_token"
CONF_SECRET_KEY = "secret_key"
CONF_HOST_UID = "host_uid"
CONF_HOME_ID = "home_id"

DEFAULT_PORT = 9108

# ── Infrastructure device class mappings ──────────────────────────────────

INFRASTRUCTURE_DEVICE_CLASSES: dict[str, SwitchDeviceClass] = {
    "pump": SwitchDeviceClass.OUTLET,
    "valve": SwitchDeviceClass.SWITCH,
    "fan": SwitchDeviceClass.SWITCH,
    "heating": SwitchDeviceClass.SWITCH,
    "towel": SwitchDeviceClass.SWITCH,
    "garage": SwitchDeviceClass.SWITCH,
    "hvac_switch": SwitchDeviceClass.SWITCH,
    "relay": SwitchDeviceClass.SWITCH,
    "other": SwitchDeviceClass.SWITCH,
}

# ── Binary sensor device class heuristic (name prefix → device class) ─────

BINARY_SENSOR_PREFIX_CLASSES: dict[str, BinarySensorDeviceClass] = {
    "MG.": BinarySensorDeviceClass.MOTION,
    "SK.": BinarySensorDeviceClass.DOOR,
    "FS.": BinarySensorDeviceClass.SMOKE,
    "GT.": BinarySensorDeviceClass.GARAGE_DOOR,
}

BINARY_SENSOR_DEFAULT_CLASS = BinarySensorDeviceClass.WINDOW

# ── HVAC state key suffixes (per-address) ─────────────────────────────────

HVAC_STATE_PROPERTIES: list[str] = [
    "ThermostatCurrentTemperature",
    "ThermostatCurrentCoolPoint",
    "ThermostatCurrentHeatPoint",
    "ThermostatCurrentSetPoint",
    "ThermostatCurrentRemoteTemperature",
    "ThermostatCurrentHumiditySetPoint",
    "ThermostatCurrentHumidifyPoint",
    "ThermostatCurrentDehumidifyPoint",
    "ThermostatHumidityMode",
    "IsThermostatHumidityModeOn",
    "IsThermostatHumidityModeOff",
    "ThermostatCurrentHumidity",
    "IsThermostatCurrentFanModeAuto",
    "IsThermostatCurrentFanModeOn",
    "ThermostatFanMode",
    "ThermostatFanStatus",
    "IsThermostatFanStopped",
    "IsThermostatFanRunning",
    "ThermostatHVACState",
    "IsCurrentHVACModeAuto",
    "IsCurrentHVACModeCool",
    "IsCurrentHVACModeHeat",
    "IsCurrentHVACModeEmergencyHeat",
    "IsCurrentHVACModeOff",
    "RelativeHumidityMode",
    "ThermostatMode",
    "ThermostatTempUnit",
    "IsGRelayEnergized",
    "IsY1RelayEnergized",
    "IsW1RelayEnergized",
    "IsY2RelayEnergized",
]

# ── Security partition state key suffixes ─────────────────────────────────

SECURITY_PARTITION_PROPERTIES: list[str] = [
    "CurrentPartitionStatus",
    "PartitionArmingStatus",
    "IsPartitionReady",
    "IsPartitionAlarmActive",
    "ExitDelaySeconds",
    "ExitDelayArmingType",
    "PartitionSmartPinArmingStatus",
    "ZonesToBypassTotal",
    "ZonesToBypassRemaining",
    "ZonesBypassedInPartition",
    "ZonesFaultedInPartition",
    "ZonesUnknownFailureInPartition",
]

SECURITY_ZONE_PROPERTIES: list[str] = [
    "ZoneSummary",
    "IsZoneBypassed",
]

# ── Shade state key resolution ────────────────────────────────────────────

SHADE_STATE_PROPERTIES: list[str] = [
    "CurrentPosition",
]
