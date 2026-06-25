# Environment Control

[< Back to Overview](../SAVANT.md) | [Service Control](service-control.md)

---

## Lighting

### Commands

| Request | Arguments | Description |
|---------|-----------|-------------|
| `__RoomSetBrightness` | `BrightnessLevel` (0-100), `USE_LAST_DIMMER_VALUE` (0/1) | Room-level brightness |
| Entity-specific | Via `requestForEvent()` | Individual light control |

### Example

```json
{
  "serviceID": "SVC_ENV_LIGHTING",
  "zone": "Living Room",
  "request": "__RoomSetBrightness",
  "requestArguments": {
    "BrightnessLevel": 75,
    "USE_LAST_DIMMER_VALUE": 0
  }
}
```

### State Keys

- `{Room}.RoomLightsAreOn` — Boolean
- `{Room}.BrightnessLevel` — 0-100
- `{Room}.RoomNumberOfLightsOn` — Count
- `Lights.Lighting_controller.DimmerLevel_{addr}` — Per-dimmer level

**Source:** `control/messaging/environment/LightRequests.java`

---

## HVAC / Climate Control

### ServiceRequest Commands

| Request | Event Type | Arguments |
|---------|-----------|-----------|
| `setCoolPoint` | 3 | Temperature setpoint |
| `setHeatPoint` | 6 | Temperature setpoint |
| `setSingleSetPoint` | 9 | Temperature setpoint |

### DIS Schedule Commands (via `hvacSchedule` app)

| Request | Arguments |
|---------|-----------|
| `ActivateProfile` | Profile name |
| `DeactivateSchedule` | — |
| `DeleteProfile` | Profile name |
| `SaveProfileProperties` | Full profile object |
| `HoldUntil` | Duration (0=clear, 1-4=hours, 5=indefinite) |
| `ClearHold` | — |

### HVAC Schedule Profile

```json
{
  "ProfileName": "Winter",
  "Active": true,
  "Mode": "Auto",
  "ProfileDays": [1, 2, 3, 4, 5],
  "ProfileZones": ["Main Floor", "Second Floor"],
  "DateRange": {
    "startDate": "09/03/2014 00:00:00",
    "endDate": "11/03/2014 00:00:00"
  },
  "ProfileSetPoints": {
    "TemperaturePoints": [
      {"time": "00:00:00", "coolPoint": "0.90", "heatPoint": "0.65"},
      {"time": "08:00:00", "coolPoint": "0.90", "heatPoint": "0.60"},
      {"time": "14:00:00", "coolPoint": "0.90", "heatPoint": "0.60"},
      {"time": "18:00:00", "coolPoint": "0.80", "heatPoint": "0.65"}
    ],
    "HumidityPoints": [
      {"time": "00:00:00", "humidifyPoint": "0.35", "dehumidifyPoint": "0"},
      {"time": "08:00:00", "humidifyPoint": "0.25", "dehumidifyPoint": "0"}
    ]
  }
}
```

Temperature/humidity values are **normalized** (0.0 - 1.0 scale).

### State Keys

- `{Zone}.HVAC_controller.ThermostatCurrentSetPoint_1`
- `{Zone}.HVAC_controller.ThermostatMode_1` — Auto/Heat/Cool/Off
- `{Zone}.HVAC_controller.ThermostatFanMode_1` — On/Auto
- `{Zone}.HVAC_controller.IsThermostatHolding_1` — Boolean
- `{Zone}.HVAC_controller.ThermostatHoldUntil_1` — "None" or timestamp
- `{Zone}.HVAC_controller.IsCurrentHVACModeAuto_1` — Boolean
- `{Zone}.HVAC_controller.IsCurrentHVACModeCool` — Boolean
- `{Zone}.HVAC_controller.IsThermostatCurrentFanModeOn` — Boolean
- `{Zone}.HVAC_controller.ThermostatCurrentHumidifyPoint`

**Source:** `control/messaging/hvac/HVACRequests.java`

---

## Shade Control

### Commands

| Request | Arguments | Description |
|---------|-----------|-------------|
| `__RoomSetShadeLevel` | `ShadeLevel` (0-100) | Room-level shade position |
| `__RoomShadeStop` | — | Stop shade motion |

### Entity Types

- Type 4: Variable level (0-100%)
- Other types: Binary (open/close only)

### State Keys

- `{Room}.ShadeLevel` — 0-100
- `{Room}.ShadeLevelIsValid` — Boolean
- `{Room}.RoomShadesAreOpen` — Boolean

**Source:** `control/messaging/shades/ShadeRequests.java`

---

## Fan Control

### Commands

| Request | Arguments | Description |
|---------|-----------|-------------|
| `__RoomSetFanLevel` | `FanLevel` (0-3) | Room fan speed |

### Fan Speed Levels

| Value | Speed |
|-------|-------|
| 0 | Off |
| 1 | Low |
| 2 | Medium |
| 3 | High |

### State Keys

- `{Room}.RoomFansAreOn` — Boolean
- `{Room}.FanLevel` — 0-3

**Source:** `control/messaging/environment/FanRequests.java`

---

## Door Lock

Controlled via entity-based `requestForEvent()` through `ServiceRequest` with `serviceID: "SVC_ENV_DOORLOCK"`.

### State Keys

- `{Room}.RoomDoorLocksAreOpen` — Boolean

---

## Garage Door

Controlled via entity-based `requestForEvent()` through `ServiceRequest` with `serviceID: "SVC_ENV_GARAGE"`.

### State Keys

- `{Room}.RoomGarageDoorsAreOpen` — Boolean

---

## Gate

Controlled via entity-based `requestForEvent()` through `ServiceRequest` with `serviceID: "SVC_ENV_GATE"`.

All paths relative to `com/savantsystems/` under the app package root
