# KELVRA Device Lab — End-to-End System Workflows (`docs/END_TO_END_WORKFLOWS.md`)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/END_TO_END_WORKFLOWS.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Phase:** Phase 15 — Standalone System Testing & Acceptance
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview

This document specifies the five foundational End-to-End (E2E) workflows verified during Phase 15 system testing. Each workflow maps the sequence of API calls, WebSocket events, state machine transitions, and UI behaviors that occur during real-world developer operations.

---

## 2. Workflow 1: Physical Fleet Discovery & Interactive Teleoperation

### Sequence of Operations
```
[Physical Device Attached via USB]
  │
  ▼
1. Discovery Sweep: AndroidDeviceProvider polls ADB localhost:5037
  │  └─ Parses 'adb devices -l', queries 'getprop' for hardware specs
  │  └─ Enrolls Device into DeviceRegistry (state = AVAILABLE)
  ▼
2. Client Enters Studio: User clicks device in Fleet Grid
  │
  ▼
3. Lease Acquisition: Client requests single-writer operator lease
  │  └─ POST /api/devices/{serial}/lease
  │  └─ SessionManager grants exclusive token (e.g. 'kdl-9a8b7c6d...')
  │  └─ Device state transitions to BUSY in registry
  ▼
4. Screen Stream Handshake: Client opens WebSocket connection
  │  └─ WS /ws/devices/{serial}/stream
  │  └─ DeviceStreamSession exits idle throttle and initiates 30 FPS screencap
  │  └─ Frames encoded to 720p JPEG (quality 75) and broadcast via WebSocket
  ▼
5. Interactive Input Injection: User taps and keys on canvas
  │  └─ POST /api/devices/{serial}/input/tap with coordinates and session_token
  │  └─ InputController validates coordinates within physical resolution
  │  └─ Dispatches 'adb shell input tap x y'
  ▼
6. Session Teardown: User releases device or tab closes
  │  └─ DELETE /api/devices/{serial}/lease
  │  └─ Streamer returns to 150ms idle throttle when viewer count reaches 0
  │  └─ Device state restored to AVAILABLE
```

---

## 3. Workflow 2: Android Virtual Device (AVD) Emulation Lifecycle

### Sequence of Operations
1. **SDK Detection:** `SdkEnvironmentDetector` discovers Android SDK root, `emulator.exe`, and available system images without executing arbitrary shell scripts.
2. **AVD Inventory Discovery:** `AvdManager` parses headerless `.ini` files in `~/.android/avd/`, extracting ABI (`x86_64`), API level, and hardware profile.
3. **Headless Launch:** Operator triggers emulator launch via `POST /api/avd/launch/{name}`. The manager assigns an even console port (`5554`), constructs command parameters (`-no-window -no-audio -no-snapshot`), and spawns the background process (`shell=False`).
4. **Boot Monitoring:** Async coroutine polls `sys.boot_completed=1` over ADB. Upon completion, AVD status updates to `READY`.
5. **Registry Integration:** Booted emulator enrolls automatically in `DeviceRegistry` as `ANDROID_VIRTUAL` in `AVAILABLE` state for immediate teleoperation.
6. **Graceful Teardown:** `stop_emulator()` sends controlled shutdown signals, reaps child process handles, and transitions registry state to `UNAVAILABLE`.

---

## 4. Workflow 3: Automated Workflow Scheduling & Artifact Persistence

### Sequence of Operations
1. **Workflow Definition:** Developer posts a structured JSON workflow defining sequential steps (`WAIT`, `TAP`, `SWIPE`, `KEY`, `TYPE_TEXT`, `SCREENSHOT`, `LAUNCH_APP`, `STOP_APP`, `ASSERT_STATE`).
2. **Pre-Flight Validation:** `AutomationEngine.validate_workflow()` validates step schema, coordinate bounds against device dimensions, and package name regex.
3. **Exclusive Execution Locking:** Engine verifies device is not currently executing another workflow, locks the target serial, and marks report status as `RUNNING`.
4. **Step Execution Loop:** Steps execute sequentially. Screenshots captured during the workflow are written to disk via `ArtifactManager`.
5. **Report Serialization:** `WorkflowExecutionReport` with timing metrics and pass/fail states is cataloged in `artifacts/reports/` and indexed in `catalog.json`.
6. **Storage Quota Enforcement:** `_prune_quota()` verifies total artifact storage remains <= 500 MB, automatically pruning oldest assets via LRU policy.

---

## 5. Workflow 4: Observability, Live Logcat & Diagnostics

### Sequence of Operations
1. **Logcat Process Spawning:** Upon client subscription (`WS /ws/devices/{serial}/logcat`), `LogcatService` attaches an async reader to `adb logcat -v time`.
2. **Real-Time Regex Scrubbing:** Each log line passes through `sanitize_log_message()`, redacting Bearer tokens, passwords, API keys, and session tokens before memory insertion.
3. **Circular Buffer Ingestion:** Log entries append to `collections.deque(maxlen=2000)`, guaranteeing $O(1)$ appends and strictly bounding memory to ~2 MB per device.
4. **Dynamic Filtering:** Client filters entries by severity level (V/D/I/W/E/F), tag, or search term with sub-millisecond query latency.
5. **Artifact Export:** Operator exports filtered logs via `GET /api/devices/{serial}/logs/export`, generating persistent TXT or JSON artifacts in `artifacts/logs/`.
6. **Diagnostics Aggregation:** `GET /api/diagnostics/devices/{serial}` aggregates multi-tier metrics (provider health, stream FPS, lease timer, battery temperature, recent errors) into a structured JSON report.

---

## 6. Workflow 5: Multi-Tenant Security & Sandboxing Gates

### Sequence of Operations
1. **Unauthorized Hardware Gate:** Devices connected without accepted RSA debugging keys are marked `UNAUTHORIZED`. REST endpoints reject teleoperation and streaming with HTTP 403 Forbidden and an actionable recovery hint.
2. **Single-Writer Collision Gate:** If Client B attempts to teleoperate a device leased by Client A, the server rejects the request with HTTP 409 Conflict, returning Client A's identifier and expiration countdown.
3. **Path Traversal Gate:** Uploads or artifact generation requests attempting directory escape (e.g. `../../secret.sh`) have `..` stripped and are anchored strictly inside `artifacts/`.
4. **Command Injection Gate:** Subprocess commands avoid shell interpreters entirely (`shell=False`), executing parameter lists directly via OS exec primitives.
