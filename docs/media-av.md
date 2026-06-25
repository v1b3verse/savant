# Media & AV Control

[< Back to Overview](../SAVANT.md) | [Service Control](service-control.md)

---

## Media Commands

Sent via URI: `media/{component}/{command}`

### Transport Commands

`Play`, `Pause`, `Stop`, `FastForward`, `Rewind`, `SkipUp`, `SkipDown`, `TogglePause`, `SlowPlayForward`, `SlowPlayReverse`, `FastPlayForward`, `FastPlayReverse`

### TV/Radio Commands

`SetChannel`, `IncrementChannel`, `DecrementChannel`, `SetRadioFrequency`, `IncrementRadioFrequency`, `DecrementRadioFrequency`, `IncrementPreset`, `DecrementPreset`, `SelectPreset`

### OSD Navigation

`OSDCursorUp`, `OSDCursorDown`, `OSDCursorLeft`, `OSDCursorRight`, `OSDSelect`, `OSDCursorSelect`, `OSDPageUp`, `OSDPageDown`, `OSDDayUp`, `OSDDayDown`

### Disc Control

`TrayOpen`, `TrayClose`, `TrayToggle`, `Eject`, `DiskUp`, `DiskDown`, `SelectDisk`

### Menu/Info

`Menu`, `Guide`, `Info`, `Title`, `Home`, `Return`, `Exit`, `Display`, `Setup`, `Search`, `List`, `Favorite`, `LiveTV`, `MyDVR`

### Color Buttons

`RedButton`, `GreenButton`, `BlueButton`, `YellowButton`

### Misc

`Record`, `RecordPause`, `ThumbsUp`, `ThumbsDown`, `PictureInPictureOn`, `PictureInPictureOff`, `PictureInPictureSwap`, `Zoom`, `ToggleZoom`, `Subtitle`, `Audio`, `Angle`

Volume is controlled at room level via state set (not media commands).

### Full Command Alias Map

See `assets/command_aliases.json` for the complete mapping of command names to display labels.

---

## Music Query Protocol

Sent via URI: `music/{component}/{logicalComponent}/{serviceId}/{query}`

### Request Format

```json
{
  "Component Identifier": "Media Server",
  "RequestingUID": "ACE6FE7C-...",
  "Logical Component": "Player_A",
  "Query": "BrowseTitles",
  "Query arguments": {
    "isIOS": true,
    "limit": "50",
    "offset": "0",
    "PlayKey": "Playlist",
    "filters": ["SetMusicFilter Playlist=c089f1f4-..."],
    "command": "EditPlaylist",
    "guid": "c089f1f4-..."
  },
  "version": "1"
}
```

### Query Types

- `BrowseTitles` — Browse music library
- `ClarifyTitleIntent` — Resolve ambiguous selection
- `Back` — Navigate back in browse hierarchy

### Play Keys

`Title`, `Artist`, `Album`, `Playlist`, `Genre`

---

## Supported AV Services

| Service ID | Name | UI Fragment |
|-----------|------|-------------|
| `SVC_AV_TV` | Cable TV | TVTabHostFragment |
| `SVC_AV_SATELLITETV` | Satellite TV | TVTabHostFragment |
| `SVC_AV_SMARTTV` | Smart TV | TVTabHostFragment |
| `SVC_AV_DVD` | DVD | DVDTabHostFragment |
| `SVC_AV_ENHANCEDDVD` | Blu-ray | DVDTabHostFragment |
| `SVC_AV_CD` | CD | CDTabHostFragment |
| `SVC_AV_FMRADIO` | FM Radio | RadioTabHostFragment |
| `SVC_AV_AMRADIO` | AM Radio | RadioTabHostFragment |
| `SVC_AV_SATELLITERADIO` | Satellite Radio | RadioTabHostFragment |
| `SVC_AV_MULTIBANDRADIO` | Multi-band Radio | RadioTabHostFragment |
| `SVC_AV_APPLEREMOTEMEDIASERVER` | Apple TV | AppleTVControlFragment |
| `SVC_AV_SONOS` | Sonos | SonosFragment |
| `SVC_AV_SAVANTMUSIC` | Savant Music | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_SPOTIFY` | Spotify | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_PANDORA` | Pandora | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_TIDAL` | Tidal | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_TUNEIN` | TuneIn | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_SAVANTMEDIAAUDIO_RADIO_SIRIUS` | SiriusXM | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_KSCAPE` | Kaleidescape | SMSFragment |
| `SVC_AV_LIVEMEDIAQUERY_XBMC` | XBMC/Kodi | ExternalMediaTabHostFragment |
| `SVC_AV_EXTERNALMEDIASERVER` | Media Server | ExternalMediaTabHostFragment |
| `SVC_AV_SURVEILLANCESYSTEM` | Surveillance | SurveillanceTabHostFragment |
| `SVC_AV_HDMI` | HDMI | StaticInputFragment |
| `SVC_AV_GAME` | Game | StaticInputFragment |
| `SVC_INFO_SMARTVIEWTILING` | Video Tiling | TilingFragment |

---

## Component Data Model

```json
{
  "id": "jkvbmAMVTEGJSDCu8Er7tA",
  "componentType": 2,
  "name": "Apple TV",
  "deviceClass": "Media_server",
  "manufacturer": "Apple",
  "model": "AppleTV",
  "rooms": [{"name": "Living Room", "id": "bgcZLbE0R9yTYZ77CEgYuA"}],
  "controllerId": "3fYRAuGvS9yXzVS0caAclQ",
  "codesetId": "N2615",
  "ueiDeviceClass": "N",
  "ueiKeys": "860001768fc00000...",
  "connections": [{
    "id": "jqQxv4dCSOOb0tHWTWOwFw",
    "srcComponent": "jkvbmAMVTEGJSDCu8Er7tA",
    "dstComponent": "GfqTd1kyQES0UpIzWm9jZg",
    "input": "HDMI3",
    "type": "audiovideo"
  }],
  "typeId": "appletv",
  "configured": true,
  "initialized": true,
  "softwareInfo": { "version": {} },
  "capabilities": {},
  "discoveryInfo": {}
}
```

### Service-to-Resource Mapping

Each service type maps to a resource type (see `assets/serviceToResource.json`):

| Service | Resource |
|---------|----------|
| `SVC_AV_TV` | `AV_TV_SOURCE` |
| `SVC_AV_SATELLITETV` | `AV_SATELLITETV_SOURCE` |
| `SVC_AV_APPLEREMOTEMEDIASERVER` | `AV_APPLEREMOTEMEDIASERVER_SOURCE` |
| `SVC_ENV_LIGHTING` | `ENV_LIGHTINGCONTROLLER_SOURCE` |
| `SVC_ENV_HVAC` | `ENV_HVACCONTROLLER_SOURCE` |
| `SVC_ENV_SHADE` | `ENV_SHADECONTROLLER_SOURCE` |
| `SVC_ENV_POOLANDSPA` | `ENV_POOLANDSPACONTROLLER_SOURCE` |
