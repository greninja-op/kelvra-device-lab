# KELVRA Device Lab — Component Adoption Decisions & Upstream Strategy

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/COMPONENT_ADOPTION_DECISIONS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Authority:** Architecture Review & Technology Governance
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Candidate-by-Candidate Adoption Decisions

Below are the definitive adoption classifications across the seven official decision categories:

### 1. Genymobile / scrcpy
- **Functionality Considered:** Device-side screen capture (`SurfaceControl`), hardware H.264 video encoding via `MediaCodec`, and binary input injection socket.
- **Decision:** `Integrate through a KELVRA Adapter (Release 1.x)`.
- **Rationale:** High-performance gold standard (sub-45ms latency, 60–120 FPS). Rather than embedding C code, we deploy `scrcpy-server.jar` as a standalone binary payload managed via `ScrcpyStreamer`.
- **What KELVRA Implements:** Python socket client, WebSocket NAL packetizer, WebCodecs browser rendering pipeline, process supervisor, and coordinate scaling engine.
- **Licensing & Attribution:** Apache 2.0. Requires preserving Genymobile copyright notices in documentation and license manifests.
- **Exit Strategy:** If scrcpy-server introduces incompatible changes, Device Lab automatically falls back to native ADB screencap streaming without service disruption.

### 2. Android Debug Bridge (ADB) & Platform Tools
- **Functionality Considered:** Local device enumeration, USB communication, APK installation, process inspection, logcat streaming, shell commands.
- **Decision:** `Adopt as an External Dependency (Host-Provided)`.
- **Rationale:** Authoritative Google toolchain. Utilizing the developer's pre-installed ADB binary avoids violating SDK redistribution terms.
- **What KELVRA Implements:** Python asynchronous socket client communicating with `127.0.0.1:5037`, command allowlists, shell argument sanitization, and output parsers.
- **Licensing:** Apache 2.0 (AOSP).
- **Exit Strategy:** ADB is an immovable standard for Android development; fallback is pure-python-adb or adbutils.

### 3. pymobiledevice3
- **Functionality Considered:** USB device discovery via `usbmuxd`, device metadata, battery/charging telemetry, and syslog streaming on Windows hosts.
- **Decision:** `Integrate through a KELVRA Adapter (Isolated Subprocess)`.
- **Rationale:** Pure-Python implementation eliminating Windows C build friction.
- **GPLv3 License Boundary:** Due to GPLv3 copyleft terms, `pymobiledevice3` must run in an isolated subprocess CLI worker or separate process boundary to ensure KELVRA proprietary and permissive code remains uncontaminated.
- **What KELVRA Implements:** Subprocess wrapper (`ApplePhysicalProvider`), JSON output parser, and telemetry adapter.
- **Exit Strategy:** Revert to `libimobiledevice` Windows binaries if GPL isolation proves administratively burdensome.

### 4. DeviceFarmer / stf
- **Functionality Considered:** Centralized device farm web UI and multi-device allocation.
- **Decision:** `Use as an Architectural Reference Only`.
- **Rationale:** STF's multi-process Node.js, RethinkDB, and ZeroMQ architecture is drastically over-engineered for a local-first workstation laboratory.
- **What KELVRA Adapts:** Concepts for device lease expiration, coordinate normalization math, and device state indicators.

### 5. Appium Device Farm
- **Functionality Considered:** Parallel device test session scheduling.
- **Decision:** `Reject for Documented Reason`.
- **Rationale:** Redundant with KELVRA Bench's native Swarm Orchestrator and Agent Runtime. Imposes heavy Node.js and Appium 2.x server dependencies.

### 6. Appium WebDriverAgent (WDA)
- **Functionality Considered:** iOS interactive screen streaming, touch injection, and XCUITest UI automation.
- **Decision:** `Defer Pending Further Research (Future macOS Workstations)`.
- **Rationale:** Requires an active Apple Developer Certificate and an Xcode toolchain running on a macOS host. Cannot run on a native Windows workstation.

### 7. Maestro Mobile Test Runner
- **Functionality Considered:** Declarative YAML UI test flow execution.
- **Decision:** `Integrate through a KELVRA Adapter (Release 1.x)`.
- **Rationale:** Provides human-readable, non-flaky UI testing flows that integrate cleanly into Bench QA agent workflows.
- **What KELVRA Implements:** YAML template generator, CLI invocation wrapper, and structured report extractor.

### 8. Native ADB Screencap & Input
- **Functionality Considered:** Fallback screen capture (`screencap -p`) and direct input injection (`input tap/swipe/keyevent`).
- **Decision:** `Selectively Adapt & Implement Internally (MVP Baseline)`.
- **Rationale:** Guarantees zero external binary dependencies for MVP; operational on 100% of Android devices immediately.

---

## 2. Component-by-Component Strategy Summary

| Subsystem Component | Technical Strategy | Upstream Basis / Tool | KELVRA Responsibility |
|---|---|---|---|
| **Android Device Discovery** | Native Adapter | Host ADB Server (`tcp:5037`) | `DeviceManager` socket poller |
| **Android Physical Connection** | Native Adapter | Host ADB Platform Tools | Connection FSM, lease management |
| **Android Screen Streaming (MVP)** | Native Implementation | ADB screencap + Pillow | In-memory JPEG WebSocket server |
| **Android Screen Streaming (1.x)**| Adapter Integration | Genymobile `scrcpy-server` | H.264 NAL demuxer + WebCodecs |
| **Android Input Control** | Native Implementation | ADB `input` + scrcpy socket | Coordinate scaling, shell sanitizer |
| **Android Virtual Device Lifecycle**| Native CLI Adapter | Android SDK `emulator` / `avdmanager` | Headless boot/shutdown manager |
| **Apple Device Discovery** | Isolated Subprocess Adapter| `pymobiledevice3` / `usbmuxd` | Serial and model metadata query |
| **Apple Device Communication** | Isolated Subprocess Adapter| `pymobiledevice3` lockdown | Battery, thermals, and status |
| **Apple Screen Streaming** | Deferred | Future macOS WDA / AirPlay | Documented as unsupported on Win |
| **Apple Input Control** | Deferred | Future macOS WDA | Documented as unsupported on Win |
| **iOS Automation** | Deferred | Appium WebDriverAgent (macOS) | Documented platform boundary |
| **Android Automation (MVP)** | Native Implementation | ADB shell + UIAutomator dump | `TestRunner` smoke verification |
| **Android Automation (1.x)** | Adapter Integration | Maestro CLI | Declarative YAML journey runner |
| **Device Inventory** | KELVRA Native Core | Internal Architecture | `DeviceRegistry` in-memory state |
| **Session Management** | KELVRA Native Core | Internal Architecture | Single-writer lease engine |
| **Process Supervision** | KELVRA Native Core | Python `asyncio.subprocess` | PID tracking, orphan cleanup |
| **Logs & Diagnostics** | Native Implementation | `adb logcat` pipe + regex | Circular buffer, secret redaction |
| **Screenshot & Recording** | Native Implementation | ADB screencap / screenrecord | PNG generator, artifact packager |
| **Persistence Store** | Native Implementation | Python `sqlite3` (WAL mode) | `device_lab.db` schema & queries |
