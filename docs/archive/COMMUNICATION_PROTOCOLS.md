# KELVRA Device Lab — Communication Protocols & API Specifications

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/COMMUNICATION_PROTOCOLS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Authority:** Local Interfaces & Network Transport Architecture
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Transport Mechanism Evaluation

| Communication Channel | Selected Protocol | Format | Justification |
|---|---|---|---|
| **UI to Backend (Control & State)** | HTTP REST (JSON) | UTF-8 JSON | Standard request-response for device listing, metadata queries, and test execution. |
| **UI to Backend (Video Streaming)** | Binary WebSocket | Binary Chunks (JPEG / H.264) | Full-duplex persistent socket; eliminates HTTP polling overhead; allows binary frame delivery. |
| **UI to Backend (Logcat Stream)** | Text WebSocket | Structured JSON Lines | High-velocity streaming with server-side filtering and secret redaction. |
| **UI to Backend (Input Teleoperation)** | WebSocket or HTTP POST | JSON Payloads | Sub-15ms touch coordinate and keyevent dispatch. |
| **Backend to ADB Server** | Local TCP Socket (`127.0.0.1:5037`) | Binary ADB Protocol | Bypasses `subprocess.run` process spawning cost; ultra-fast device polling. |
| **Backend to Managed Workers** | Asynchronous Process Pipes | stdio / stderr byte streams | Safe, non-blocking asynchronous stream consumption. |
| **Backend to Persistence** | Direct In-Process SQLite API | C-level binary bindings | Sub-millisecond queries; zero network/IPC overhead. |
| **Backend to KELVRA Bench** | HTTP POST to `/api/events` | JSON Swarm Events | Decoupled fire-and-forget event bridge. |

---

## 2. REST API Endpoints Specification

All REST endpoints return standardized JSON response envelopes:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-10-04T00:50:00Z"
}
```

### 2.1 Fleet & Device Endpoints
- `GET /api/devices`: List all discovered devices and their live status.
- `GET /api/devices/{serial}`: Retrieve detailed hardware specs and telemetry for a specific device.
- `POST /api/devices/scan`: Trigger an immediate fleet discovery scan.
- `POST /api/devices/{serial}/lease`: Acquire exclusive teleoperation lease (`client_id`, `ttl_seconds`).
- `DELETE /api/devices/{serial}/lease`: Release teleoperation lease.

### 2.2 Teleoperation & Input Endpoints
- `POST /api/devices/{serial}/input/tap`: Inject touch tap (`x: float`, `y: float`).
- `POST /api/devices/{serial}/input/swipe`: Inject touch swipe (`x1`, `y1`, `x2`, `y2`, `duration_ms`).
- `POST /api/devices/{serial}/input/key`: Inject hardware keycode (`keycode: int`).
- `POST /api/devices/{serial}/input/text`: Inject text string (`text: str`).

### 2.3 Application & Test Runner Endpoints
- `POST /api/devices/{serial}/apps/install`: Install APK (`file_path: str` or multipart file).
- `POST /api/devices/{serial}/apps/launch`: Launch application package (`package_name: str`).
- `POST /api/devices/{serial}/apps/stop`: Force stop application package (`package_name: str`).
- `POST /api/devices/{serial}/screenshot`: Capture uncompressed PNG screenshot. Returns file path and base64 preview.
- `POST /api/devices/{serial}/tests/run`: Execute automated smoke test suite. Returns structured JSON report.

---

## 3. WebSocket Channel Specifications

### 3.1 Video Stream Channel (`/ws/stream/{serial}`)
- **Protocol:** Binary WebSocket frame transport.
- **Client Handshake:**
  - Client connects: `ws://127.0.0.1:8098/ws/stream/{serial}?client_id=dev-1&quality=high`
  - Server confirms with JSON handshake header:
    ```json
    {
      "type": "STREAM_INITIALIZED",
      "codec": "jpeg",
      "width": 1080,
      "height": 2400,
      "fps": 30
    }
    ```
- **Frame Transmission:**
  - Each video frame is transmitted as a raw binary WebSocket message containing image bytes (JPEG / H.264 NAL).
  - The client draws binary chunks directly to the canvas using `createImageBitmap(blob)`.
- **Client Upstream Messages:**
  - `{"type": "PING"}` / `{"type": "PONG"}` (Heartbeat every 10s).
  - `{"type": "SET_QUALITY", "quality": "medium" | "low"}`.

### 3.2 Logcat Stream Channel (`/ws/logcat/{serial}`)
- **Protocol:** Text WebSocket transmitting JSON log line packets.
- **Packet Structure:**
  ```json
  {
    "timestamp": "10-04 00:50:12.345",
    "pid": 12450,
    "tid": 12480,
    "level": "I",
    "tag": "KelvraMobile",
    "message": "LocalSpeechRecognizer initialized offline successfully."
  }
  ```
- **Client Upstream Filters:**
  - `{"type": "SET_FILTER", "tag": "KelvraMobile", "level": "W", "search": "error"}`.

---

## 4. Error Propagation & Timeout Standards

- **Standardized Error Envelope:**
  ```json
  {
    "success": false,
    "data": null,
    "error": {
      "code": "DEVICE_BUSY",
      "message": "Device 8TCABAIFWOZTDICI is currently leased by client 'agent-qa-1'.",
      "details": { "leased_until": "2026-10-04T00:52:00Z" }
    },
    "timestamp": "2026-10-04T00:50:00Z"
  }
  ```
- **Standard Timeouts:**
  - Device info query: `3.0s` timeout.
  - Touch/key injection: `1.5s` timeout.
  - Screenshot capture: `5.0s` timeout.
  - APK installation: `45.0s` timeout.
  - AVD emulator boot: `60.0s` timeout.
  - WebSocket heartbeat: `15.0s` inactivity timeout before socket teardown.
