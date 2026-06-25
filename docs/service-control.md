# Service Control Protocol

[< Back to Overview](../SAVANT.md)

---

## ServiceRequest Message

All device control goes through `ServiceRequest`, sent via URI `service/request`:

```json
{
  "serviceID": "SVC_ENV_LIGHTING",
  "request": "__RoomSetBrightness",
  "requestArguments": {
    "BrightnessLevel": 100,
    "USE_LAST_DIMMER_VALUE": 1
  },
  "zone": "Living Room",
  "component": "Lights",
  "logicalComponent": "Lighting_controller",
  "variantID": "1",
  "alias": "Lighting",
  "requestId": "uuid-string"
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `serviceID` | Yes | Service type constant (e.g., `SVC_ENV_LIGHTING`) |
| `request` | Yes | Request name (e.g., `__RoomSetBrightness`) |
| `requestArguments` | Yes | HashMap of key-value parameters |
| `zone` | Optional | Zone/Room identifier |
| `component` | Optional | Component identifier |
| `logicalComponent` | Optional | Logical component name |
| `variantID` | Optional | Variant identifier |
| `alias` | Optional | Display alias |
| `requestId` | Auto | Auto-generated UUID for request correlation |

---

## Service Type Constants

| Constant | Value | Description |
|----------|-------|-------------|
| LIGHTING | `SVC_ENV_LIGHTING` | Lighting control |
| HVAC | `SVC_ENV_HVAC` | Dual-setpoint HVAC |
| HVAC_SINGLE | `SVC_ENV_SINGLE_SETPOINT_HVAC` | Single-setpoint HVAC |
| SHADE | `SVC_ENV_SHADE` | Window shades |
| FAN | `SVC_ENV_FAN` | Fan control |
| DOOR_LOCK | `SVC_ENV_DOORLOCK` | Door locks |
| GARAGE | `SVC_ENV_GARAGE` | Garage doors |
| GATE | `SVC_ENV_GATE` | Gates |
| SECURITY | `SVC_ENV_SECURITYSYSTEM` | Security system |
| POOL_SPA | `SVC_ENV_POOLANDSPA` | Pool & spa |
| ENERGY | `SVC_ENV_ENERGYMONITOR` | Energy monitoring |
| CAMERA | `SVC_ENV_SECURITYCAMERA` | Security cameras |
| ENTRY | `SVC_ENV_ENTRY` | Entry/doorbell |
| RELAY | `SVC_ENV_GENERALTRIGGERCONTROLLEDDEVICE` | Relay devices |
| EV_CHARGER | `SVC_ENV_EVCHARGER` | EV chargers |
| HOT_WATER | `SVC_ENV_HOTWATER` | Hot water |

**Source:** `com/savantsystems/core/data/service/ServiceTypes.java`

---

## DIS Protocol (Distributed Information System)

DIS handles higher-level operations: scenes, HVAC scheduling, energy management.

### DISRequest Message

Sent via URI `dis/{app}/request`:

```json
{
  "app": "dashboard",
  "request": "ApplyScene",
  "requestArguments": {
    "id": "UEFP-XCVD-YQRE",
    "version": "2.0"
  },
  "requestId": "uuid-string"
}
```

### DIS Applications

| App Name | Purpose |
|----------|---------|
| `dashboard` | Scene management |
| `hvacSchedule` | HVAC scheduling profiles |
| `energyMonitor` | Energy monitoring & control |

### DISResults Response

```json
{
  "results": { ... },
  "request": "ApplyScene",
  "requestId": "matching-uuid",
  "errorCode": 0,
  "errorMessage": "",
  "errorList": []
}
```

### DIS State Registration

Subscribe to DIS states via URI: `dis/{app}/register`

---

## Command Flow Pattern

1. Create request (`ServiceRequest` or `DISRequest`)
2. Set required parameters in `requestArguments` HashMap
3. Send via `Savant.control.sendMessage(request)`
4. Listen for response via event bus or state updates
5. Response includes `requestId` for correlation

---

## Related Documents

- [Environment Control](environment-control.md) — Lighting, HVAC, shades, fans, locks
- [Scene Management](scenes.md) — Scene CRUD via DIS
- [Energy & Security](energy-security.md) — Energy DIS commands, security
- [Media & AV](media-av.md) — Media service commands
