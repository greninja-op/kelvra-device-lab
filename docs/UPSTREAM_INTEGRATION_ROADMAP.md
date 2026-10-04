# KELVRA Device Lab — Upstream Component Integration Roadmap

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/UPSTREAM_INTEGRATION_ROADMAP.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Authority:** Implementation Staging & Integration Sequencing
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Phased Component Implementation Sequence

The integration of upstream components is mapped sequentially across the project's development phases:

```
[Phase 4: Upstream Research (COMPLETE)]
                     │
                     ▼
[Phase 5: Standalone UI & Native Provider Implementation]
- Native ADB Server Client Integration
- Baseline JPEG WebSocket Screen Streamer
- Coordinate Transformer & Native Input Injector
- Circular Buffer Logcat Service with Secret Redaction
- In-Memory Device Registry & State Machine
                     │
                     ▼
[Phase 6: Standalone Teleoperation & Smoke Automation]
- APK Installation & Package Lifecycle Driver
- Single-Click & Checkpoint Screenshot Engine
- Standalone Verification Test Suite (16/16 Unit/Integration)
- Physical POCO X6 Pro 5G Teleoperation Acceptance
                     │
                     ▼
[Phase 7: Advanced Adapters (Release 1.x)]
- scrcpy-server H.264 WebCodecs Adapter (60/120 FPS)
- Android Virtual Device (AVD) CLI Lifecycle Manager
- pymobiledevice3 Isolated Subprocess Adapter (iOS Diagnostics)
- Maestro Declarative YAML Runner Integration
                     │
                     ▼
[Phase 8: KELVRA Bench Integration Docking (DEFERRED)]
- Bench EventBus Bridge (/api/events)
- Bench Model Context Protocol (MCP) Tool Exposure
- Embedded Workspace Docking in Tauri/Vite Control Room
```

---

## 2. Component Integration Matrix

### 2.1 Native ADB Server Integration (Phase 5)
- **Component:** `src/device_manager.py` & `src/providers/android_physical.py`.
- **Prerequisites:** Host Android Platform Tools (`adb.exe` on PATH).
- **Integration Boundary:** Python asyncio client connecting to local socket `127.0.0.1:5037`.
- **Required Verification Tests:**
  - Automated detection of physical POCO X6 Pro (`8TCABAIFWOZTDICI`).
  - Parsing device properties (`ro.product.model`, `ro.build.version.sdk`).
  - Handling device disconnection and reconnection cleanly.
- **Risks:** Host ADB daemon killed by external process. Mitigated by auto-restart logic (`adb start-server`).

### 2.2 Baseline JPEG Streamer & Input Injector (Phase 5)
- **Component:** `src/screen_streamer.py` & `src/input_controller.py`.
- **Prerequisites:** Python `Pillow` library in local virtual environment.
- **Integration Boundary:** WebSocket endpoint `/ws/stream/{serial}`.
- **Required Verification Tests:**
  - Sustained 15–30 FPS frame delivery over 5-minute session.
  - Coordinate tap accuracy <= 3px.
  - Shell metacharacter rejection in text typing injection.

### 2.3 scrcpy-server H.264 WebCodecs Adapter (Phase 7)
- **Component:** `src/screen_streamer_scrcpy.py`.
- **Prerequisites:** Verified `scrcpy-server.jar` payload with matching SHA-256 checksum.
- **Integration Boundary:** Forwarded local TCP port connecting to device abstract socket.
- **Required Verification Tests:**
  - Stable 60 FPS delivery with glass-to-glass latency < 45ms.
  - Adaptive throttling down to 30 FPS under artificial host load.
  - Full socket and subprocess cleanup upon disconnect.

### 2.4 pymobiledevice3 iOS Adapter (Phase 7)
- **Component:** `src/providers/apple_physical.py`.
- **Prerequisites:** Apple `usbmuxd` Windows service running.
- **Integration Boundary:** Isolated subprocess executing `pymobiledevice3` CLI commands returning structured JSON.
- **Required Verification Tests:**
  - Detection of attached iPhone/iPad.
  - Extraction of battery health and OS version.
  - Streaming syslog entries without blocking main server loop.
  - Absolute isolation from KELVRA core codebase (zero in-process Python imports).
