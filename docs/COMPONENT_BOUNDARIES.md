# KELVRA Device Lab — Component Boundaries & Interfaces

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/COMPONENT_BOUNDARIES.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Authority:** Subsystem Modularity & Interface Contracts
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Component Architecture Overview

```mermaid
flowchart TD
    subgraph UI_Layer ["Presentation Layer (static/)"]
        SHELL["App Shell (index.html / app.js)"]
        VIEWER["Canvas Screen Renderer"]
        LOG_VIEW["Virtualized Logcat Viewer"]
        TELE_VIEW["Telemetry & Health Cards"]
    end

    subgraph API_Layer ["API Layer (src/server.py)"]
        REST_API["FastAPI REST Router"]
        WS_HUB["WebSocket Connection Hub"]
        AUTH_GATE["Token Auth & Scope Validator"]
    end

    subgraph Core_Services ["Device Orchestration & Core Services"]
        DEV_MGR["Device Manager (Registry & State Engine)"]
        INPUT_CTRL["Input Controller & Coordinate Transformer"]
        LOGCAT_SVC["Logcat Service (Ring Buffer & Redaction)"]
        TELE_SVC["Device Telemetry Collector"]
        TEST_RUNNER["Autonomous Test Runner"]
        BENCH_BR["Bench Bridge (EventBus Publisher)"]
    end

    subgraph Stream_Engine ["Streaming Subsystem (src/screen_streamer.py)"]
        STREAM_MGR["Stream Session Arbiter"]
        FRAME_GEN["Frame Generator (JPEG / H.264 NAL)"]
        RATE_CTRL["Backpressure & Frame Dropper"]
    end

    subgraph Providers ["Provider Layer (src/providers/)"]
        P_BASE["BaseDeviceProvider (Contract)"]
        P_AND_PHYS["AndroidPhysicalProvider"]
        P_AND_VIRT["AndroidVirtualProvider"]
        P_IOS["ApplePhysicalProvider"]
    end

    subgraph Persistence ["Persistence Layer (src/storage.py)"]
        SQLITE_DB["SQLite State Store (device_lab.db)"]
        EVIDENCE_DIR["Test Evidence Artifacts (/artifacts)"]
    end

    SHELL <-->|REST & WS| REST_API
    VIEWER <-->|Binary Frames| WS_HUB
    LOG_VIEW <-->|JSON Stream| WS_HUB
    REST_API --> AUTH_GATE
    AUTH_GATE --> DEV_MGR
    AUTH_GATE --> TEST_RUNNER
    WS_HUB --> STREAM_MGR
    WS_HUB --> LOGCAT_SVC
    DEV_MGR --> P_BASE
    INPUT_CTRL --> P_BASE
    TELE_SVC --> P_BASE
    STREAM_MGR --> FRAME_GEN
    FRAME_GEN --> P_BASE
    P_BASE <|-- P_AND_PHYS
    P_BASE <|-- P_AND_VIRT
    P_BASE <|-- P_IOS
    TEST_RUNNER --> P_BASE
    TEST_RUNNER --> EVIDENCE_DIR
    DEV_MGR --> SQLITE_DB
    DEV_MGR --> BENCH_BR
```

---

## 2. Detailed Component Specifications

### 2.1 Presentation Shell (`static/index.html`, `app.js`, `style.css`)
- **Primary Role:** Renders the 3-column studio interface, coordinates user interactions, paints video frames to the canvas, and displays live telemetry.
- **Inbound Interfaces:** User mouse clicks, drag gestures, keyboard strokes, tab clicks.
- **Outbound Interfaces:**
  - HTTP `GET /api/devices`: Fetches fleet list.
  - HTTP `POST /api/devices/{serial}/input`: Dispatches keyevents or coordinates.
  - WebSocket `/ws/stream/{serial}`: Consumes binary video frames.
  - WebSocket `/ws/logcat/{serial}`: Consumes filtered JSON log entries.
- **Fault Isolation:** Browser UI thread decoupling; heavy canvas drawing uses `requestAnimationFrame` and `createImageBitmap` to prevent freezing.

---

### 2.2 REST API & WebSocket Controller (`src/server.py`)
- **Primary Role:** ASGI server entry point hosting REST endpoints and multiplexing WebSocket streams.
- **Inbound Interfaces:** HTTP requests on port `:8098`, WebSocket upgrades.
- **Outbound Interfaces:** Dispatches parsed requests to `DeviceManager`, `InputController`, `TestRunner`, and `ScreenStreamer`.
- **Fault Isolation:** Global exception handlers return structured JSON error envelopes (`{ "error": true, "code": "DEVICE_NOT_FOUND", "message": "..." }`) rather than 500 crashes.

---

### 2.3 Device Manager & Registry (`src/device_manager.py`)
- **Primary Role:** Canonical registry maintaining in-memory state, lease reservations, and capability profiles for all discovered devices.
- **Inbound Interfaces:** `scan_devices()`, `get_device(serial)`, `acquire_lease(serial, client_id)`, `release_lease(serial)`.
- **Outbound Interfaces:** Calls concrete `DeviceProvider` methods.
- **State Machine Authority:** Enforces transitions: `DISCOVERED -> CONNECTING -> ONLINE -> BUSY -> OFFLINE`.

---

### 2.4 Device Provider Adapters (`src/providers/`)
- **Primary Role:** Encapsulates all platform-specific command construction, socket connections, and hardware diagnostics.
- **Contract Defined in:** [`docs/DEVICE_PROVIDER_CONTRACT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_PROVIDER_CONTRACT.md).
- **Implementations:**
  - `AndroidPhysicalProvider`: Interfaces with physical Android devices via ADB server client.
  - `AndroidVirtualProvider`: Manages AVD instances via `emulator` and `avdmanager` CLI.
  - `ApplePhysicalProvider`: Interfaces with iOS devices via `pymobiledevice3`.
- **Fault Isolation:** Platform crashes or device unplugs trigger provider-level exceptions caught by `DeviceManager`; sibling providers remain completely unaffected.

---

### 2.5 Streaming Subsystem (`src/screen_streamer.py`)
- **Primary Role:** Manages screen capture loops, video encoding, backpressure monitoring, and binary frame broadcasting.
- **Inbound Interfaces:** `start_stream(serial, websocket)`, `stop_stream(serial)`.
- **Backpressure Handling:** Drops incoming frames if the WebSocket send buffer exceeds 2 queued frames, preventing buffer bloat and lag.

---

### 2.6 Input Controller (`src/input_controller.py`)
- **Primary Role:** Translates normalized viewport coordinates `(0.0 - 1.0)` into physical device display pixels, applies rotation offsets, and dispatches gestures.
- **Security Role:** Sanitizes text strings against shell metacharacters before executing `input text`.

---

### 2.7 Logcat Streaming Service (`src/logcat_service.py`)
- **Primary Role:** Spawns asynchronous `adb logcat` processes, consumes stdout lines, stores lines in a circular ring buffer (capacity: 5,000 lines), redacts secrets, and streams to connected WebSockets.
- **Process Cleanup:** Process termination is guaranteed via `process.terminate()` and `process.kill()` when all clients disconnect.

---

### 2.8 Device Telemetry Collector (`src/device_telemetry.py`)
- **Primary Role:** Periodic background poller (3-second interval) extracting CPU load, memory utilization, storage availability, battery percentage, charging state, and temperature.
- **Alert Generation:** Dispatches immediate alert events if temperature > 42°C or battery < 15%.

---

### 2.9 Autonomous Test Runner (`src/test_runner.py`)
- **Primary Role:** Executes automated verification pipelines: installs APK builds, verifies launch, checks process state, captures screenshot evidence, and packages execution reports.

---

### 2.10 Bench Bridge (`src/bench_bridge.py`)
- **Primary Role:** Publishes Device Lab events (device connected, test completed, thermal alert) to KELVRA Bench's EventBus (`/api/events`) over HTTP.
- **Decoupling Guarantee:** Operates strictly fire-and-forget. If Bench is not running on port `:8099`, the bridge logs a debug notice and Device Lab continues operating autonomously.
