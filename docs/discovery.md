# Discovery & Connection

[< Back to Overview](../SAVANT.md)

---

## mDNS/Bonjour

The app discovers local Savant hosts via mDNS with service name **`_control_.ws`**.

**Source:** `com/savantsystems/core/discovery/SavantDiscovery.java`

---

## SavantHome Data Model

Each discovered (or cloud-retrieved) system is represented as a `SavantHome`:

```json
{
  "hostUID": "XXXXXXXXXXXX",
  "homeID": "6A870A4A-0505-4E35-8730-...",
  "hostName": "savant-host.local",
  "scheme": "wss",
  "port": 5000,
  "localURL": "wss://savant-host.local:5000",
  "cellURL": "https://...",
  "bluetoothAddress": "AA:BB:CC:DD:EE:FF",
  "isCloud": true,
  "isLocallyAvailable": true,
  "isRemote": true,
  "online": true,
  "cloudEnvironment": "production",
  "cloudStatus": 2,
  "configStatus": 4,
  "channel": 1,
  "version": 3,
  "buildVersion": "...",
  "onboardKey": "...",
  "wifiSSID": "...",
  "remoteAccessEnabled": true,
  "notificationsEnabled": true,
  "sipNumber": "...",
  "sipPassword": "...",
  "sipProxyHost": "...",
  "sipProxyPort": 5060
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `hostUID` | Unique hardware identifier of the Savant host |
| `homeID` | Cloud-assigned home identifier |
| `scheme` | `"wss"` (default) or `"ws"` |
| `port` | WebSocket port, default `5000` |
| `cellURL` | Remote/cloud relay URL for off-network access |
| `channel` | 1 = Mid, 2 = Pro |
| `onboardKey` | Used during initial device pairing |
| `bluetoothAddress` | BT MAC for offline fallback |
| `sipNumber` / `sipPassword` | SIP telephony integration |
| `sipProxyHost` / `sipProxyPort` | SIP proxy (default 5060) |

### URI Construction

```java
public URI getURI() {
    String scheme = this.scheme != null ? this.scheme : "wss";
    String url = scheme + "://" + hostName;
    if (port > 0) url += ":" + port;
    return URI.create(url);
}
```

**Source:** `com/savantsystems/core/discovery/SavantHome.java`

---

## Connection Modes

### 1. Local Network (Priority)

Direct WebSocket to `wss://hostname:5000/` discovered via mDNS. Self-signed certificates accepted. No cert verification.

### 2. Cloud Remote Access

Routes through cloud API endpoints. Requires cloud auth (token + secret). Target determined by `cellURL` or cloud proxy.

### 3. Bluetooth/OBEX (Fallback)

OBEX over Bluetooth for offline pairing. Uses `bluetoothAddress` from SavantHome.

### Connection Selection

The app checks `isLocallyAvailable` first. If the system is reachable on LAN, it connects locally. Otherwise it falls back to cloud remote access via `cellURL`.
