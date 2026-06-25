# Scene Management

[< Back to Overview](../SAVANT.md) | [Service Control](service-control.md)

---

## Overview

Scenes are managed via the DIS protocol with `app: "dashboard"`. Each scene captures a snapshot of system state (lighting, AV, HVAC, shades, etc.) that can be applied, scheduled, or triggered by automation conditions.

---

## Scene Operations

All sent as `DISRequest` with `app: "dashboard"`:

| Request | Description |
|---------|-------------|
| `ApplyScene` | Activate a scene |
| `RemoveScene` | Delete a scene |
| `CreateScene` / `UpsertScene` | Create or update |
| `FetchScene` | Get scene details |
| `CaptureScene` | Capture current system state as scene |
| `OrderScenes` | Reorder scene list |
| `ActivateSchedule` / `DeactivateSchedule` | Toggle scheduled execution |
| `ActivateAutomation` / `DeactivateAutomation` | Toggle condition-based automation |
| `ActivateCountdown` / `DeactivateCountdown` | Timed scene execution |
| `SuggestSceneNames` | Get AI-suggested names |

### Apply Example

```json
{
  "app": "dashboard",
  "request": "ApplyScene",
  "requestArguments": {
    "id": "UEFP-XCVD-YQRE",
    "version": "2.0"
  }
}
```

Scene version is `"2.0"` for modern hosts, `"1.0"` for older ones.

---

## Scene Data Model

```json
{
  "id": "UEFP-XCVD-YQRE",
  "name": "Movie Night",
  "isActive": false,
  "isGlobal": true,
  "isScheduled": false,
  "isScheduleActive": false,
  "isCountdownActive": false,
  "isAutomationActive": false,
  "fadeTime": 2.0,
  "tags": ["Living Room", "Relax", "Favorite"],
  "version": "2.0",
  "definition": {
    "power": { ... },
    "volume": { ... },
    "av": { ... },
    "lighting": { ... },
    "hvac": { ... },
    "schedule": { ... }
  }
}
```

### Definition Sections

**Power** — Which services are on in which rooms:
```json
"power": {
  "rooms": {
    "Living Room": {
      "Living Room-Cable 2-Cable_box-1-SVC_AV_TV": "1"
    }
  },
  "lightingOff": ["Master Bedroom"]
}
```

**Volume** — Per-room volume levels:
```json
"volume": { "Living Room": "24", "Kitchen": "75" }
```

**AV** — Source device states:
```json
"av": {
  "Cable 2.Cable_box": {
    "states": { "CurrentStation": "32" },
    "alias": "Kids Cable",
    "rooms": ["Living Room"],
    "serviceID": "SVC_AV_TV"
  }
}
```

**Lighting** — Dimmer levels:
```json
"lighting": {
  "Lights.Lighting_controller": {
    "states": { "DimmerLevel_2_1_2_0": 30, "DimmerLevel_1_49_4_0": "100" },
    "alias": "Lighting",
    "rooms": ["Living Room"],
    "serviceID": "SVC_ENV_LIGHTING"
  }
}
```

**HVAC** — Thermostat settings:
```json
"hvac": {
  "Main Floor.HVAC_controller": {
    "serviceID": "SVC_ENV_HVAC",
    "states": {
      "ThermostatCurrentSetPoint_1": "50",
      "ThermostatMode_1": "Auto",
      "ThermostatFanMode_1": "On"
    },
    "zones": ["Main Floor"],
    "rooms": ["Living Room", "Kitchen"]
  }
}
```

**Schedule** — Recurring execution:
```json
"schedule": {
  "scheduledTime": 0,
  "activeDateRange": {
    "startMonth": "7", "endMonth": "10",
    "startDate": "1", "endDate": "28"
  },
  "scheduledDays": ["NO","YES","YES","YES","YES","YES","NO"],
  "type": "normal",
  "repeatPeriod": "weekly"
}
```

---

## Automation Conditions

Scenes can be triggered by conditions:

| Category | Condition ID | Fields |
|----------|-------------|--------|
| Camera | `Camera:{component}.{logicalComponent}.MotionDetected` | `cameraMotionDetected` (bool) |
| Entry | `Entry:{component}.{logicalComponent}.MotionDetected` | `entryMotionDetected` (bool) |
| Security | `Security:PartitionStatus.{entityID}` | `securitySystemState` (Armed/Disarmed/Alarmed/...) |
| Energy | `Energy:Grid.IsAvailable` | `gridAvailable` (bool) |
| Energy | `Energy:Battery.StateOfCharge` | `decreasesTo` (int 10-100) |
| Time | `Time:global.CurrentTime` | `hour` (0-23), `minute` (0-59) |
| Time | `Time:CelestialWithOffset` | `celestial` (Dawn/Sunrise/SolarNoon/Sunset/Dusk), `minutesOffset` |
| Time | `Time:DayOfTheWeek` | `daysOfWeek` (Sunday-Saturday, multiselect) |
| Time | `Time:DateRange` | `startMonth/Date`, `endMonth/Date` |

### Condition Dependencies

Each condition declares dependencies on other conditions:
- `"required"` — Must also be configured
- `"optional"` — May be configured
- `"forbidden"` — Cannot coexist

---

## Source

`com/savantsystems/control/messaging/SavantScene.java`
