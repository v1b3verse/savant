# State Management

[< Back to Overview](../SAVANT.md)

---

## Overview

Savant uses a **pub/sub model** for state management. The client subscribes to state names and receives real-time push updates whenever values change on the host.

---

## State Registration Flow

1. Client sends `StateRegister` via URI `state/register` with list of state names
2. Host sends initial `StateUpdate` with current values for all subscribed states
3. Host pushes `StateUpdate` on every subsequent change (real-time)
4. Client can `StateUnregister` (URI `state/unregister`) to stop updates
5. Client can `StateSet` (URI `state/set`) to write new values

---

## State Categories

The `StateManager` maintains separate subscription sets:

| Set | Contents |
|-----|----------|
| `mServiceStates` | Active services per room |
| `mVolumeStates` | Volume levels and mute |
| `mLightStates` | Lighting levels |
| `mShadeStates` | Shade positions |
| `mTemperatureStates` | HVAC readings |
| `mGarageStates` | Garage door status |
| `mGateStates` | Gate status |
| `mDoorlockStates` | Door lock status |
| `mSecurityStates` | Security system |
| `mEnergyStates` | Energy monitoring |
| `mGlobalStates` | System-wide states |
| `mUserSettingStates` | User settings |
| `mScenesStates` | Scene activation status |
| `mChannelFavoriteStates` | TV favorites |

---

## State Key Naming Convention

All state keys use **dot-separated hierarchical notation**. The general pattern is:

```
{Scope}.{Component}.{LogicalComponent}.{Variant}.{ServiceID}.{Property}
```

Not all levels are always present. The depth depends on the state category:

| Depth | Pattern | Example |
|-------|---------|---------|
| 1 | `global.{Property}` | `global.SystemHasStarted` |
| 2 | `{Room}.{Property}` | `Kitchen.RoomLightsAreOn` |
| 3 | `{Component}.{LogicalComponent}.{Property}` | `CD.CD_player.CurrentDiskNumber` |
| 4 | `{Zone}.HVAC_controller.{Property}` | `Main Floor.HVAC_controller.ThermostatCurrentSetPoint_1` |
| 5 | `{Room}.{Component}.{LogicalComponent}.{Variant}.{ServiceID}.{Property}` | `Living Room.Cable 1.Cable_box.1.SVC_AV_TV.ServiceIsActive` |

---

## State Name Patterns with Real Examples

> All examples below are from the bundled demo data (`demo-states.json`).
> Demo rooms: Living Room, Sitting Room, Kitchen, Dining Room, Master Bedroom, Master Bathroom, Entry, Patio

### Room-Level States

Per-room properties. Subscribe to `{Room}.{Property}`.

| State Key | Type | Example Value | Description |
|-----------|------|---------------|-------------|
| `{Room}.ActiveService` | string | `"Living Room-Cable 1-Cable_box-1-SVC_AV_TV"` | Currently active service (dash-separated ID) |
| `{Room}.ActiveServices` | string | `"Living Room-Dad's Apple TV-Media_server-1-SVC_AV_APPLEREMOTEMEDIASERVER"` | All active services |
| `{Room}.ActiveAudioService` | string | `"Kitchen-All Radio-Radio_2-1-SVC_AV_SATELLITERADIO"` | Active audio source |
| `{Room}.ActiveVideoService` | string | `""` | Active video source |
| `{Room}.LastActiveService` | string | `"Dining Room-SMS-Player_B-1-SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_PANDORA"` | Previous service |
| `{Room}.LastServiceUpdateTime` | string | `"1409591085"` | Unix timestamp of last service change |
| `{Room}.CurrentVolume` | int | `25` | Volume level (0-100) |
| `{Room}.IsMuted` | bool | `false` | Mute state |
| `{Room}.RelativeVolumeOnly` | int | `0` | 1=only relative volume control |
| `{Room}.RoomLightsAreOn` | bool | `true` | Any lights on in room |
| `{Room}.ZoneHasVideo` | int | `1` | 1=room has active video |
| `{Room}.ZoneHasAudio` | int | `1` | 1=room has active audio |
| `{Room}.ZoneIsActive` | int | `1` | 1=room has any active service |
| `{Room}.SecurityStatus` | string | `"0"` or `"1"` | Security zone status |
| `{Room}.ContentProtectionIssues` | int | `0` | HDCP issues count |
| `{Room}.MismatchedModules` | int | `0` | Module mismatch count |
| `{Room}.AllUIServersFound` | int | `1` | All UI servers online |
| `{Room}.SleepTimerEnabled` | int | `1` | Sleep timer available |
| `{Room}.SleepTimerActive` | int | `0` | Sleep timer running |
| `{Room}.SleepTimerRemainingTime` | string | `""` | Remaining time |

**Room status indicators** (per room):

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `{Room}.ControlStatusIsGreen` | bool | `false` | All OK |
| `{Room}.ControlStatusIsYellow` | bool | `false` | Warnings |
| `{Room}.ControlStatusIsRed` | bool | `true` | Errors |
| `{Room}.ControlStatusIsGrey` | bool | `false` | Unknown |
| `{Room}.ControlStatusLight` | int | `2` | 0=grey, 1=green, 2=yellow, 3=red |
| `{Room}.ControlStatus` | string | `"Cannot communicate with components."` | Human-readable |
| `{Room}.SystemStatusIsGreen` | bool | `false` | |
| `{Room}.SystemStatusIsYellow` | bool | `false` | |
| `{Room}.SystemStatusIsRed` | bool | `true` | |
| `{Room}.SystemStatusLight` | int | `2` | |
| `{Room}.SystemStatus` | string | `"Chassis are reporting errors."` | |
| `{Room}.ControllerStatusIsGreen` | bool | `false` | |
| `{Room}.ControllerStatusIsYellow` | bool | `false` | |
| `{Room}.ControllerStatusIsRed` | bool | `true` | |
| `{Room}.ControllerStatusLight` | int | `2` | |
| `{Room}.ControllerStatus` | string | `"Chassis are reporting errors."` | |
| `{Room}.ConfigurationStatusIsGreen` | bool | `true` | |
| `{Room}.ConfigurationStatusIsYellow` | bool | `false` | |
| `{Room}.ConfigurationStatusIsRed` | bool | `false` | |
| `{Room}.ConfigurationStatusIsGrey` | bool | `false` | |
| `{Room}.ConfigurationStatusLight` | int | `0` | |
| `{Room}.ConfigurationStatus` | string | `""` | |

---

### Service-Level States

Every service instance has 3 standard states. The key pattern is:

```
{Room}.{Component}.{LogicalComponent}.{Variant}.{ServiceID}.{Property}
```

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `ServiceIsActive` | int | `0` or `1` | Whether this service is currently active |
| `ServiceState` | string | `"active"`, `"inactive"` | Service state string |
| `ZonesActiveIn` | string | `"Living Room"`, `""` | Comma-separated room list |

**Real examples from demo:**

```
Living Room.Cable 1.Cable_box.1.SVC_AV_TV.ServiceIsActive = 1
Living Room.Cable 1.Cable_box.1.SVC_AV_TV.ServiceState = "active"
Cable 1.Cable_box.1.SVC_AV_TV.ZonesActiveIn = "Living Room"

Living Room.Front Door.Security_camera.1.SVC_ENV_SECURITYCAMERA.ServiceIsActive = 0
Entry.Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ServiceIsActive = 0
Entry.Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ServiceState = "inactive"
Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ZonesActiveIn = ""

Dining Room.Pool Control.Pool_and_spa_controller.1.SVC_ENV_POOLANDSPA.ServiceIsActive = 0
Entry.Entry Room.HVAC_controller.1.SVC_ENV_SINGLE_SETPOINT_HVAC.ServiceIsActive = 0
Living Room.Shades.Lighting_controller.1.SVC_ENV_SHADE.ServiceIsActive = 0
```

Note: `ZonesActiveIn` is often at the component level without room prefix:
```
Cable 1.Cable_box.1.SVC_AV_TV.ZonesActiveIn = "Living Room"
Shades.Lighting_controller.1.SVC_ENV_SHADE.ZonesActiveIn = ""
User Security System.Security_system.1.SVC_ENV_USERLOGIN_SECURITYSYSTEM.ZonesActiveIn = ""
```

**Active service ID format** (used in `ActiveService`, `ActiveAudioService` etc.):
```
{Room}-{Component}-{LogicalComponent}-{Variant}-{ServiceID}
```
Example: `"Living Room-Cable 1-Cable_box-1-SVC_AV_TV"` (dashes, not dots)

---

### HVAC / Climate States

Pattern: `{Zone}.HVAC_controller.{Property}` where Zone = HVAC zone name (e.g., "Main Floor", "Second Floor", "Basement", "Entry Room").

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `{Zone}.HVAC_controller.ThermostatCurrentSetPoint_1` | string | `"88"` | Current setpoint (°F) |
| `{Zone}.HVAC_controller.ThermostatCurrentSchedule_1` | string | `"Spring"` | Active schedule name |
| `{Zone}.HVAC_controller.ThermostatCurrentHumidity_1` | string | `"57.5"` | Current humidity % |
| `{Zone}.HVAC_controller.ThermostatCurrentHumidifyPoint` | string | `"57"` | Humidify setpoint |
| `{Zone}.HVAC_controller.ThermostatCurrentHumiditySetPoint_1` | string | `"65"` | Humidity setpoint |
| `{Zone}.HVAC_controller.ThermostatCurrentDehumidifyPoint` | string | `"38"` | Dehumidify setpoint |
| `{Zone}.HVAC_controller.ThermostatCurrentDehumidifyPoint_1` | string | `"36.0"` | Dehumidify setpoint (alt) |
| `{Zone}.HVAC_controller.ThermostatCurrentHumidifyPoint_1` | string | `"57"` | Humidify setpoint (alt) |
| `{Zone}.HVAC_controller.ThermostatTempGraphHistory_1` | string | `"0"` | Temp history data |
| `{Zone}.HVAC_controller.ThermostatHoldUntil_1` | string | `"None"` | Hold expiry |
| `{Zone}.HVAC_controller.IsThermostatHolding_1` | bool | `false` | Hold active |
| `{Zone}.HVAC_controller.IsCurrentHVACModeAuto_1` | bool | `true` | Auto mode |
| `{Zone}.HVAC_controller.IsCurrentHVACModeCool` | bool | `false` | Cooling mode |
| `{Zone}.HVAC_controller.IsCurrentHVACModeCool_1` | bool | `false` | Cooling mode (alt) |
| `{Zone}.HVAC_controller.IsCurrentHVACModeOff` | bool | `false` | System off |
| `{Zone}.HVAC_controller.IsCurrentHVACModeOff_1` | bool | `false` | System off (alt) |
| `{Zone}.HVAC_controller.IsThermostatCurrentFanModeOn` | bool | `false` | Fan running |
| `{Zone}.HVAC_controller.IsThermostatCurrentFanModeOn_1` | bool | `false` | Fan running (alt) |
| `{Zone}.HVAC_controller.IsThermostatCurrentFanModeAuto` | bool | `true` | Fan auto mode |
| `{Zone}.HVAC_controller.IsThermostatCurrentFanModeAuto_1` | bool | `true` | Fan auto mode (alt) |
| `{Zone}.HVAC_controller.IsThermostatHumidityModeOn` | bool | `false` | Humidity control active |
| `{Zone}.HVAC_controller.IsThermostatHumidityModeOn_1` | bool | `true` | Humidity control (alt) |
| `{Zone}.HVAC_controller.IsW1RelayEnergized` | bool | `false` | Heating stage 1 relay |
| `{Zone}.HVAC_controller.IsW1RelayEnergized_1` | bool | `false` | Heating stage 1 (alt) |
| `{Zone}.HVAC_controller.IsW2RelayEnergized` | bool | `false` | Heating stage 2 relay |
| `{Zone}.HVAC_controller.IsW2RelayEnergized_1` | bool | `false` | Heating stage 2 (alt) |
| `{Zone}.HVAC_controller.IsW3RelayEnergized_1` | bool | `false` | Heating stage 3 relay |
| `{Zone}.HVAC_controller.IsY1RelayEnergized` | bool | `false` | Cooling stage 1 relay |
| `{Zone}.HVAC_controller.IsY1RelayEnergized_1` | bool | `false` | Cooling stage 1 (alt) |
| `{Zone}.HVAC_controller.IsY2RelayEnergized_1` | bool | `false` | Cooling stage 2 relay |

Note: Suffix `_1` typically indicates dual-setpoint thermostat zone index. Some multi-zone systems use ` 2` suffix (with a space): `IsCurrentHVACModeHeat_5 2`.

---

### Lighting States

Pattern: `Lights.Lighting_controller.{Property}` (global component, not per-room).

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `Lights.Lighting_controller.DimmerLevel_{addr}` | int | `0`-`100` | Dimmer level for address |
| `Lights.Lighting_controller.IsLED1On_{addr}` | int | `0` | LED indicator 1 state |
| `Lights.Lighting_controller.IsLED2On_{addr}` | int | `0` | LED indicator 2 state |
| `Lights.Lighting_controller.IsLED3On_{addr}` | int | `0` | LED indicator 3 state |
| `Lights.Lighting_controller.IsLED4On_{addr}` | int | `0` | LED indicator 4 state |

**Address format** for `{addr}`: `{bus}_{address}` e.g., `1_7`, `1_8`, `2_26`, `2_32`, `2_1_2_0` (extended addressing for scene dimmer targets like `DimmerLevel_2_1_2_0 = 30`).

Lighting service state per room:
```
Living Room.Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ServiceIsActive = 0
Living Room.Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ServiceState = "inactive"
Lights.Lighting_controller.1.SVC_ENV_LIGHTING.ZonesActiveIn = ""
```

---

### Shade States

Shades reuse the `Lighting_controller` component with service ID `SVC_ENV_SHADE`:

```
Living Room.Shades.Lighting_controller.1.SVC_ENV_SHADE.ServiceIsActive = 0
Living Room.Shades.Lighting_controller.1.SVC_ENV_SHADE.ServiceState = "inactive"
Shades.Lighting_controller.1.SVC_ENV_SHADE.ZonesActiveIn = ""
```

---

### Media / AV Device States

Device-level states (no room prefix):

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `{Component}.{LogicalComponent}.CurrentPowerStatus` | string | `"OFF"` | Power state |
| `{Component}.{LogicalComponent}.CurrentMuteStatus` | string | `"OFF"` | Mute state |
| `{Component}.{LogicalComponent}.CurrentVolume` | string | `"0"` | Volume level |
| `{Component}.{LogicalComponent}.IsPowered` | int | `0` | Power as int |
| `{Component}.{LogicalComponent}.IsMuted` | int | `0` | Mute as int |
| `{Component}.{LogicalComponent}.Host` | string | `"42.0.0.15:45505"` | Network address |
| `{Component}.{LogicalComponent}.CurrentStation` | string | `"410"` | TV channel |

**Real examples:**
```
DirecTV 1.Satellite_tv_tuner.CurrentPowerStatus = "OFF"
DirecTV 3.Satellite_tv_tuner.IsPowered = 0
Cable 1.Cable_box.CurrentStation = "410"
Cable 2.Cable_box.CurrentMuteStatus = "OFF"
Living Room Display.HD_monitor.CurrentMuteStatus = "OFF"
Living Room Display.HD_monitor.CurrentVolume = "0"
Living Room Display.HD_monitor.IsMuted = 0
Sitting Room Display.HD_monitor.CurrentPowerStatus = "OFF"
Sitting Room Display.HD_monitor.IsPowered = 0
AppleTV.Media_server.Host = "42.0.0.15:45505"
Kaleidescape.Media_server.Host = " "
```

**Playback states** (media players):
```
AppleTV.Media_server.CurrentElapsedTime = "01:20"
AppleTV.Media_server.CurrentElapsedHour = ""
AppleTV.Media_server.CurrentElapsedMinute = ""
AppleTV.Media_server.CurrentElapsedSecond = ""
AppleTV.Media_server.CurrentRemainingTime = "-02:07"
AppleTV.Media_server.CurrentTimeRemainingHour = ""
AppleTV.Media_server.CurrentTimeRemainingSecond = ""
AppleTV.Media_server.CurrentPauseStatus = 0
AppleTV.Media_server.CurrentShuffleStatus = 0
AppleTV.Media_server.ErrorMessage = ""

Shared Bluray.EnhancedDVD_player.CurrentChapter = "15"
Shared Bluray.EnhancedDVD_player.CurrentTitle = ""
Shared Bluray.EnhancedDVD_player.CurrentDiskText = "Raiders of the Lost Ark"
Shared Bluray.EnhancedDVD_player.CurrentElapsedHour = "01"
Shared Bluray.EnhancedDVD_player.CurrentElapsedMinute = "03"

CD.CD_player.CurrentDiskNumber = "1"
CD.CD_player.CurrentElapsedMinute = "02"
```

**Radio states:**
```
All Radio.Radio.CurrentTunerFrequency = 107.1
All Radio.Radio_2.CurrentSatelliteChannelName = "Alt Nation"
All Radio.Radio_2.CurrentSatelliteCategoryName = "Rock"
Duo Tuner.Radio_2.CurrentSatelliteChannelNumber = "16"
Duo Tuner.Radio_2.CurrentSatelliteChannelName = "Deep Tracks"
Duo Tuner.Radio_2.CurrentSatelliteSongTitle = "Blowin' in the Wind"
```

**Savant Music (streaming/LMQ):**
```
Savant Music.Player_A.CurrentSongName = "Someone Like You"
Savant Music.Player_A.CurrentArtistName = "Adele"
Savant Music.Player_A.CurrentArtworkPath = "sonos_demo_artwork"
Savant Music.Player_A.CurrentRemainingTime = "03:23"
```

---

### Video Processing States

Pattern: `{OSD System}.{Zone}.{Property}`

```
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentVideoInputFormat = "1080i"
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentVideoOutputFormat = "1080p"
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentHue = 0
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentSaturation = 0
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentNoiseReduction = 0
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentDetailEnhancementLevel = 0
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentDetailEnhancementThreshold = 0
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentAspectRatioIsZoom = false
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentAspectRatioIsAnamorphic = false
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentAspectRatioIsVerticalStretch = false
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentAspectRatioIsPillarBox = false
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentAspectRatioIsPanoramicStretch = false
Savant ROSIE OSD Control System.Video Audio Zone 1.CurrentContrast = 0
```

---

### Security System States

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `Security System.Security_system.CurrentPartitionStatus_{n}` | string | `"Alarm Critical"` | Partition alarm status |
| `Security System.Security_system.CurrentPartitionArmingStatus_{n}` | string | `"Disarmed"`, `"ArmedStay"`, `"ArmedAway"` | Arming state |
| `Security System.Security_system.CurrentZoneStatus_{n}` | string | `"Ready"`, `"Critical"`, `"Trouble"` | Zone status |
| `Security System.Security_system.ZoneSummary_{n}` | string | `"0"`, `"1"`, `"2"` | Zone summary count |
| `Security System.Security_system.CurrentLCDContentsLine1_{n}` | string | `"Issues detected in:"` | Panel LCD line 1 |
| `Security System.Security_system.CurrentLCDContentsLine2_{n}` | string | `"Living Room, Entry"` | Panel LCD line 2 |
| `Security System.Security_system.CurrentUserNumber_{n}` | string | `"1"` | User number |

**User Security System** (per-user login variant):
```
User Security System.Security_system.CurrentPartitionArmingStatus_1 = "Disarmed"
User Security System.Security_system.CurrentPartitionArmingStatus_2 = "ArmedAway"
User Security System.Security_system.CurrentUserAccessCode_1 = "123"
User Security System.Security_system.CurrentUserAccessCode_2 = "456"
User Security System.Security_system.CurrentZoneStatus_1 = "Ready"
```

---

### Pool & Spa States

Pattern: `Pool Control.Pool_and_spa_controller.{Property}`

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `Pool Control.Pool_and_spa_controller.CurrentSpaTemperature` | string | `"105"` | Spa temp (°F) |
| `Pool Control.Pool_and_spa_controller.CurrentSpaHeaterMode` | string | `"On"` | Spa heater |
| `Pool Control.Pool_and_spa_controller.CurrentPoolHeaterSetpoint` | string | `"70"` | Pool temp setpoint |
| `Pool Control.Pool_and_spa_controller.CurrentPumpMode` | bool | `false` | Pump running |
| `Pool Control.Pool_and_spa_controller.IsWaterfallModeOn` | bool | `false` | Waterfall feature |
| `Pool Control.Pool_and_spa_controller.IsAuxiliary{1-16}On` | bool | `true`/`false` | Aux relay states |

---

### Surveillance States

```
Surveillance System.Surveillance_controller.PTZState = 0
Surveillance System.Surveillance_controller.1.SVC_AV_SURVEILLANCESYSTEM.ZonesActiveIn = ""
```

---

### Global States

Pattern: `global.{Property}` — system-wide, not room-specific.

| State Key | Type | Example | Description |
|-----------|------|---------|-------------|
| `global.SystemHasStarted` | int | `1` | Host has booted |
| `global.SystemIsReady` | bool | `true` | System fully ready |
| `global.AllProcessesStarted` | int | `1` | All processes running |
| `global.AllChassisActive` | int | `0` | All chassis online |
| `global.AllUIServersFound` | int | `1` | All UI servers found |
| `global.ActiveZones` | string | `"Sitting Room,Dining Room,Kitchen,Living Room"` | Comma-separated active rooms |
| `global.CurrentDay` | string | `"Monday"` | Day of week |
| `global.IsWeekday` | int | `1` | |
| `global.IsWeekend` | int | `0` | |
| `global.TimeZone` | string | `"America/New_York"` | IANA timezone |
| `global.Dawn` | string | `"invalid"` or datetime | Dawn time |
| `global.Dusk` | string | `"2014-09-01 10:48:00 -0400"` | Dusk time |
| `global.Sunrise` | string | `"2014-09-01 00:39:00 -0400"` | Sunrise time |
| `global.Sunset` | string | `"2014-09-01 09:47:00 -0400"` | Sunset time |
| `global.EventHistoryEnabled` | bool | `true` | Event logging |
| `global.SystemStatusIsYellow` | bool | `false` | |
| `global.SystemStatusIsGrey` | bool | `false` | |
| `global.SystemStatusLight` | int | `2` | 0=grey, 1=green, 2=yellow, 3=red |
| `global.ControlStatusIsRed` | bool | `true` | |
| `global.ControlStatusIsGrey` | bool | `false` | |
| `global.ControlStatusLight` | int | `2` | |
| `global.ControllerStatusIsGreen` | bool | `false` | |
| `global.ControllerStatusIsGrey` | bool | `false` | |
| `global.ControllerStatusIsRed` | bool | `true` | |
| `global.ControllerStatus` | string | `"Chassis are reporting errors in zones: Sitting Room, Patio, ..."` | |
| `global.ConfigurationStatus` | string | `""` | |
| `global.ConfigurationStatusIsGreen` | bool | `true` | |
| `global.ConfigurationStatusIsGrey` | bool | `false` | |
| `global.ConfigurationStatusIsRed` | bool | `false` | |
| `global.DiagnosticReportStatus` | string | `"Diagnostic reports have been logged."` | |
| `global.DiagnosticReportStatusLight` | int | `1` | |
| `global.DiagnosticReportStatusIsGreen` | bool | `false` | |
| `global.DiagnosticReportStatusIsYellow` | bool | `true` | |
| `global.DiagnosticReportStatusIsGrey` | bool | `false` | |
| `global.{Component}.ControlIsConnected` | int | `1` | Per-component connectivity |

---

### DIS / App Location States

Internal state tracking for DIS app endpoints:

```
disAppLocation.dashboard = "42.0.0.15:34189"
disAppLocation.hvacSchedule = "42.0.0.15:34623"
disAppLocation.hvacMonitor = "42.0.0.15:35947"
disAppLocation.equalizer = "42.0.0.15:37471"
disAppLocation.userData = "42.0.0.15:41414"
disAppLocation.sleepTimer = "42.0.0.15:55195"
hvacSchedule.MatchRequests.HumiditySingle = 1
```

---

### Device Identity States

Pattern: `{DeviceUID}.{Property}` — identifies connected control devices.

```
e24e1cc759f5fda5.DeviceModel = "Nexus 7"
e24e1cc759f5fda5.DeviceType = "Android"
e24e1cc759f5fda5.SoftwareVersion = "Android 4.4.4"
e24e1cc759f5fda5.AppVersion = "Control (7.0 sprint8)"
e24e1cc759f5fda5.Name = "Android Control App"
428E4143-EBA2-4E47-925B-EA4335B5012A.DeviceModel = "iPad Simulator"
428E4143-EBA2-4E47-925B-EA4335B5012A.DeviceMake = "Apple"
428E4143-EBA2-4E47-925B-EA4335B5012A.interfaceBecameActive = "2014-09-01 13:05:25 -0400"
```

---

### Miscellaneous States

```
.MetadataArtworkServerIP = "42.0.0.15:8080"
Patio Door Status.Device.IsOn = "1"
[ROSIE - Resources].ActiveService = ""
disApp.equalizer.RootMenuTimeStamp = "2014-09-01 13:00:05 -0400"
disApp.equalizer.Host = "42.0.0.15:60531"
Kaleidescape.RootMenuTimeStamp = "2014-09-01 12:59:13 -0400"

System 12 (A).Status = 2
System 12 (A).MainBoard.Status = 2
System 12 (A).SwitchBoard.Status = 2
System 12 (A).Audio Output Slot 1.Status = 2
System 12 (A).Audio Input Slot 2.Status = 2
System 12 (A).Video Input Slot 2.Status = 2
```

---

## Value Type Summary

| Type | JSON representation | Notes |
|------|-------------------|-------|
| bool | `true` / `false` | Used for mode flags, status indicators |
| int | `0`, `1`, `2`, `25` | 0/1 for boolean-like, larger for levels |
| float | `107.09999999999999` | Radio frequencies |
| string | `"inactive"`, `"105"`, `""` | Note: numeric values are often strings! |
| datetime string | `"2014-09-01 10:48:00 -0400"` | Format: `yyyy-MM-dd HH:mm:ss Z` |
| unix timestamp string | `"1409591085"` | Seconds since epoch (as string) |

**Important**: Types are inconsistent across states. The same logical concept may be `bool` in one state and `int` (0/1) in another. Numeric values like temperatures and setpoints are typically strings, not numbers. Always handle both.

---

## Demo Home Layout

The demo data defines these rooms/zones and components:

**Rooms:** Living Room, Sitting Room, Kitchen, Dining Room, Master Bedroom, Master Bathroom, Entry, Patio, Equipment Rack, [ROSIE - Resources]

**HVAC Zones:** Main Floor, Second Floor, Basement, Entry Room

**Components:**
- Lighting: `Lights` / `Lighting_controller`
- Shades: `Shades` / `Lighting_controller` (same controller!)
- HVAC: `{Zone}` / `HVAC_controller`
- AV: `Cable 1`/`Cable_box`, `DirecTV 1-3`/`Satellite_tv_tuner`, `AppleTV`/`Media_server`, `Kaleidescape`/`Media_server`, `Shared Bluray`/`EnhancedDVD_player`, `CD`/`CD_player`, `Vudu`/`Media_server`
- Radio: `All Radio`/`Radio` (FM), `All Radio`/`Radio_2` (Satellite), `Duo Tuner`/`Radio_2`
- Music: `Savant Music`/`Player_A` (Savant Media Server / Sonos)
- Security: `Security System`/`Security_system`, `User Security System`/`Security_system`
- Cameras: `Front Door`/`Security_camera`, `Office`/`Security_camera`, `Local Office`/`Security_camera`, `Kids Room`/`Security_camera`
- Surveillance: `Surveillance System`/`Surveillance_controller`
- Pool: `Pool Control`/`Pool_and_spa_controller`
- Displays: `Living Room Display`/`HD_monitor`, `Sitting Room Display`/`HD_monitor`, `Master Bedroom Display`/`HD_monitor`
- Video Processing: `Savant ROSIE OSD Control System`/`Video Audio Zone 1` (multiple instances: System, System 1, System 2)
- Audio: `System 12 (A)`, `System 12 (B)` — audio matrix

---

## Source

`com/savantsystems/core/state/StateManager.java`

Demo data: `assets/demo-states.json` (bundled in APK)
