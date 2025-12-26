# Equation Virtus AC API

Unofficial API documentation for Equation Virtus Air Conditioners (sold at Leroy Merlin), reverse-engineered from the Enki mobile app.

**Important**: This API is completely different from the Firebase-based API used by Equation radiators. The Virtus AC uses Adeo's cloud gateway with Keycloak OAuth2 authentication.

## Device Information

- **Model**: AD-WMACKC-U1
- **Node Type**: ESDK
- **Icon**: air_conditioners

## Authentication

The API uses Keycloak OAuth2 authentication:

- **Auth Server**: `https://keycloak-prod.iot.leroymerlin.fr/realms/enki`
- **Client ID**: `enki-front`
- **Token Type**: Bearer JWT

### Token Claims

```json
{
  "iss": "https://keycloak-prod.iot.leroymerlin.fr/realms/enki",
  "azp": "enki-front",
  "realm_access": {
    "roles": ["default-roles-enki", "offline_access", "uma_authorization"]
  },
  "scope": "email profile"
}
```

## API Base URL

```
https://enki.api.devportal.adeo.cloud
```

## Required Headers

```http
x-gateway-apikey: Nntj37xS5lih1qqFy8SbyHWKG5NEhSCm
authorization: Bearer {JWT_TOKEN}
homeid: {HOME_ID}
content-type: application/json; charset=utf-8
```

## Endpoints

### Get Device State

```http
GET /api-enki-equation-airco-prod/v1/equation-airco/{node_id}/check-airconditioner-state
```

**Response:**

```json
{
  "nodeId": "69472cb0293e2b3d8df6710e",
  "homeId": "6851b6c2e6a96d42eae600a2",
  "lastReportedDate": "2025-12-26T15:01:34.192Z",
  "lastReportedValue": {
    "targetTemperature": 24.0,
    "currentTemperature": 14.0,
    "operatingMode": "HEAT",
    "power": "ON",
    "selfCleanMode": false,
    "frostProtectionMode": false,
    "defrostMode": false,
    "healthMode": false,
    "quietMode": false,
    "sleepMode": false,
    "fanSpeed": "AUTO",
    "swingOrientation": {
      "horizontal": "AUTO",
      "vertical": "AUTO"
    }
  }
}
```

### Set Device State

```http
POST /api-enki-equation-airco-prod/v1/equation-airco/{node_id}/change-airconditioner-state
```

**Request Body:**

```json
{
  "targetTemperature": 24.0,
  "currentTemperature": null,
  "operatingMode": "COOL",
  "power": "ON",
  "fanSpeed": "AUTO",
  "frostProtectionMode": false,
  "selfCleanMode": false,
  "healthMode": false,
  "quietMode": false,
  "sleepMode": false,
  "swingOrientation": null
}
```

**Response:** `202 Accepted` (empty body)

**Note:** Only include fields you want to change. Set unchanged fields to `null`.

### Check Device Errors

```http
GET /api-enki-equation-airco-prod/v1/equation-airco/{node_id}/check-airconditioner-error
```

**Response:**

```json
{
  "nodeId": "69472cb0293e2b3d8df6710e",
  "homeId": "6851b6c2e6a96d42eae600a2",
  "lastReportedDate": "2025-12-20T23:11:07.630Z",
  "lastReportedValue": "NONE"
}
```

### Get Node Information

```http
GET /api-enki-node-agg-prod/v1/nodes/{node_id}
```

**Note:** Uses different API key: `UBb0Kv6xXpG6bOvD8VZ9A63uxqQ4G1A3`

**Response:**

```json
{
  "id": "69472cb0293e2b3d8df6710e",
  "type": "ESDK",
  "pairingState": "PAIRING_DONE",
  "icon": "air_conditioners",
  "deviceId": "6579df71dd602641561a4d59",
  "homeId": "6851b6c2e6a96d42eae600a2",
  "creationDate": "2025-12-20T23:09:36.271Z",
  "updateDate": "2025-12-20T23:10:02.055Z",
  "label": "AC",
  "factoryId": "34B4726B1713",
  "modelNumber": "AD-WMACKC-U1"
}
```

### Get Temperature History

```http
GET /api-enki-temperature-humidity-sensor-prod/v1/sensors/bff/nodes/{node_id}/specific-granularity?stateType=TEMPERATURE&startDate={ISO_DATE}&timePeriod={PERIOD}
```

**Query Parameters:**
- `stateType`: `TEMPERATURE`
- `startDate`: ISO 8601 format (e.g., `2025-12-26T00:00:00.000Z`)
- `timePeriod`: `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`

## Enums and Valid Values

### Power

| Value | Description |
|-------|-------------|
| `ON`  | Power on    |
| `OFF` | Power off   |

### Operating Mode

| Value  | Description          |
|--------|----------------------|
| `COOL` | Cooling mode         |
| `HEAT` | Heating mode         |
| `FAN`  | Fan only mode        |
| `DRY`  | Dehumidify mode      |
| `AUTO` | Automatic mode       |

### Fan Speed

| Value    | Description      |
|----------|------------------|
| `LOW`    | Low fan speed    |
| `MEDIUM` | Medium fan speed |
| `HIGH`   | High fan speed   |
| `AUTO`   | Automatic        |

### Swing Orientation

```json
{
  "horizontal": "AUTO",
  "vertical": "AUTO"
}
```

Possible values for both `horizontal` and `vertical`:
- `AUTO` - Automatic swing
- Other values TBD (not captured during testing)

### Boolean Modes

| Mode | Description |
|------|-------------|
| `healthMode` | Health/ionizer mode |
| `frostProtectionMode` | Frost protection |
| `selfCleanMode` | Self cleaning |
| `quietMode` | Quiet/silent operation |
| `sleepMode` | Sleep mode |
| `defrostMode` | Defrost (read-only) |

## Other Useful Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api-enki-mobile-bff-prod/v1/dashboard/homes/{home_id}?hasGroups=true` | Dashboard with all devices |
| `/api-enki-home-prod/v1/homes/{home_id}` | Home details |
| `/api-enki-room-prod/v1/rooms?homeId={home_id}&nodeId={node_id}` | Room assignments |
| `/api-enki-referentiel-agg-prod/v1/devices/{device_id}?version=2.19.0` | Device reference data |
| `/api-enki-schedule-prod/v1/devices/{device_id}/is-eligible` | Schedule eligibility |
| `/api-enki-programmer-prod/v1/timers/{node_id}?homeId={home_id}` | Timers |
| `/api-enki-programmer-prod/v1/programmers?nodeId={node_id}&homeId={home_id}` | Programmers/schedules |

## API Keys by Service

| Service | API Key |
|---------|---------|
| `equation-airco` | `Nntj37xS5lih1qqFy8SbyHWKG5NEhSCm` |
| `node-agg` | `UBb0Kv6xXpG6bOvD8VZ9A63uxqQ4G1A3` |

## Notes

1. **Temperature Range**: The AC supports temperatures from around 16°C to 30°C (exact range TBD).

2. **State Updates**: After sending a command, poll the `check-airconditioner-state` endpoint to verify the change was applied.

3. **Token Refresh**: JWT tokens expire after ~2 hours. Use standard Keycloak refresh token flow.

4. **Rate Limiting**: Unknown, but reasonable polling intervals (e.g., 30-60 seconds) recommended.

## Disclaimer

This documentation is provided for educational purposes and personal home automation projects. Use at your own risk. This project is not affiliated with Equation, Leroy Merlin, or Adeo.

## License

MIT License
