# KELVRA Device Lab — Comprehensive Technical Knowledge & Architectural Reference (DEVICE_LAB_KNOWLEDGE.md)

## 1. Product Definition & Vision

### 1.1 Mission & Purpose
KELVRA Device Lab is an autonomous mobile device teleoperation, real-time screen streaming, fleet management, and automated testing engine designed for the KELVRA ecosystem. It provides direct hardware and virtual emulator supervision, low-latency remote interaction, and autonomous agent orchestration.

### 1.2 Target Users & Personas
1. **Autonomous AI Agents (KELVRA Bench Swarm):** Direct teleoperation via Model Context Protocol (MCP) tools for automated mobile regression, app installation, gesture automation, and error diagnostics.
2. **Human Developers & QA Engineers:** Direct interactive device control via the editorial dark Control Studio UI at http://127.0.0.1:8098/ for manual debugging, log analysis, and macro recording.
3. **Continuous Integration Runners:** Headless execution of automated multi-step verification workflows with persistent artifact generation (screenshots, videos, scrubbed logcat, execution reports).

### 1.3 Core Product Workflows
- **Fleet Discovery & Inventory:** Instant enumeration of attached USB physical Android devices, wireless ADB targets, Android Virtual Devices (AVDs), and Apple iOS devices via usbmuxd.
- **Low-Latency Screen Teleoperation:** Real-time aspect-ratio-locked screen streaming over binary/JSON WebSockets with single-writer leased touch/drag/text injection.
- **Virtual Device Supervisor:** Automated discovery of Android SDK tools (vdmanager, emulator), headerless INI profile parsing, headless background boot, and clean process termination.
- **Observability & Log Streaming:** Circular-buffer logcat capture with automated real-time regex sanitization of credentials, passwords, Bearer tokens, and secrets.
- **Workflow Automation:** Declarative 10-step DSL workflow execution with step-level timeouts, coordinate validation, and structured reporting.
- **Bench Hybrid Integration:** Decoupled out-of-process client bridge connecting KELVRA Bench (:8099) to Device Lab (:8098) with 8 dedicated MCP tools.

### 1.4 Explicit Exclusions & Hard Boundaries
- **Zero Raw Unicode Emojis:** Absolute prohibition of raw Unicode emojis in all code, commits, logs, toasts, and UI layouts. Authentic vector SVGs and flat indicators only.
- **Workspace Boundary:** All Device Lab development is strictly confined to Kelvra/KELVRA Device Lab/ (and approved integration bridge files in kelvra-bench/).
- **Zero Personal Data Extraction:** No extraction or harvesting of SMS, contacts, personal documents, device accounts, or camera streams.
- **Platform Honesty:** On Windows host workstations, iOS devices operate exclusively in honest Inspection Mode (metadata, pairing status, UDID). Streaming and touch injection are explicitly disabled without simulated or fake interfaces.
- **GPLv3 Licensing Isolation:** External tools (pymobiledevice3, etc.) are invoked strictly via isolated CLI subprocesses; zero in-process Python imports to preserve permissive licensing.

---

## 2. Architectural Foundations & 8-Layer Stack

KELVRA Device Lab follows an 8-layer decoupled architecture:
1. **Presentation Layer (Web Control Studio):** Vanilla ES6 SPA (static/index.html, static/style.css, static/app.js) rendering editorial dark theme, responsive navigation, device inventory, real-time canvas streaming, touch controls, and diagnostic panels.
2. **API & Dispatch Layer (src/server.py):** FastAPI application on port :8098 exposing REST endpoints, WebSocket streaming channels, static file serving, and CORS middleware.
3. **Session & Security Layer (src/session_manager.py, src/security/auth.py):** Enforces Single-Writer Lease exclusivity, session token validation (kdl-*), heartbeat renewals, and constant-time token verification (kbt-*).
4. **Automation & Observability Layer (src/automation/, src/diagnostics/):** Declarative workflow executor, screenshot capturer, MP4 recorder, circular logcat service, and diagnostics aggregator.
5. **Storage & Vault Layer (src/artifacts/artifact_manager.py):** Partitioned directory storage (screenshots/, 
ecordings/, logs/, 
eports/), SHA-256 deduplication, atomic catalog indexing (catalog.json), and 500 MB LRU quota eviction.
6. **Streaming & Input Layer (src/streaming/, src/teleop/):** WebSocket screen streamer with backpressure frame dropping, 30 FPS clamping, aspect ratio letterboxing, and normalized coordinate touch scaling.
7. **Domain & Registry Layer (src/domain/, src/registry/):** Strongly typed domain models (Device, DevicePlatform, DeviceLifecycleState), thread-safe DeviceRegistry with listener events.
8. **Hardware & Virtual Providers (src/providers/):** AndroidDeviceProvider (physical ADB), AvdManager (virtual emulator supervisor), AppleDeviceProvider (TCP 27015 usbmuxd inspector), and MockDeviceProvider (isolated test harness).

---

## 3. Technology Stack & Runtime Topology

### 3.1 Technology Choices
- **Backend Framework:** Python 3.10+ with FastAPI and Uvicorn ASGI server.
- **Data Validation & Modeling:** Pydantic v2 data models with strict type validation.
- **Real-Time Streaming:** RFC 6455 WebSockets with JSON control framing and binary JPEG payloads.
- **Image Processing:** Pillow (PIL) for synthetic frames, aspect ratio letterboxing, and format conversion.
- **Frontend Architecture:** Vanilla ES6 JavaScript, HTML5 Canvas, modern Vanilla CSS with CSS custom properties (zero NPM/bundler dependencies).
- **Process Supervision:** Standard Python syncio.subprocess and subprocess.Popen with shell=False, list arguments, 64 KB output bounding, and timeouts.
- **Deployment:** Linux systemd unit (kelvra-device-lab.service), Windows Service wrapper via NSSM (install_windows_service.bat), and standalone launcher suite (
un_standalone.py, .bat, .sh).

### 3.2 Network Topology & Ports
- **:8098:** Dedicated KELVRA Device Lab HTTP REST API, WebSocket streaming server, and SPA static host.
- **:8099:** KELVRA Bench desktop/web runtime host.
- **127.0.0.1:27015:** Apple Mobile Device Service (usbmuxd) TCP daemon for iOS device discovery.
- **5037:** Standard Android Debug Bridge (db) server port.
- **5554-5584:** Android Emulator console and ADB ports.

---

## 4. Design System & UI Specifications

### 4.1 Design Philosophy & Aesthetic Identity
Device Lab adheres to the Anthropic editorial dark design system established in KELVRA Bench:
- **Background Base:** --bg-base (#191918 / #1E1E1C)
- **Panel Surface:** --bg-panel (#1A1918 / #262624)
- **Card Surface:** --bg-card (#222120 / #2C2B28)
- **Card Hover:** --bg-card-hover (#282725 / #33322E)
- **Accent Primary (Terra Cotta / Coral):** --accent (#D97757 / #CC785C)
- **Accent Light:** --accent-light (#E0886C)
- **Status Green (Complete / Online):** #57A373 / #788C5D
- **Status Amber (Warning / Reconnecting):** #E09F3E / #D4A373
- **Status Red (Error / Disconnected):** #D9534F
- **Typography:** Lora (headings/editorial), Inter (body/UI), JetBrains Mono (code/metrics/timestamps).

### 4.2 Control Studio Screen Hierarchy
1. #/overview — Fleet Overview (live device counts, active leases, subsystem status, activity ledger).
2. #/devices — Device Inventory (grid and table views, platform and state filtering, search, device detail drawer).
3. #/devices/studio — Remote Control Studio (aspect-ratio-locked screen canvas, coordinate-normalized touch injection, hardware nav keys: Back/Home/Recents/Power/Volume, quality/FPS selectors, stream HUD).
4. #/virtual — Virtual Devices Hub (AVD inventory, system image specs, one-click headless boot/kill).
5. #/sessions — Live Sessions (active single-writer leases, client IDs, remaining TTL, force revoke).
6. #/automation — Automation Console (10-step DSL workflow templates: Smoke Test, Settings, Gesture; live step-by-step progress tracker, abort control, execution history).
7. #/diagnostics — Logs & Diagnostics (circular logcat console, level filter, credential scrubbing, export to JSON/TXT, deep system health meters).
8. #/settings — Service Configuration (host/port bindings, timeouts, auth mode, storage quotas).

---

## 5. Device Domain Model & Lifecycle State Machine

### 5.1 10-State Lifecycle FSM
Devices transition deterministically across 10 lifecycle states:
DISCOVERED -> UNAUTHORIZED -> AVAILABLE -> CONNECTING -> CONNECTED -> BUSY -> UNAVAILABLE -> DISCONNECTING -> DISCONNECTED -> ERROR.
- AVAILABLE: Device is connected, authorized, and idle (ready for lease or stream).
- BUSY: Device is currently held under an exclusive single-writer operator lease.
- UNAUTHORIZED: Device is attached via USB but requires RSA key fingerprint confirmation on screen.

### 5.2 Device Data Contract
`python
class Device(BaseModel):
    id: str                        # e.g., 'android:emulator-5554'
    serial: str                    # Hardware or emulator serial
    provider_id: str               # Provider identifier ('android_physical', 'avd_provider', 'apple_provider')
    platform: DevicePlatform       # ANDROID_PHYSICAL, ANDROID_VIRTUAL, APPLE_PHYSICAL, APPLE_VIRTUAL
    device_type: DeviceType        # PHYSICAL, VIRTUAL
    display_name: str              # User-friendly name ('Pixel 7 Pro')
    manufacturer: Optional[str]    # 'Google', 'Samsung', 'Apple'
    model: Optional[str]           # Hardware model string
    state: DeviceLifecycleState    # Active state in 10-state FSM
    capabilities: List[DeviceCapability]
    display_width: Optional[int]   # Physical display resolution width
    display_height: Optional[int]  # Physical display resolution height
    display_density: Optional[int] # Screen density (DPI)
    battery_level: Optional[int]   # Battery percentage [0, 100]
    is_charging: Optional[bool]
    ip_address: Optional[str]
    connection_transport: ConnectionTransport # USB, WIFI, EMULATOR_PIPE
    last_seen: datetime
`

---

## 6. Single-Writer Lease & Teleoperation Engine

### 6.1 Lease Exclusivity Contract
- **Unlimited Viewers:** Any number of operators, dashboards, or agents may concurrently observe the live screen stream.
- **Single-Writer Mutex:** Exactly one operator or agent may hold an active DeviceLease on a device at any moment.
- **Lease Duration & Heartbeat:** Default duration is 300 seconds (configurable). Active holders renew via heartbeat pulses. If an operator disconnects, the lease automatically expires and the device returns to AVAILABLE.
- **Collision Handling:** A secondary client requesting a lease on a leased device receives HTTP 409 Conflict with LeaseConflictError containing the holder identity and remaining TTL.

### 6.2 Input Coordinate Normalization
- Clients send normalized touch coordinates (x, y) in the floating-point range [0.0, 1.0].
- The InputController scales coordinates to physical device pixels:
  	arget_x = int(norm_x * display_width)
  	arget_y = int(norm_y * display_height)
- Out-of-bounds coordinates (x < 0.0 or x > 1.0) are strictly rejected with HTTP 422 before dispatching to ADB.
- Touch events include down, move, up (simulated via db shell input tap x y and db shell input swipe x1 y1 x2 y2 duration_ms).
- Key events include standard Android keycodes (KEYCODE_BACK = 4, KEYCODE_HOME = 3, KEYCODE_APP_SWITCH = 187, KEYCODE_POWER = 26, KEYCODE_VOLUME_UP = 24, KEYCODE_VOLUME_DOWN = 25).

---

## 7. Screen Streaming Subsystem (Dual-Pipeline Architecture)

### 7.1 Baseline MJPEG Streaming Pipeline
- **Protocol:** MJPEG frames delivered over WebSocket (`/ws/devices/{serial}/stream`).
- **Framing:** JSON metadata frame header followed by binary JPEG payload or base64-encoded payload.
- **Backpressure Protection:** The streaming capture loop evaluates client connection write buffers. If a viewer cannot consume frames in real time, excess frames are non-blocking dropped rather than queued, preserving low latency (< 50 ms loopback).
- **Idle Throttling:** When zero viewers are connected to an active stream session, the capture loop throttles to 150 ms intervals, bypassing `adb exec-out screencap` subprocess execution to eliminate CPU thrashing.
- **Dynamic Clamping:** Clamped to a maximum of 30 FPS for JPEG streaming; configurable quality [30, 95] and resolution downscaling [320, 1920].

### 7.2 Low-Latency WebCodecs H.264 Pipeline (`scrcpy_streamer.py`)
- **Pipeline Architecture:** Leverages `scrcpy-server.jar` execution via `adb forward/reverse` socket tunneling or deterministic synthetic Annex-B framing for testing.
- **Annex-B NAL Unit Parsing (`H264Parser`):** Splits incoming raw H.264 bitstreams on 3-byte (`0x000001`) and 4-byte (`0x00000001`) start codes into discrete NAL packets.
- **Parameter Set Caching:** Extracts and persistently caches Sequence Parameter Set (SPS, NAL unit type 7) and Picture Parameter Set (PPS, NAL unit type 8). When new WebSocket clients connect mid-stream, cached SPS/PPS packets are prepended immediately before the next IDR/slice frame, guaranteeing instant `VideoDecoder` configuration without waiting for keyframe cycles.
- **Binary WebSocket Delivery:** Binary transport over `/ws/devices/{serial}/stream/h264`. Frames include a 1-byte framing header: `0x01` indicates initialization parameters (SPS/PPS), `0x02` indicates regular video slice frames.
- **Client WebCodecs Worker Architecture (`static/decoder_worker.js`):** Offloads hardware-accelerated H.264 decoding to an `OffscreenCanvas` inside a dedicated Web Worker thread. Prevents main UI thread blocking, enabling sustained 30-60 FPS playback with < 35 ms end-to-end glass-to-glass latency.
- **Graceful Fallback:** Frontend client feature-detects `window.VideoDecoder`. If WebCodecs or `OffscreenCanvas` is unavailable in the host browser, the studio client automatically falls back to the baseline MJPEG stream.

### 7.3 Stream Telemetry & Session Lifecycle
- REST management endpoints:
  - `POST /api/devices/{id}/stream/h264/start`: Initiates session and returns port/encoder parameters.
  - `POST /api/devices/{id}/stream/h264/stop`: Terminates session and cleans up adb forwards and sockets.
  - `GET /api/devices/{id}/stream/h264/status`: Reports active status, connected viewers, rolling FPS, total frames transmitted, total bytes, and SPS/PPS readiness.
- Rolling telemetry: Windowed 10-second FPS estimation computed dynamically on broadcast.
- Lifespan management: Integrated directly into FastAPI shutdown hooks (`await scrcpy_streamer.stop_all()`), ensuring zero orphaned socket forwards or lingering capture processes.

---

## 8. Android Virtual Device (AVD) Supervisor

### 8.1 Toolchain Discovery & INI Parsing
- Scans ANDROID_HOME, ANDROID_SDK_ROOT, and local user directories (~/AppData/Local/Android/Sdk on Windows).
- Locates vdmanager, emulator, and system images.
- Implements a specialized headerless INI parser parsing AVD config.ini files line by line, bypassing Python standard configparser crashes on headerless files.

### 8.2 Emulator Lifecycle Control
- Headless launch support (emulator -avd <name> -no-window -no-audio -gpu swiftshader_indirect).
- Polls boot completion via db -s emulator-<port> shell getprop sys.boot_completed.
- Graceful shutdown via db -s emulator-<port> emu kill with fallback process SIGKILL after 10-second timeout.

---

## 9. Apple Platform Architecture & Capabilities

### 9.1 usbmuxd TCP Daemon Discovery
- Connects directly to Apple Mobile Device Service via loopback TCP 127.0.0.1:27015.
- Parses binary plist packets for Listen and ReadPairRecord requests.
- Maps Apple product identifiers (iPhone14,2 -> iPhone 13 Pro, iPhone15,3 -> iPhone 14 Pro Max).
- Reads pairing trust records from %ProgramData%\Apple\Lockdown on Windows.

### 9.2 Honest Windows Inspection Mode
- Because Apple does not support remote video capture or touch injection on non-macOS hosts without proprietary MDM configurations, Device Lab enforces transparent Inspection Mode:
  - Displays hardware model, serial, UDID, battery, iOS version, and pairing trust.
  - Transparently disables video player and touch injection controls.
  - Zero mock or fake touch injection.

---

## 10. Automation Engine & Artifact Storage Vault

### 10.1 Declarative DSL Workflow Engine
- Supports 10 discrete workflow step types: WAIT, DELAY, TAP, SWIPE, KEY, TYPE_TEXT, SCREENSHOT, LAUNCH_APP, STOP_APP, ASSERT_STATE.
- Pre-execution validation verifies device availability, lease acquisition, coordinate ranges, and step parameters.
- Execution runner supports step-level timeouts and operator cancellation (cancel_execution).
- Serializes WorkflowExecutionReport saved as a JSON report artifact.

### 10.2 Partitioned Storage Vault & Retention
- Structured partitioning:
  - rtifacts/screenshots/: JPEG/PNG screen captures.
  - rtifacts/recordings/: MP4 hardware screen recordings.
  - rtifacts/logs/: Plaintext and JSON logcat exports.
  - rtifacts/reports/: Workflow execution reports.
- Enforces 500 MB workstation quota with automated Least-Recently-Used (LRU) pruning.
- Path traversal defense: filenames sanitized to prevent directory escapes; atomic metadata catalog maintained at rtifacts/catalog.json.

---

## 11. Diagnostics & Credential Scrubbing

### 11.1 Real-Time Credential Redaction
All logcat streams and diagnostic exports pass through sanitize_log_message regex filters:
- Bearer tokens: Bearer [A-Za-z0-9\-._~+/]+=* -> Bearer [REDACTED]
- Authorization headers: Basic [A-Za-z0-9+/=]+ -> Basic [REDACTED]
- Passwords and secrets: password=..., 	oken=..., pi_key=... -> [REDACTED]

### 11.2 Circular Buffer Observability
- Fixed-size circular deque (maxlen=2,000 entries) preventing host memory bloat.
- Real-time level filtering: Verbose (V), Debug (D), Info (I), Warning (W), Error (E), Fatal (F).
- Dynamic tag filtering and substring search.

---

## 12. Security Architecture & Process Sandboxing

1. **Subprocess Sandboxing:** Strict prohibition of shell=True. All subprocesses pass explicit argument lists (['adb', '-s', serial, 'shell', ...]).
2. **Output Bounding & Timeouts:** Subprocess stdout and stderr capped at 64 KB; execution bounded by timeouts (3.0s to 30.0s) to prevent frozen processes.
3. **Loopback & Bearer Token Authentication:** Loopback interface open for local development (127.0.0.1); optional constant-time kbt-* token validation when KELVRA_AUTH_REQUIRED=1.
4. **Linux Sandboxing Directives:** NoNewPrivileges=true, ProtectSystem=full, ProtectHome=read-only, PrivateTmp=true, LimitNOFILE=65535 in deploy/kelvra-device-lab.service.

---

## 13. KELVRA Bench Integration Architecture

Device Lab integrates with KELVRA Bench via **Approach 4 (Hybrid Out-of-Process Adapter)**:
1. **Physical Decoupling:** Device Lab runs on :8098, Bench on :8099. If Device Lab restarts, Bench remains stable.
2. **Feature Flag Isolation:** KELVRA_DEVICE_LAB_ENABLED=true/false in kelvra-bench/.env.
3. **HTTPX Client Bridge (device_lab_bridge.py):** Asynchronous client in Bench with error bounding for network faults.
4. **8 Swarm MCP Tools (device_lab_mcp.py):**
   - mobile_list_devices: Query available device inventory.
   - mobile_get_telemetry: Inspect battery, display, and state.
   - mobile_device_tap: Tap at normalized (x, y) coordinate.
   - mobile_device_swipe: Swipe from (x1, y1) to (x2, y2).
   - mobile_device_key: Send Android hardware keycode.
   - mobile_device_type: Type text string into active input field.
   - mobile_capture_screenshot: Capture instant JPEG/PNG screenshot.
   - mobile_execute_workflow: Execute multi-step declarative DSL macro.
5. **Proxy APIRouter (device_lab_router.py):** Mounted on Bench at /api/device-lab/*.
6. **Desktop UI Integration:** Dedicated Device Lab viewport and tab docked directly inside Bench.

---

## 14. Permanent Documentation Governance Rule (MANDATORY)

To prevent documentation proliferation and fragmentation, the following rule applies permanently to all future tasks and coding agents working on KELVRA Device Lab:

1. **Maximum Four Canonical Documents:** All human-maintained project documentation must reside strictly in these four canonical files inside docs/:
   - docs/DEVICE_LAB_KNOWLEDGE.md: Architectural reference, product vision, requirements, technical decisions, protocols, and security policies.
   - docs/DEVICE_LAB_STATUS.md: Verified current implementation baseline, build/test health, platform matrix, and active blockers.
   - docs/DEVICE_LAB_CHANGELOG.md: Chronological implementation history (Phases 1–24+), architectural decision records, and validation evidence.
   - docs/DEVICE_LAB_ROADMAP.md: Future work horizons, prioritization register, open decisions ledger, and next phase contracts.
2. **In-Place Updates Required:** Whenever a new phase, feature, fix, or review is completed, update the existing canonical documents in place. NEVER create separate phase prompt records, standalone validation reports, ad-hoc decision logs, or temporary status files.
3. **Zero Raw Emojis:** Never output, insert, or commit raw Unicode emojis into any documentation, code, or UI layouts.
