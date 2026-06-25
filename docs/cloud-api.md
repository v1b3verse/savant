# Cloud REST API

[< Back to Overview](../SAVANT.md)

---

## Base URLs

| Environment | URL |
|-------------|-----|
| **Production** | `https://api.savantcs.com/edge` |
| Beta 1 | `https://cbeta1-edge.savantcs.com/edge` |
| Dev 2 | `https://cdev2-edge.savantcs.com/edge` |
| Alpha 1 | `https://calpha1-edge.savantcs.com/edge` |
| Fault Vault | `https://faultvault.savantcs.com/faultvault` |

**Local host REST:** `https://<hostname>:9001/`

---

## User Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `api/users/login` | Login (email, password, **type:int**, clientId) — `type` is an **integer** (0=REGULAR_USER, 1=LITE_INSTALLER), not a string |
| POST | `api/users` | Create account (email, firstName, lastName, password, tsAndCsAccepted) |
| GET | `api/users/{userId}` | Get user profile |
| PUT | `api/users/{userId}` | Update user |
| DELETE | `api/users/{userId}` | Delete account |
| PUT | `api/users/{userId}/signout` | Logout |
| GET | `api/users/checkemail?email=` | Check email availability |
| POST | `api/users/2fa/check` | Check 2FA requirement |
| GET | `api/users/{userId}/isemailverified` | Check email verification |
| POST | `api/users/resendverificationemail?email=` | Resend verification email |
| POST | `api/users/password/reset` | Request password reset |
| PUT | `api/users/{userId}/pincode` | Set/update PIN |
| POST | `api/users/{userId}/pincode/auth` | Authenticate with PIN |
| PUT | `api/users/{userId}/profilepic` | Update profile picture URL |

**Source:** `core/cloud/resource/user/UserRequestApi.java`

---

## Home Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `api/users/{id}/homes` | List user's homes |
| GET | `api/users/{id}/homes/uber2?accessRequests=&homeInvitation=` | Extended home list |
| GET | `api/homes/{homeId}` | Home details |
| GET | `api/homes/{homeId}/config` | **Full house configuration as JSON** (rooms with capabilities, services, zones, security, cameras) |
| GET | `api/homes/{homeId}/config/active` | **Active config metadata** with signed S3 URL to download the `.rpmConfig.tar.gz` archive containing the SQLite database (`serviceImplementation.sqlite`) and all other configuration files |
| GET | `api/homes/{homeId}/rooms` | Rooms in home |
| GET | `api/homes/rooms/types` | Room type definitions |
| GET | `api/homes/{homeId}/users/{userId}` | User in home |
| DELETE | `api/homes/{homeId}/users/{userId}` | Remove user from home |
| PUT | `api/homes/{homeId}/users/{userId}/permissions` | Update permissions |
| POST | `api/homes/{homeId}/claimcode` | Generate claim code |
| PUT | `api/homes/{homeId}/invitations/accept/{invitationId}` | Accept invitation |
| GET | `api/homes/{homeId}/access` | Access settings |
| PUT | `api/homes/accessrequest` | Request dealer access |
| GET | `api/homes/{homeId}/partners` | OAuth partners |
| DELETE | `api/homes/{homeId}/partners/{partnerId}` | Remove partner |
| GET | `api/thirdparty/home/{homeId}/partner/{manufacturer}` | Third-party integration |

**Source:** `core/cloud/resource/home/HomeRequestApi.java`

---

## Video Clips

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `api/video/clips/{homeId}` | List video clips |
| GET | `api/video/clips/{homeId}/{cameraId}?rangeStart=&rangeEnd=&eventIds=&onlyProtected=` | Camera clips |
| POST | `api/video/clips/{homeId}/byCameraIds` | Clips by camera IDs |
| DELETE | `api/video/clips/{homeId}/{cameraId}/{clipId}` | Delete clip |

---

## Notifications

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `api/clients` | Device check-in / register for push |
| PUT | `api/clients` | Update notification token |
| GET | `api/homes/{homeId}/triggers` | List notification triggers |
| POST | `api/homes/{homeId}/triggers` | Create trigger |
| PUT | `api/homes/{homeId}/triggers/{triggerId}` | Update trigger |
| PUT | `api/homes/{homeId}/triggers/{triggerId}/enable` | Enable trigger |
| PUT | `api/homes/{homeId}/triggers/{triggerId}/disable` | Disable trigger |
| DELETE | `api/homes/{homeId}/triggers/{triggerId}` | Delete trigger |

### FCM Registration

```json
{
  "pushNotificationIdentifier": "<fcm_token>",
  "channel": "cedia",
  "appVersion": "11.1.4",
  "manufacturer": "Samsung",
  "model": "Galaxy S24",
  "osVersion": "14",
  "deviceType": "Android",
  "os": "Android"
}
```

**Source:** `core/cloud/resource/notification/NotificationRequestApi.java`

---

## Local Host Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `api/clients/{id}/login` | Local client login |
| GET | `components` | List components |
| PUT | `components/{id}` | Update component |
| POST | `config/apply` | Apply configuration |

**Source:** `core/cloud/resource/local/LocalRequestApi.java`

---

## OTA Updates

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `config/v1/location/ota/cmdetails` | OTA component details |
| GET | `config/v1/location/ota/cmstates` | OTA component states |
| GET | `config/v1/location/ota/states` | OTA states |
| POST | `config/v1/location/ota/cminstall` | OTA component install |
| POST | `config/v1/location/ota/install` | Trigger OTA install |

**Source:** `core/rest/ota/OtaRestRequestApi.java`

---

## Access Requests

| Method | Endpoint | Purpose |
|--------|----------|---------|
| PUT | `api/homes/{homeId}/accessrequests/{requestId}` | Accept/reject dealer access |

All paths relative to `com/savantsystems/` under the app package root
