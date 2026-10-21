# KELVRA Device Lab — Integration API & Event Contract (v1.0)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/INTEGRATION_CONTRACT.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Version:** 1.0.0-draft
- **Protocol:** HTTP REST, WebSocket (RFC 6455), JSON-RPC / MCP
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Specification Overview

This contract establishes the formal communication interface between **KELVRA Bench** (`:8099`) and **KELVRA Device Lab** (`:8098`). All communication adheres to standard REST semantics, Pydantic v2 JSON models, and standard HTTP status codes.

---

## 2. Authentication & Header Standards

All REST and WebSocket requests dispatched from KELVRA Bench to KELVRA Device Lab must supply standard authorization and tracing headers:

| Header Name | Type | Description | Example |
|:---|:---:|:---|:---|
| `Authorization` | String | Bearer token format (`kdl-<hex>` or translated `kbt-<hex>`) | `Bearer kdl-9f8a7c2b` |
| `X-Request-ID` | String | Correlation UUID for distributed trace observability | `req-550e8400-e29b-41d4-a716` |
| `X-Bench-Agent` | String | Identity of Swarm Agent originating the request | `agent-scout-01` |

---

## 3. REST API Specification

### 3.1 Device Fleet & Discovery

#### `GET /api/devices`
Returns complete inventory of discovered physical and virtual mobile devices.
- **Request:** Empty
- **Response (200 OK):**
```json
{
  "devices": [
    {
      "serial": "8TCABAIFWOZTDICI",
      "platform": "ANDROID_PHYSICAL",
      "state": "AVAILABLE",
      "model": "POCO X6 Pro 5G",
      "os_version": "14",
      "api_level": 34,
      "screen_resolution": "1220x2712",
      "battery_level": 88,
      "temperature_c": 32.4,
      "is_emulator": false
    }
  ],
  "total": 1
}
```

#### `GET /api/devices/{serial}`
Returns detailed specification and real-time state for a specific device.
- **Path Parameter:** `serial` (String)
- **Response (200 OK):** Device detail object.
- **Error (404 Not Found):** `{"detail": "Device not found"}`

---

### 3.2 Single-Writer Leases

#### `POST /api/leases/{serial}/acquire`
Acquires exclusive write access for input injection or test execution.
- **Path Parameter:** `serial` (String)
- **Body:**
```json
{
  "operator_id": "bench-agent-qa",
  "lease_duration_sec": 300
}
```
- **Response (200 OK):**
```json
{
  "status": "ACQUIRED",
  "lease_id": "lease-8f7a6b5c",
  "expires_at": "2026-10-04T07:15:00Z"
}
```
- **Error (409 Conflict):** `{"detail": "Device currently leased by operator 'human-operator-1'"}`

#### `POST /api/leases/{serial}/release`
Releases an active exclusive lease.
- **Body:** `{"lease_id": "lease-8f7a6b5c"}`
- **Response (200 OK):** `{"status": "RELEASED"}`

---

### 3.3 Remote Input & Control

All input operations require an active lease ID passed via header `X-Lease-ID`.

#### `POST /api/devices/{serial}/input/tap`
Simulates a touch tap using normalized coordinates.
- **Body:**
```json
{
  "x": 0.542,
  "y": 0.812
}
```
- **Response (200 OK):** `{"status": "SUCCESS", "action": "tap", "coords": [661, 2202]}`

#### `POST /api/devices/{serial}/input/swipe`
Simulates a directional touch gesture.
- **Body:**
```json
{
  "start_x": 0.5,
  "start_y": 0.8,
  "end_x": 0.5,
  "end_y": 0.2,
  "duration_ms": 300
}
```
- **Response (200 OK):** `{"status": "SUCCESS"}`

#### `POST /api/devices/{serial}/input/key`
Dispatches standard hardware key code.
- **Body:** `{"keycode": 3}` (KEYCODE_HOME)
- **Response (200 OK):** `{"status": "SUCCESS"}`

#### `POST /api/devices/{serial}/input/text`
Types UTF-8 string into focused input field.
- **Body:** `{"text": "Hello Kelvra"}`
- **Response (200 OK):** `{"status": "SUCCESS"}`

---

### 3.4 Live Screen Streaming (WebSocket)

#### `WS /ws/stream/{serial}`
Low-latency JPEG broadcast stream.
- **Subprotocol:** Standard binary WebSocket frames.
- **Payload:** High-resolution JPEG binary frames prefixed with 8-byte frame header (timestamp + frame index).
- **Client Uplink Messages (JSON Text):**
```json
{
  "command": "SET_QUALITY",
  "max_fps": 30,
  "quality": 80,
  "scale": 0.75
}
```

---

### 3.5 Declarative Automation & Workflows

#### `POST /api/automation/execute-inline`
Executes an atomic automation sequence directly against a leased device.
- **Body:**
```json
{
  "serial": "8TCABAIFWOZTDICI",
  "workflow_name": "CompanionAppLaunchVerification",
  "steps": [
    { "action": "LAUNCH_APP", "package": "com.kelvra.companion" },
    { "action": "DELAY", "ms": 1500 },
    { "action": "SCREENSHOT", "name": "app_splash_screen" },
    { "action": "TAP", "x": 0.5, "y": 0.65 },
    { "action": "DELAY", "ms": 500 },
    { "action": "SCREENSHOT", "name": "app_main_screen" }
  ]
}
```
- **Response (200 OK):**
```json
{
  "execution_id": "exec-d4e5f6",
  "status": "COMPLETED",
  "steps_completed": 6,
  "total_steps": 6,
  "artifacts": [
    "artifacts/screenshots/app_splash_screen.jpg",
    "artifacts/screenshots/app_main_screen.jpg"
  ],
  "report_url": "/api/artifacts/exec-d4e5f6-report/download"
}
```

---

## 4. Bench EventBus Publishing Contract

KELVRA Device Lab publishes asynchronous lifecycle events to Bench's EventBus at `POST http://127.0.0.1:8099/api/events`.

### Event Envelope Specification
```json
{
  "event_type": "DEVICE_STATE_CHANGED",
  "source": "kelvra-device-lab",
  "timestamp": "2026-10-04T07:22:15.120Z",
  "correlation_id": "card-4892",
  "payload": {
    "serial": "8TCABAIFWOZTDICI",
    "old_state": "DISCONNECTED",
    "new_state": "AVAILABLE",
    "platform": "ANDROID_PHYSICAL",
    "model": "POCO X6 Pro 5G"
  }
}
```

### Event Catalog
1. `DEVICE_DISCOVERED` — Emitted when a new USB or network device is recognized.
2. `DEVICE_DISCONNECTED` — Emitted when a device is unplugged or enters offline state.
3. `DEVICE_STATE_CHANGED` — Emitted when device transitions (e.g. `AVAILABLE` to `BUSY`).
4. `DEVICE_AUTOMATION_COMPLETED` — Emitted upon workflow finish with status and artifact paths.
5. `DEVICE_THERMAL_ALERT` — Emitted if device battery temperature exceeds 42.0 C.

---

## 5. Backward Compatibility Guarantee

All endpoints in this v1.0 specification are immutable. Any future enhancements (e.g. WebCodecs H.264 streaming) will be introduced via content negotiation or under `/api/v2/` prefixes without breaking v1.0 clients.
