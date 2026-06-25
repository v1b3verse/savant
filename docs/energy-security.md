# Energy Monitoring, Pool/Spa, Security & Cameras

[< Back to Overview](../SAVANT.md) | [Service Control](service-control.md)

---

## Energy Monitoring

### State Keys

| State Key | Description |
|-----------|-------------|
| `Energy.Total.Consumption` | Total power consumption |
| `Energy.Total.Production` | Solar/generator production |
| `Energy.Total.Net` | Net power flow |
| `Energy.Grid.IsAvailable` | Grid connection status |
| `Energy.Mode.PowerFlow` | Power flow direction |
| `Energy.Battery.OperatingMode` | Battery mode |
| `Energy.Battery.ChargingSource` | Charge source |
| `Energy.Budget.LimitWatts` | Budget limit |
| `Energy.Budget.AvailableWatts` | Available budget |
| `Energy.Generator.Status` | Generator state |
| `Energy.Solar.isProducingEnergy` | Solar production active |
| `Energy.Mode.IsVCLPActivating` | Energy scene activating |
| `Energy.PDU.TogglesInFlight` | Pending load toggles |

### DIS Commands (via `energyMonitor` app)

| Command | Description |
|---------|-------------|
| `EnergyCommand` | Generic energy command |
| `setEnergyOnlyLoad` | Set critical load behavior |
| `modifyVCLP` | Modify energy scene |
| `SetEnergyMode` | Set on-grid/off-grid mode |
| `SetSelectedVCLP` | Set critical load scene |
| `getVCLPInfo` | Get scene information |
| `FetchEnergyTree` | Get full energy hierarchy |

### Energy Tree Structure

```json
{
  "appSettings": { "maxPowerScaleValue": 100000 },
  "microgridConfig": {
    "isGridTied": 1,
    "hasGenerator": 1,
    "hasSolar": 1,
    "hasBattery": 1,
    "modes": [0, 3, 4]
  },
  "Energy.Total.Net": {"Label": "Net Power", "IconName": "Grid"},
  "Energy.Total.Production": {"Label": "Total Production"},
  "Energy.Total.Consumption": {"Label": "Total Consumption"},
  "Energy.Group.Solar": {"Parent ID": "Energy.Total.Net", "Label": "Solar", "ProductionOnly": 1},
  "Energy.Circuit.Solar": {
    "uuid": "...",
    "Parent ID": "Energy.Group.Solar",
    "Classification": "Production",
    "Label": "Solar",
    "dlmPredefinedCircuitType": "solarInverter",
    "ProductionType": "Solar"
  }
}
```

**Source:** `controlapp/dev/energy/repository/EnergyRepository.java`

---

## Pool & Spa

### Entity Types

| Type | Value | Description |
|------|-------|-------------|
| AUX | 1 | Auxiliary equipment |
| ONE_TOUCH | 2 | One-touch control |
| DIMMER | 3 | Variable speed/brightness |
| JANDY_COLORS | 4 | Jandy color lights |
| JANDY_LED | 5 | Jandy LED |
| PENTAIR_SAM | 6 | Pentair SAm |
| PENTAIR_INTELLI_BRITE | 7 | Pentair IntelliBrite |
| HAYWARD_CL | 8 | Hayward ColorLogic |

### Key States

- `Pool Control.Pool_and_spa_controller.CurrentSpaHeaterMode` — On/Off
- `Pool Control.Pool_and_spa_controller.CurrentPumpMode` — Boolean
- Heater enable/disable, setpoints, pump speed, waterfall mode, cleaning system

### Event Types

Enable/disable heaters (pool, secondary, spa, solar), set temperature setpoints, pump mode/speed control, waterfall/spa mode, cleaning system, auxiliary controls.

**Source:** `controlapp/services/poolspa/`

---

## Security System

### Commands

Sent via URI: `events/security`

**Keypad commands:**
`NumberOne`, `NumberTwo`, ..., `NumberZero`, `NumberAsterix`, `NumberPound`

**Function commands:**
`KeypadPolice`, `KeypadFire`, `KeypadMedical`, `KeypadPanic`

**Arm/Disarm:**
`ArmAlarmAway`, `ArmAlarmStay`, `DisarmAlarm`

**Zone control:**
`BypassZone`, `UnBypassZone`

**Navigation:**
`CursorLeft`, `CursorRight`, `EndKeyPress`

### Security System States

Security system supports these partition states:
`Armed`, `ArmedAway`, `ArmedStay`, `ArmedVacation`, `ArmedNightStay`, `ArmedInstant`, `Disarmed`, `Alarmed`

### State Keys

- `Security System.Security_system.CurrentZoneStatus_{n}` — Ready/Critical/Trouble
- `User Security System.Security_system.CurrentUserNumber_{n}`
- `User Security System.Security_system.CurrentZoneStatus_{n}`
- `{Room}.SecurityStatus`

**Source:** `controlapp/services/requests/SecurityRequests.java`

---

## Cameras & Video

### Camera Commands

Sent via URI: `cameras/{component}-{logicalComponent}/{command}`

| Command | Description |
|---------|-------------|
| `startFetch` | Start camera stream |
| `stopFetch` | Stop camera stream |

### WebRTC Signaling

Sent via URI: `rtcSignaling/{command}`

Used for real-time camera streaming and P2P intercom (`dis/p2pIntercom/{path}`).

### Video Clip API

See [Cloud API — Video Endpoints](cloud-api.md#video-clips) for cloud-stored video clip management.

All paths relative to `com/savantsystems/` under the app package root
