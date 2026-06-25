# House Configuration Discovery Mechanism

> How the Savant Android app discovers rooms, lights, services, and other devices.
> Based on analysis of the Savant Control App Pro v11.1.4 protocol.

[< Back to Overview](../SAVANT.md)

---

## TL;DR — Two-Phase Data Model

The Savant app uses **two separate data models** that work together:

| Model | Source | Format | What it contains |
|-------|--------|--------|------------------|
| **Configuration Data** | `uiconfig.tar.gz` (WebSocket file download) | SQLite (`serviceImplementation.sqlite`) | Rooms, services, entity definitions, commands, UI layout |
| **Runtime State Data** | `state/register` → `StateUpdate` (WebSocket push) | MessagePack via WebSocket | Current values: dimmer levels, on/off, temperatures, etc. |

**Key insight:** The house structure (which rooms exist, what devices are in them, what commands they support) comes from an **SQLite database** that is downloaded from the host as a compressed archive over the WebSocket. Runtime values are then subscribed separately via state registration.

---

## Alternative Path: Cloud REST API (No WebSocket Needed)

The house configuration can also be obtained through the **Savant Cloud REST API** without needing to establish a WebSocket connection. This is the simplest path for integration.

### Step 1: Cloud Login

```
POST https://api.savantcs.com/edge/api/users/login
Headers:
  SCS-Agent: FoWT9Z40axK88bO95EbNVfDILm34ff
  SCS-Channel: cedia
  Content-Type: application/json
  (No SCS-Authorization for login!)

Body:
  {"email": "user@example.com", "password": "...", "type": 0, "clientId": "..."}
```

Response includes:
- `token` — Auth token for subsequent requests
- `secretKey` — HMAC secret for building SCS-Authorization header

**Important:** The `type` field is an **integer** (0 = REGULAR_USER, 1 = LITE_INSTALLER), NOT a string.

### Step 2: Build Auth Header (for subsequent requests)

```python
# JWT-style claim JSON, NOT the request payload
claim = json.dumps({
    "alg": "SHA256",
    "iat": int(time.time() * 1000),  # current time in milliseconds
    "iss": "SCS",
    "sub": token,                     # the auth token from login
    "typ": "user",
}, separators=(",", ":"))

b64 = base64.b64encode(claim.encode()).decode()  # Base64.NO_WRAP
hmac_sig = hmac.new(secret.encode(), claim.encode(), hashlib.sha256).hexdigest()

headers = {
    "SCS-Authorization": f"{b64}:{hmac_sig}",
    "SCS-Agent": API_KEY,
    "SCS-Channel": "cedia",
    "Content-Type": "application/json",
}
```

**Source:** `SavantRestUtils.java` (constructMessage, getAuthHeaders)

### Step 3: Get Homes

```
GET https://api.savantcs.com/edge/api/users/{userId}/homes
```

Returns list of `SavantHome` objects with:
- `id` — Home ID
- `uid` — Host UID (e.g., `XXXXXXXXXXXX`)
- `cellUrl` — Remote WebSocket relay URL (e.g., `wss://cprd1e05-app.savantcs.com`)
- `hostName` — Local hostname (empty for cloud-only hosts)
- Various metadata (name, address, timezone, software version, licenses, permissions, etc.)

### Step 4a: Get Full Configuration (JSON)

```
GET https://api.savantcs.com/edge/api/homes/{homeId}/config
```

Returns **full house configuration as JSON** with:
- `rooms[]` — Array of rooms with `name`, `id`, `capabilities` (has lights, shades, HVAC, security, fans, etc.), `climate[]` for HVAC-linked rooms
- `services[]` — Array of services (may be empty in newer format)
- `zones[]` — Zone definitions
- `security[]` — Security system partitions
- `cameras[]` — Camera configurations

**This is the simplest way to get house configuration!**

### Step 4b: Get Active Config Archive (S3 Download)

```
GET https://api.savantcs.com/edge/api/homes/{homeId}/config/active
```

Returns a signed S3 URL pointing to the full `.rpmConfig.tar.gz` archive containing:
- `serviceImplementation.sqlite` — **Full SQLite database** (all rooms, services, entities, commands)
- `zoneInfo.plist` — Zone configuration
- `uimanifest.json` — UI layout definitions
- `serviceImplementation.xml` — Full service implementation XML
- `componentDataInfo.plist` — Component data
- `dataTableInfo.plist` — Data tables
- `KNXSettings.plist` — KNX-specific settings
- `edm.sqlite` — EDM database
- Mac `.action` bundles, workflow files, images, etc.

### Verified Data (from a production Smart 10 host running v11.2.0):

- **SQLite database version**: 53 ("Adds ServiceOptions table")
- **Tables**: 36 tables covering Rooms, LightEntities (144 lights), HVACEntities (10), ShadeEntities (18), FanEntities (4), SecuritySystemEntities (29), GarageEntities (1), and more
- **Rooms**: 29 rooms (Kitchen, Living, Office, Bedrooms, Terrace, Garage, etc.)
- **Components**: KNX (lighting/HVAC), Somfy RS485 (shades), Paradox EVO (security), CoolMasterNet (HVAC), example-host (generic)
- **State key pattern**: `KNX.Lighting_controller.DimmerLevel_141` — derived from the `stateName` column in LightEntities

---

## Direct Local Connection (No Cloud Needed)

The house configuration can also be obtained **directly from the local Savant server** without any cloud connection. The same WebSocket protocol works locally, and the server serves the identical `uiconfig.tar.gz`.

### Connection Details

| Parameter | Value |
|-----------|-------|
| Host | Local IP (e.g., `203.0.113.1`) |
| Port | **9108** |
| Protocol | WSS with self-signed cert |
| Sub-Protocol | `rpm-protocol` |

### Full Local Handshake

```python
import asyncio, aiohttp, ssl, msgpack, json, uuid, tarfile

async def download_config_locally(host: str, port: int, user: str, password: str) -> bytes:
    """Download uiconfig.tar.gz directly from the local Savant server."""
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    session = aiohttp.ClientSession()
    ws = await session.ws_connect(
        f"wss://{host}:{port}/",
        protocols=["rpm-protocol"],
        ssl=ssl_ctx
    )
    
    # Step 1: DevicePresent (no hostUID/homeID needed for local)
    dp = {
        "device": {
            "UID": uuid.uuid4().hex.upper(),
            "OS": "Linux", "app": "pysavant", "versionName": "0.1.0",
            "model": "Python Client", "make": "Custom",
            "type": "Android", "name": "pysavant", "class": "phone",
        },
        "messageFormat": 1, "protocolVersion": "2.0",
        "configurationID": str(uuid.uuid4()),
        "cloudToken": "", "hostUID": "", "homeId": "",
    }
    await ws.send_bytes(
        msgpack.packb({"URI": "session/devicePresent", "messages": [dp]}, use_bin_type=False)
    )
    
    # Step 2: Read deviceRecognized (wait for Text frame)
    msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
    assert msg.type == aiohttp.WSMsgType.TEXT
    
    # Step 3: AuthRequest with user credentials
    await ws.send_bytes(
        msgpack.packb({
            "URI": "session/authenticationRequest",
            "messages": [{"user": user, "password": password}]
        }, use_bin_type=False)
    )
    msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
    assert msg.type == aiohttp.WSMsgType.TEXT
    
    # Step 4: Request config file
    await ws.send_bytes(
        msgpack.packb({
            "URI": "session/fileDownload",
            "messages": [{"filePath": "uiconfig.tar.gz"}]
        }, use_bin_type=False)
    )
    
    # Step 5: Read binary chunks
    file_data = bytearray()
    for _ in range(200):
        msg = await asyncio.wait_for(ws.receive(), timeout=15.0)
        if msg.type == aiohttp.WSMsgType.BINARY:
            data = msg.data
            flags = data[1]
            is_complete = bool(flags & 0x80)
            ident_len = int.from_bytes(data[10:14], "big")
            header_size = 14 + ident_len
            if header_size < len(data):
                file_data.extend(data[header_size:])
            if is_complete:
                break
    
    await ws.close()
    await session.close()
    return bytes(file_data)
```

### Binary Transfer Protocol (on wire)

Each binary frame has a **14-byte header** followed by optional identifier/options and payload:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 1 | `type` | 1 = file, 2 = camera |
| 1 | 1 | `flags` | Bit 7 = `isComplete`, Bits 0-6 = `version` |
| 2 | 8 | `fileSize` | Total file size (big-endian uint64) |
| 10 | 4 | `identLength` | Length of identifier/options (big-endian uint32) |
| 14 | * | `ident` or `options` | Identifier string (ASCII) OR msgpack-encoded options map (detected by byte 14 & 0xF0 == 0x80) |
| 14+* | * | `payload` | Binary data chunk |

**Source:** `SavantBinaryTransfer.TransferPacket(byte[])` in `SavantBinaryTransfer.java`

---

## Phase 1: WebSocket Connection & Authentication

Before any configuration can be downloaded, the app must establish a WebSocket session:

```
Client                                     Host
  |                                          |
  |--- WSS connect (hostname:5000) -------->|
  |    sub-protocol: "rpm-protocol"         |
  |                                          |
  |--- session/devicePresent ------------->  |
  |    {UID, hostUID, homeID, type,         |
  |     configurationID, cloudToken, ...}   |
  |                                          |
  |<-- session/deviceRecognized -----------  |
  |    {hostUID, homeID, authorized,        |
  |     authentication, configurationUID,  |
  |     buildNumber, buildVersion,          |
  |     hostName, protocolVersion}          |
  |                                          |
  |--- session/authenticationRequest ---->  |
  |    (if auth needed)                     |
  |    {user, password/pinCode, hostToken}  |
  |                                          |
  |<-- session/authenticationResponse -----  |
  |    {hostToken, hostSecretKey,           |
  |     configurationUID, startZone,        |
  |     permissions}                        |
  |                                          |
  |        Session state: READY (3)          |
```

**Source:** `SavantConnection.java` (Session class), `SavantControl.java` (ConnectionManger)

---

## Phase 2: Configuration Update Check

After authentication, the session checks if the configuration is up to date.

### The `Session.updateAvailable` Flag

The `DeviceResponse` (from `session/deviceRecognized`) contains:
- `configurationUID` — a GUID identifying the current configuration
- Various build/version info

When the configuration is outdated (determined by comparing `configurationUID` with the cached value on disk), the **`updateAvailable` flag is set to `true`** on the `Session` object.

### The Flow in `ConnectionManger.onConnect()`

```java
// SavantControl.java — ConnectionManger.onConnect()
if (mConnection.isUpdateAvailable() && !ignoreConfigUpdateForConnectionRestore) {
    Log.i(TAG, "Update available, downloading new configuration.");
    mConnection.downloadConfiguration(new ConfigRequest());
} else {
    Log.i(TAG, "Configuration is up to date.");
    systemReady(false);
}
```

**Source:** `SavantControl.java` lines 2118–2126

---

## Phase 3: Configuration Download (`uiconfig.tar.gz`)

### Requesting the Download

The app sends a file download request over the **WebSocket** (not HTTP):

```
Client                                          Host
  |                                               |
  |--- session/fileDownload ------------------>  |
  |    {filePath: "uiconfig.tar.gz"}             |
  |                                               |
  |<-- [binary data chunks] ------------------  |
  |    (MessagePack frames with file metadata)   |
  |                                               |
  |<-- [final chunk with "complete" flag] -----  |
  |    (triggers extraction)                     |
```

### Request Format

```java
// SavantMessages.java — ConfigRequest class
public class ConfigRequest extends FileRequest {
    public String path = "uiconfig.tar.gz";
    
    public Map<Object, Object> toMap() {
        HashMap hashMap = new HashMap();
        hashMap.put("filePath", this.path);
        return hashMap;
    }
}
```

**URI:** `session/fileDownload`

**Source:** `SavantMessages.java` (ConfigRequest), `SavantConnection.java` (downloadConfiguration)

### Binary Transfer Protocol

The file is received as a series of binary MessagePack frames via the WebSocket. The `SavantBinaryTransfer` class handles the assembly:

1. Each incoming binary frame contains a **transfer packet** with:
   - `identifier` — file name (`uiconfig.tar.gz`)
   - `sessionID` — transfer session identifier
   - `payload` — data chunk bytes
   - `fileSize` — total file size
   - `isComplete` — whether this is the final chunk
   - `persistent` — whether this is a resume (appending to existing file)
   - `type` — 1=file, 2=camera
   - `options` — additional metadata map

2. Chunks are written to `Savant.paths.getSystemDir(hostUID)/uiconfig.tar.gz`
3. On completion (`isComplete == true`), the file is extracted:
   - `.tar.gz` → GZIP decompress to `.tar` → TarInputStream extract
   - Files are extracted to `Savant.paths.getSystemDir(hostUID)/`

**Source:** `SavantBinaryTransfer.java` (handleFilePacket, untar)

### Storage Path

```java
// SavantPaths.java
public File getSystemDir(String hostUID) {
    return new File(this.mBaseDir, hostUID);
}
```

On Android: `/data/data/com.savantsystems.controlapp.pro/files/{hostUID}/`

---

## Phase 4: Data Initialization (`systemReady`)

After the configuration is downloaded (or if already up to date), the system enters "ready" state.

### The `systemReady()` Method

```java
// SavantControl.java — ConnectionManger.systemReady()
private void systemReady(boolean z) {
    // ... setup ...
    if (mSystemUID != null && context != null) {
        mData = SavantData.getSavantData("DEFAULT", context, mSystemUID, null, null);
        mData.setUIManifest(mSystemManifest);
        mData.setCustomScreenData(mCustomScreenData);
    }
    // ...
    mIsReady = true;
    // ... register states, notify listener ...
}
```

### How `SavantData` is Created

```java
// SavantData.java
public static SavantData getSavantData(String dataType, Context context, 
                                         String systemUID, SQLiteDatabase db1, SQLiteDatabase db2) {
    return new SavantSqlDataK(context, systemUID, dataType, db1, db2);
}
```

The `SavantSqlDataK` constructor opens the SQLite database from disk:

```java
// SavantSQLData.java (parent of SavantSqlDataK)
File file = new File(Savant.paths.getSystemDir(systemUID), "serviceImplementation.sqlite");
this.mDatabase = SQLiteDatabase.openDatabase(file.toString(), null, 17);
```

**Source:** `SavantSQLData.java` lines 50–56

### Extracted Files

After `uiconfig.tar.gz` extraction, the following files exist under `paths.getSystemDir(hostUID)/`:

| File | Purpose |
|------|---------|
| `serviceImplementation.sqlite` | **Main configuration database** (rooms, services, entities, commands) |
| `uimanifest.json` | UI layout definitions (screen structure, button layouts) |
| `bos/` | Custom screen definitions (`.xml` files) |
| Other `.json`, `.xml` files | Additional configuration assets |

---

## Phase 5: Reading Room and Entity Data from SQLite

### `getRooms()` — The Core Room Query

When `ProductionHomeModel.getRooms()` is called, it delegates through:

```
HomeModel.getRooms()
  → Savant.control.getData().getAllRooms()
    → SavantSQLData.getAllRooms()
      → SQLite query (rawQuery) on Rooms table
```

### The SQL Query for Rooms

```sql
SELECT DISTINCT 
    Rooms.id, Rooms.name, RoomGroups.name as groupName,
    hasAV, hasLights, hasShades, hasHVAC, hasSecurity, hasCameras
FROM Rooms
LEFT JOIN RoomGroupMap ON Rooms.id = RoomGroupMap.roomID
LEFT JOIN RoomGroups ON RoomGroups.id = RoomGroupMap.groupID
LEFT JOIN RoomCapabilities ON Rooms.id = RoomCapabilities.roomID
WHERE Rooms.name NOT IN ('__ROOM_BLACKLIST__')
ORDER BY RoomGroups.name IS NULL, RoomGroups.name, Rooms.name
```

**Source:** `SavantQueries.java` (V1Statements.allRooms())

### Room Object Construction

Each row is built into a `Room` object (from `Room.java`):

```java
Room room = new Room(cursor.getString("name"), localizedName);
room.roomId = cursor.getString("roomID");
room.group = new RoomGroup(cursor.getString("groupName"));

// Version-dependent columns
if (version >= 3) {
    room.hasAV = cursor.getInt("hasAV") == 1;
    room.hasLighting = cursor.getInt("hasLights") == 1;
    room.hasShades = cursor.getInt("hasShades") == 1;
    room.hasHVAC = cursor.getInt("hasHVAC") == 1;
    room.hasSecurity = cursor.getInt("hasSecurity") == 1;
    room.hasCameras = cursor.getInt("hasCameras") == 1;
}
if (version >= 13) room.hasFans = cursor.getInt("hasFans") == 1;
if (version >= 14) room.hasDimmers = cursor.getInt("hasDimmers") == 1;
if (version >= 27) {
    room.hasGarageDoor = cursor.getInt("hasGarageDoor") == 1;
    room.hasDoorLock = cursor.getInt("hasDoorLock") == 1;
}
if (version >= 29) room.hasEntry = cursor.getInt("hasEntry") == 1;
```

**Source:** `SavantSQLData.java` (getAllRooms)

### `getEntities()` — Device Discovery

```java
// SavantData.java
public List<SavantEntities.Entity> getEntities(Room room, String zone, Service service) {
    int type = SavantEntities.typeForService(service);
    switch (type) {
        case 1: return getHVACEntities(roomId, zone, service);
        case 2: return getLightEntities(roomId, zone, service);
        case 3: return getShadeEntities(roomId, zone, service);
        case 4: return getSecurityEntities(roomId, zone, service);
        case 5: return getCameraEntities(roomId, zone, service);
        case 6: return getPoolSpaEntities(roomId, zone, service);
        case 7: // Home Monitor
        case 8: return getFanEntities(roomId, zone, service);
        case 9: return getDoorLockEntities(roomId, zone, service);
        case 10: return getGarageEntities(roomId, zone, service);
        case 11: return getEntryEntities(roomId, zone, service);
        case 12: return getEvChargerEntities(service);
        case 13: return getGateEntities(roomId, zone, service);
        case 14: return getHotWaterHeaterEntities(roomId, zone, service);
    }
}
```

**Source:** `SavantData.java` (getEntities)

### Lighting Entity Query

```sql
SELECT 
    light.name, light.addresses, light.entityType,
    light.pressCommand, light.holdCommand, light.releaseCommand,
    light.togglePressCommand, light.toggleHoldCommand, light.toggleReleaseCommand,
    light.dimmerCommand, light.fadeTime, light.delayTime, light.stateName,
    light.id,
    services.zone, services.component, services.logicalComponent,
    services.serviceVariantID, services.serviceType,
    Zones.name, Rooms.name, isSceneable
FROM Rooms
    JOIN ServiceImplementationServiceResources services ON Rooms.id = services.zone
    JOIN LightEntities light ON light.zoneID = Zones.id
WHERE Rooms.name IS NOT NULL
  AND Zones.name IS NOT NULL
  AND services.zone IS NOT NULL
  AND services.component IS NOT NULL
  AND services.logicalComponent IS NOT NULL
  AND services.serviceVariantID IS NOT NULL
  AND services.serviceType IS NOT NULL
GROUP BY light.id
ORDER BY light.id
```

**Source:** `SavantQueries.java` (V5Statements.lightingEntitiesWithArguments)

Similar queries exist for:
- **Shades**: `ShadeEntities` table (shade.name, shade.addresses, shade.entityType, sceneNumber, etc.)
- **HVAC**: HVAC-specific tables
- **Security**: `SecuritySystemEntities` table (partitionNumber, zoneNumber, hasBypass, etc.)
- **Cameras**: `CameraEntities` table (cameraName, previewURL, fullscreenURL, etc.)
- **Fans**: `FanEntities` table
- **Door Locks**: Door lock specific tables
- **Garage**: Garage specific tables
- **Gates**: Gate specific tables
- **Entry**: Entry system tables
- **EV Chargers**: `EVChargerEntities` table
- **Pool/Spa**: Pool/Spa specific tables

### Service Discovery

Rooms are linked to services via `ServiceImplementationServiceResources` table:

```sql
-- Get services for a zone/room
SELECT ... FROM ServiceImplementationServiceResources services
JOIN ServiceInfo ON services.id = ServiceInfo.serviceID
WHERE services.zone = ?
  AND services.component = ?
  -- ... etc
```

The `Service` object has these key fields:
```java
public class Service {
    public String zone;              // Room/zone name
    public String component;         // e.g., "Cable 1", "Lighting_controller"
    public String logicalComponent;  // e.g., "Cable_box", "Dimmer"
    public String variantID;         // e.g., "1"
    public String serviceID;         // e.g., "SVC_AV_TV", "SVC_ENV_LIGHTING"
    public String alias;             // Human-readable name
    public String brand;             // Device brand
    public boolean hidden;           // Hidden from UI
    public List<String> capabilities;
}
```

**Source:** `Service.java`, `SavantQueries.java`

---

## Phase 6: State Subscription & Runtime Values

After the SQLite config is loaded, the app subscribes to runtime state updates:

```
-- After systemReady():
1. Re-register previously subscribed states (state/register)
2. Host pushes StateUpdate with current values
3. Host pushes updates on every state change
```

### State Key Pattern

```
{Room}.{Component}.{LogicalComponent}.{Variant}.{ServiceID}.{Property}
```

Example: `Living Room.Cable 1.Cable_box.1.SVC_AV_TV.ServiceIsActive`

### Lighting State Example

For a lighting load with address `1_1_1`, the state key would be:
```
Lights.Lighting_controller.DimmerLevel_1_1_1
```

The state key structure is derived from the `Entity.getLightDefinition()` method:

```java
// SavantEntities.java — Entity.getLightDefinition()
public String getLightDefinition() {
    return getStateScope() + getStateSuffix().substring(1).replace("_", ".");
}
// getStateScope() → "{component}.{logicalComponent}."
// getStateSuffix() → "_{address1}_{address2}_..."
// Result: "Lights.Lighting_controller.1.1.1"
```

**Source:** `SavantEntities.java`, `StateManager.java`

---

## Complete Discovery Flow Diagram

```
┌─────────────────────────────────────────────┐
│ 1. WebSocket Handshake                       │
│    DevicePresent → DeviceRecognized          │
│    AuthRequest → AuthResponse                │
│    → Session state: READY                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 2. Version Check                             │
│    If configurationUID changed:              │
│    → session/fileDownload                    │
│      {filePath: "uiconfig.tar.gz"}           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. Binary Transfer                           │
│    Receive chunks over WebSocket             │
│    → Assemble uiconfig.tar.gz               │
│    → Extract to system dir                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. Data Initialization                       │
│    Open serviceImplementation.sqlite        │
│    Load uimanifest.json                     │
│    Load custom screens                      │
│    → SavantData is ready                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 5. Query Configuration (SQLite)              │
│    getAllRooms() → Room[]                    │
│    getServices(service) → Service[]          │
│    getEntities(room, zone, service) → Entity[]│
│                                              │
│    Room.hasLighting → discover lights        │
│    Room.hasHVAC → discover HVAC              │
│    Room.hasShades → discover shades          │
│    etc.                                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 6. Subscribe to Runtime States               │
│    state/register                            │
│    → Receive StateUpdate (current values)   │
│    → Push updates (on change)               │
│                                              │
│    "Living Room.DimmerLevel_1_1_1" = 75     │
│    "Living Room.ThermostatCurrentSetPoint" = 72  │
│    etc.                                      │
└─────────────────────────────────────────────┘
```

---

## Key Source Files

| File | Original Source Path | Purpose |
|------|------|---------|
| `SavantControl.java` | `com/savantsystems/control/SavantControl.java` | Main control, systemReady(), ConnectionManger |
| `SavantConnection.java` | `com/savantsystems/core/connection/SavantConnection.java` | WebSocket connection, downloadConfiguration(), Session |
| `SavantBinaryTransfer.java` | `com/savantsystems/core/connection/SavantBinaryTransfer.java` | Binary file reception, tar.gz extraction |
| `SavantMessages.java` | `com/savantsystems/core/connection/SavantMessages.java` | ConfigRequest, FileRequest, ServiceRequest |
| `SavantData.java` | `com/savantsystems/core/data/SavantData.java` | Abstract data layer, getEntities() dispatcher |
| `SavantSQLData.java` | `com/savantsystems/core/data/SavantSQLData.java` | SQLite queries: getAllRooms(), getLightEntities(), etc. |
| `SavantSqlDataK.kt` | `com/savantsystems/core/data/SavantSqlDataK.kt` | Kotlin bridge to SavantSQLData |
| `SavantQueries.java` | `com/savantsystems/core/data/SavantQueries.java` | All SQL query builders by version |
| `SavantEntities.java` | `com/savantsystems/core/data/SavantEntities.java` | Entity class hierarchy, typeForService() |
| `Service.java` | `com/savantsystems/core/data/service/Service.java` | Service model (zone, component, serviceID) |
| `Room.java` | `com/savantsystems/core/data/room/Room.java` | Room model with has* flags |
| `HomeModel.java` | `savant/savantmvp/model/sdk/HomeModel.java` | Abstract home model, getRooms()/getEntities() |
| `ProductionHomeModel.java` | `savant/savantmvp/model/sdk/ProductionHomeModel.java` | Concrete implementation delegating to SavantData |
| `SavantPaths.java` | `com/savantsystems/control/paths/SavantPaths.java` | File system paths for config storage |

---

## Appendix: Entity Type Mapping

```java
// SavantEntities.java static initializer
typeMap.put(ServiceTypes.HVAC,                     1);  // HVAC
typeMap.put(ServiceTypes.HVAC_SINGLE_SET_POINT,     1);  // HVAC single setpoint
typeMap.put(ServiceTypes.LIGHTING,                  2);  // Lighting
typeMap.put(ServiceTypes.SHADE,                     3);  // Shades
typeMap.put("SVC_ENV_SECURITYSYSTEM",               4);  // Security
typeMap.put("SVC_ENV_USERLOGIN_SECURITYSYSTEM",     4);  // User-login security
typeMap.put(ServiceTypes.SECURITY_CAMERA,           5);  // Cameras
typeMap.put(ServiceTypes.POOL_AND_SPA,              6);  // Pool & Spa
typeMap.put(ServiceTypes.FAN,                       8);  // Fans
typeMap.put(ServiceTypes.DOOR_LOCK,                 9);  // Door locks
typeMap.put(ServiceTypes.GARAGE,                   10);  // Garage doors
typeMap.put(ServiceTypes.GATE,                     13);  // Gates
typeMap.put(ServiceTypes.ENTRY,                    11);  // Entry/doorbell
typeMap.put(ServiceTypes.EV_CHARGER,               12);  // EV chargers
typeMap.put(ServiceTypes.HOT_WATER,                14);  // Hot water heaters
```
