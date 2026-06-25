# Source File Map

[< Back to Overview](../SAVANT.md)

All paths relative to `com/savantsystems/` under the app package root

---

## Core Protocol

| File | Purpose |
|------|---------|
| `core/connection/SavantConnection.java` | Connection manager, message routing, session lifecycle |
| `core/connection/SavantMessages.java` | All message classes, URI builders, serialization |
| `core/connection/SavantWebSocket.java` | WebSocket transport |
| `core/connection/SavantTransport.java` | Abstract transport (MessagePack) |
| `core/connection/ws/WebSocketClient.java` | Low-level WebSocket client (OkHttp3) |
| `core/msgpack/ObjectPack.java` | MessagePack encode/decode |
| `core/state/StateManager.java` | State subscriptions and event bus |
| `core/discovery/SavantDiscovery.java` | UDP probe host discovery |
| `core/discovery/SavantHome.java` | Home data model |

---

## Cloud / Auth

| File | Purpose |
|------|---------|
| `core/cloud/SavantCloud.java` | Cloud coordination |
| `core/cloud/SavantRestUtils.java` | HMAC auth header construction |
| `core/cloud/SavantSSLHelper.java` | SSL/TLS configuration (trust-all) |
| `core/cloudrx/SavantServiceFactory.java` | Retrofit service factory, base URLs |
| `core/cloudrx/retrofit/SavantAuthenticator.java` | Auto token refresh on 401 |
| `core/cloudrx/services/UserService.java` | User API service |
| `core/cloudrx/services/HomeService.java` | Home API service |
| `core/cloudrx/services/HostService.java` | Host API service |

---

## REST API Definitions

| File | Purpose |
|------|---------|
| `core/cloud/resource/home/HomeRequestApi.java` | Home management endpoints |
| `core/cloud/resource/user/UserRequestApi.java` | User management endpoints |
| `core/cloud/resource/local/LocalRequestApi.java` | Local host endpoints |
| `core/cloud/resource/notification/NotificationRequestApi.java` | Push notification endpoints |
| `core/cloud/resource/core/DiagnosticsRequestApi.java` | Diagnostics |
| `core/cloud/resource/core/VaultRequestApi.java` | Fault vault |
| `core/cloud/resource/uei/UEIRequestApi.java` | UEI IR code service |
| `core/rest/ota/OtaRestRequestApi.java` | OTA update endpoints |

---

## Control Protocol

| File | Purpose |
|------|---------|
| `control/messaging/SavantScene.java` | Scene management |
| `control/messaging/environment/LightRequests.java` | Lighting commands |
| `control/messaging/environment/FanRequests.java` | Fan commands |
| `control/messaging/hvac/HVACRequests.java` | HVAC commands |
| `control/messaging/shades/ShadeRequests.java` | Shade commands |
| `controlapp/services/requests/SecurityRequests.java` | Security commands |
| `controlapp/dev/energy/repository/EnergyRepository.java` | Energy monitoring |
| `core/data/service/ServiceTypes.java` | Service type constants |
| `core/data/SavantEntities.java` | Entity definitions |
| `core/data/user/SavantUser.java` | User data model |

---

## UI Application

| File | Purpose |
|------|---------|
| `controlapp/launch/CloudLoginModel.java` | Cloud login logic |
| `controlapp/launch/CloudLoginFragment.java` | Login UI |
| `controlapp/launch/CloudLoginViewModel.java` | Login view model |
| `controlapp/launch/LocalClientManager.java` | Local auth management |
| `controlapp/discovery/HomeSelectorFragment.java` | Home selection UI |
| `controlapp/notifications/NotificationManager.java` | Push notification handling |
| `controlapp/notifications/NotificationService.java` | FCM service |
| `controlapp/services/av/media/OAuthWebActivity.java` | Third-party OAuth flow |

---

## Package Structure

```
com/savantsystems/
  analytics/          - Analytics tracking
  animations/         - Custom animations
  config/             - Configuration system
  control/            - Core control logic & messaging
  controlapp/         - Main UI application
    dev/              - Device controllers (energy, doorlock, garage, gate)
    discovery/        - Home selection
    launch/           - Login & startup
    notifications/    - Push notifications
    services/         - Service UI fragments
      av/             - AV services (TV, radio, media, Apple TV, Sonos)
      hvac/           - HVAC UI
      lighting/       - Lighting UI
      shades/         - Shade UI
      fans/           - Fan UI
      security/       - Security UI
      poolspa/        - Pool & spa UI
      entry/          - Entry/doorbell UI
      custom/         - Custom commands & relays
    tiling/           - SmartView video tiling
  core/               - Core networking & protocols
    cloud/            - Cloud API (SavantCloud, SavantRestUtils, SSLHelper)
      resource/       - REST API interfaces (home, user, local, notification)
    cloudrx/          - RxJava cloud services (Retrofit)
      retrofit/       - Retrofit config (SavantAuthenticator)
      services/       - Service interfaces (User, Home, Host)
    connection/       - WebSocket & transport
      ws/             - WebSocket client
      bluetooth/      - Bluetooth/OBEX
    data/             - Data models (SavantUser, ServiceTypes, Entities)
    discovery/        - UDP probe discovery (SavantDiscovery, SavantHome)
    msgpack/          - MessagePack codec
    rest/             - REST config
      ota/            - OTA update API
    state/            - State management
  data/               - Data persistence
  images/             - Image management
  platform/           - Platform abstractions
  trueimage/          - Device auth/unlock
  utils/              - Utility functions
```

---

## Third-Party Dependencies

| Library | Purpose |
|---------|---------|
| OkHttp3 | HTTP client with WebSocket |
| Retrofit2 | REST client with RxJava adapters |
| RxJava2 | Reactive extensions |
| Jackson | JSON processing |
| MessagePack | Binary serialization |
| Dagger | Dependency injection |
| Firebase | Push notifications (FCM) |
| Apache Commons Lang | String/Object utilities |
