# WebSocket Protocol

[< Back to Overview](../SAVANT.md)

---

## Connection Establishment

```
Client                                   Host
  |                                        |
  |--- WebSocket Connect (wss://:5000) --->|
  |                                        |
  |--- DevicePresent ------------------->  |
  |    {UID, hostUID, homeID, make,        |
  |     model, type:"Android", OS,         |
  |     version, configurationID,          |
  |     cloudToken, messageFormat}         |
  |                                        |
  |<-- DeviceResponse -------------------- |
  |    {hostUID, homeID, session info}     |
  |                                        |
  |--- AuthRequest (if needed) ----------> |
  |    {user, password/pinCode,            |
  |     hostToken}                         |
  |                                        |
  |<-- AuthResponse ---------------------- |
  |    {hostToken, hostSecretKey}          |
  |                                        |
  |--- StateRegister -------------------> |
  |    (subscribe to state changes)        |
  |                                        |
  |<== StateUpdate (push) ================ |
  |<== StateUpdate (push) ================ |
  |                                        |
```

### DevicePresent Fields

| Field | Description |
|-------|-------------|
| `UID` | Device unique identifier |
| `hostUID` | Target host UID |
| `homeID` | Home identifier |
| `make`, `model`, `modelNum` | Device hardware info |
| `serialNum`, `partNum` | Device identifiers |
| `type` | `"Android"` |
| `OS`, `name`, `clazz` | Device class |
| `version`, `app`, `versionName` | App version info |
| `configurationID` | GUID for configuration |
| `messageFormat` | Protocol version |
| `cloudToken` | User cloud auth token |

---

## Session States

| State | Meaning |
|-------|---------|
| 0 | Closed |
| 1 | Connected (waiting for DeviceResponse) |
| 2 | Authentication required |
| 3 | Fully established / authenticated |

---

## Timeouts & Keep-alive

| Parameter | Value |
|-----------|-------|
| Connection timeout | 30s |
| Read timeout | 30s |
| Write timeout | 30s |
| Session handshake timeout | 6000ms |
| Ping interval | ~1s |
| Ping payload | `"SavantPing"` + counter |

---

## Sub-Protocol

Custom WebSocket sub-protocol name: **`rpm-protocol`**

Uses OkHttp3 WebSocket with:
- MODERN_TLS connection spec only
- Self-signed certificates accepted for local connections
- Binary (MessagePack) or text (JSON) frames

---

## Message Format

### MessageWrapper

Every WebSocket message is wrapped in:

```json
{
  "URI": "service/request",
  "messages": [ { ...message_payload... } ]
}
```

Serialized as **MessagePack** (binary) for efficiency. GZIP compression supported (detected by `0x1F 0x8B` header bytes). Binary messages detected by `0x8X` first byte pattern.

**Source:** `com/savantsystems/core/msgpack/ObjectPack.java`

---

## URI Routing Table

| URI Pattern | Purpose |
|-------------|---------|
| `session/{action}` | Session lifecycle (devicePresent, authenticationRequest, fileDownload) |
| `service/request` | Service commands (lighting, HVAC, shades, etc.) |
| `component/{componentId}/{request}` | Component-specific operations |
| `state/register` | Subscribe to state changes |
| `state/unregister` | Unsubscribe from state changes |
| `state/set` | Set state values |
| `dis/{app}/{action}` | DIS protocol (scenes, schedules, energy) |
| `dis/{app}/register` | DIS state registration |
| `mci/{identifier}/{action}` | MCI protocol requests |
| `media/{component}/{command}` | Media/AV control |
| `music/{comp}/{logicalComp}/{serviceId}/{query}` | Music service queries |
| `events/security` | Security system events |
| `events/{uri}` | Generic events |
| `cameras/{comp}-{logicalComp}/{command}` | Camera operations (startFetch, stopFetch) |
| `rtcSignaling/{command}` | WebRTC signaling |
| `dis/p2pIntercom/{path}` | P2P intercom |
| `osd/{displayId}/{action}` | On-screen display control |
| `device/version/{command}` | Version/device info |
| `status/{type}` | Status queries |
| `users` | User management |
| `analytics/{action}` | Analytics events |
| `diagnostics/{action}` | Diagnostic logging |
| `dcm/request` | Dynamic Color Manager |

### URI Builder Methods

```java
sessionURI(action)             -> "session/{action}"
serviceURI(action)             -> "service/{action}"
componentURI(id, request)      -> "component/{id}/{request}"
stateURI(action)               -> "state/{action}"
disURI(identifier, action)     -> "dis/{identifier}/{action}"
mciURI(identifier, action)     -> "mci/{identifier}/{action}"
mediaURI(component, command)   -> "media/{component}/{command}"
musicURI(c, lc, svc, query)   -> "music/{c}/{lc}/{svc}/{query}"
securityURI()                  -> "events/security"
statusURI(type)                -> "status/{type}"
osdURI(component, action)      -> "osd/{component}/{action}"
cameraURI(comp, lcomp, cmd)    -> "cameras/{comp}-{lcomp}/{cmd}"
versionURI(command)            -> "device/version/{command}"
eventURI(uri)                  -> "events/{uri}"
userURI()                      -> "users"
analyticURI(action)            -> "analytics/{action}"
diagURI(action)                -> "diagnostics/{action}"
webRTCURI(command)             -> "rtcSignaling/{command}"
```

---

## Response Routing

Responses are dispatched by URI prefix:

| URI | Response Class |
|-----|---------------|
| `session/deviceRecognized` | `DeviceResponse` |
| `session/authenticationResponse` | `AuthResponse` |
| `state/*` | `StateUpdate` |
| `media/*` | `MediaResult` |
| `component/*` | `ComponentResult` |
| `service/*` | `ServiceResult` |
| `dis/*` | `DISResults` |
| `device/version/*` | `VersionResponse` |
| `users` | `UsersResponse` |

---

## Key Source Files

| File | Purpose |
|------|---------|
| `core/connection/SavantConnection.java` | Connection manager, message routing |
| `core/connection/SavantMessages.java` | Message classes, URI builders |
| `core/connection/SavantWebSocket.java` | WebSocket transport |
| `core/connection/SavantTransport.java` | Abstract transport (MessagePack) |
| `core/connection/ws/WebSocketClient.java` | Low-level WebSocket client |
| `core/msgpack/ObjectPack.java` | MessagePack encode/decode |

All paths relative to `com/savantsystems/` under the app package root
