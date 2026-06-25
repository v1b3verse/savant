# Authentication

[< Back to Overview](../SAVANT.md)

---

## Cloud Authentication — HMAC-SHA256

The app uses a custom HMAC-SHA256 scheme (not JWT/OAuth).

### Header Construction

```
SCS-Authorization: <base64(message)>:<hmac-sha256(message, secret)>
SCS-Agent: <api_key>
SCS-Channel: cedia
Content-Type: application/json
```

### Message JSON

```json
{
  "alg": "SHA256",
  "iat": 1708700000000,
  "iss": "SCS",
  "sub": "user@example.com",
  "typ": "USER"
}
```

### HMAC Generation

```java
SecretKeySpec key = new SecretKeySpec(secret.getBytes(), "HmacSHA256");
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(key);
String signature = hex(mac.doFinal(base64message.getBytes()));
```

For local client auth, `typ` is set to `"HOST"` instead of `"USER"`.

**Source:** `com/savantsystems/core/cloud/SavantRestUtils.java`

---

## API Keys (per environment)

| Environment | Key |
|-------------|-----|
| RELEASE | `FoWT9Z40axK88bO95EbNVfDILm34ff` |
| ALPHA | `JUa0aq5MT8zaJ93mIpCo9oXItFUO5y` |
| BETA | `7tLg9qUXt135v6389kMOivkqsbx1W6` |
| DEV2 | `Nmch38eg4eOy8bWLdXFmPaLY482w1P` |

---

## Login Flow

1. POST `api/users/login` with `{email, password, type, clientId}`
2. Response returns `SavantUser` with `id`, `token`, `secret`
3. `token` = subject for HMAC, `secret` = HMAC signing key
4. All subsequent requests signed with HMAC headers
5. On 401: `SavantAuthenticator` re-authenticates automatically with stored email+password

### Two-Factor Authentication

- POST `api/users/2fa/check` to determine if 2FA is required
- Supports EMAIL_CODE verification type
- Flow: `checkTwoFactor` -> `loginWithTwoFactor`

### Token Lifecycle

- Obtained on login via `api/users/login`
- Stored in `SavantUser` object (and SharedPreferences)
- Attached to every authenticated request
- Refreshed automatically on 401 response via `SavantAuthenticator`
- Cleared on logout

---

## Local WebSocket Authentication

1. WebSocket connects to `wss://hostname:port/` (port from discovery response or manual config)
2. Client sends `DevicePresent` message
3. Host responds with `DeviceResponse` (session info)
4. If auth required: Client sends `AuthRequest` with username + password/PIN
5. Host returns `AuthResponse` with `hostToken` and `hostSecretKey`

### Local Client Credentials

Stored separately from cloud credentials:
- `localClientToken` — Token for local access
- `localClientSecret` — Secret for HMAC
- `localClientID` — Client identifier

**Source:** `com/savantsystems/controlapp/launch/LocalClientManager.java`

---

## User Permission Model

```json
{
  "admin": true,
  "remote": true,
  "notifications": true,
  "zoneBlacklist": [],
  "serviceBlacklist": []
}
```

### User Types

| Type | Description |
|------|-------------|
| `ADMIN` | Full system access |
| `HOUSEHOLD` | Standard user |
| `GUEST` | Limited access |
| `LOCAL` | Local-only access |

### SavantUser Object

```java
public class SavantUser {
    String id;
    String email;
    String password;       // Stored plaintext (security concern)
    String token;          // Auth token from server
    String secret;         // HMAC signing key
    String firstName, lastName;
    String type;           // ADMIN, HOUSEHOLD, GUEST, LOCAL
    Object permissions;
    boolean twoFactor;
    boolean pinAuthRequired;
    String profilePicUrl;
}
```

---

## Complete Authentication Flow

```
1. USER LOGIN
   +-- Email + Password + ClientID
       +-- POST /api/users/login
           +-- Response: SavantUser {id, token, secret, ...}

2. CHECK 2FA (if required)
   +-- POST /api/users/2fa/check
   +-- User enters code
   +-- POST /api/users/login with twoFactor data

3. FETCH HOMES
   +-- GET /api/users/{id}/homes
       +-- Returns list of SavantHome objects

4. SELECT HOME
   +-- GET /api/homes/{homeId}
       +-- Get system details (localURL, cellURL, etc.)

5. ESTABLISH CONNECTION
   +-- LOCAL (if available):
   |   +-- WebSocket wss://hostname:port/
   |   +-- DevicePresent -> DeviceResponse -> AuthRequest -> AuthResponse
   |
   +-- REMOTE (if local unavailable):
       +-- All requests via cloud API with HMAC headers

6. MAINTAIN SESSION
   +-- Attach token + secret to all requests
   +-- On 401: Auto-retry with re-authentication
```
