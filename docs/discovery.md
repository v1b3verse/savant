# Discovery & Connection

---

## UDP Probe Discovery

The official Savant app discovers hosts via a **custom UDP probe**, not mDNS/Bonjour.

The probe is sent to **UDP port 9101** with a MessagePack-encoded payload:

```json
{"service": "_control_.ws", "version": 1}
```

The host responds with a `SavantHome` map containing connection details:

| Field | Description |
|-------|-------------|
| `UID` / `hostUID` | Unique hardware identifier of the Savant host |
| `homeID` / `homeId` | Cloud-assigned home identifier |
| `hostName` | Host display name |
| `scheme` | `"wss"` (default) or `"ws"` |
| `port` | WebSocket port advertised by the host |
| `online` | Whether the host reports itself online |
| `version` | Protocol version |
| `buildNumber` | Build version |

### Discovery Strategy

The library uses a two-phase strategy matching the Android app:

1. **Broadcast** — send the probe to all LAN subnet broadcasts
2. **Subnet sweep** — if no broadcast response arrives within half the timeout, send unicast probes to every address (.1 through .254) on each detected subnet

**Source:** `com/savantsystems/core/discovery/SavantDiscovery.java`, `SavantHome.java`

---

## Host Response (SavantHome)

Example response from a real Savant host:

```json
{
  "UID": "XXXXXXXXXXXX",
  "homeID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "hostName": "SAVANT",
  "scheme": "wss",
  "port": 42333,
  "online": true,
  "version": 3,
  "buildNumber": 42
}
```

> The `port` value is the actual WebSocket port the host is listening on. It varies by system and firmware version — do not hardcode it.

---

## Connection

### Local Network (Primary)

Direct WebSocket to `wss://<host>:<port>/` discovered via UDP probe or configured manually. Self-signed certificates are accepted (no cert verification).

### Cloud Remote Access

Routes through the cloud API. Requires cloud auth (token + secret). The target is determined by `cellURL` from the cloud login response.

### Connection Selection

The app first tries local network connection. If the host is reachable on LAN it connects directly; otherwise it falls back to cloud remote access.
