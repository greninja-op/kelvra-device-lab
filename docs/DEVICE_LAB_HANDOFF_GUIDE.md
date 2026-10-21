# KELVRA Device Lab — Developer Handoff & Operations Guide (DEVICE_LAB_HANDOFF_GUIDE.md)

## 1. Overview & Orientation

KELVRA Device Lab is an autonomous mobile device teleoperation, real-time screen streaming, fleet management, and automated verification engine. It operates standalone on port `:8098` or connects to KELVRA Bench on port `:8099` via a decoupled HTTPX client bridge.

This guide provides everything an incoming engineer or operator needs to set up, run, test, troubleshoot, and extend KELVRA Device Lab.

---

## 2. Prerequisites & Environment Requirements

### 2.1 Software Prerequisites
- **Python Runtime:** Python 3.10 or higher (Verified on Python 3.13.7 AMD64).
- **Android Debug Bridge (ADB):** Android SDK Platform-Tools v34+ installed and available on system PATH or configured via `adb_path`.
- **Operating System:**
  - **Windows 11 / Windows 10:** Full Android physical and AVD support; iOS inspection mode.
  - **Linux (Ubuntu 22.04+):** Full Android physical and AVD support; iOS inspection mode via libimobiledevice.
  - **macOS (Sonoma / Sequoia):** Full Android physical and AVD support; native iOS teleoperation planned for Horizon 3.
- **Client Web Browser:** Chrome 94+, Edge 94+, Firefox 90+, or Safari 15.4+ (WebCodecs API supported for 60 FPS H.264 stream; automatic fallback to JPEG over WebSocket).

### 2.2 Optional Hardware & Platform Tools
- **Physical Android Device:** Android 8.0+ with Developer Options and USB Debugging enabled.
- **Android Emulator (AVD):** Android Studio SDK with Windows Hypervisor Platform (WHPX) or KVM enabled.
- **Apple iOS Hardware:** iOS 14.0+ with Apple Mobile Device Service (AMDS) running on port 27015.

---

## 3. Installation & Quick Start

### 3.1 Setup Virtual Environment
From the repository root (`Kelvra/KELVRA Device Lab/`):
```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies in editable mode
pip install -e .
```

### 3.2 Verify Deployment Readiness
Before running the service, execute the automated pre-flight deployment check:
```bash
python deploy/deploy_check.py
```
Expected output:
```
==================================================================
 KELVRA Device Lab - Pre-Flight Deployment Verification Report
==================================================================
 [PASS]   | Python Version           | Python 3.13.7 (>= 3.10 required)
 [PASS]   | Core Dependencies        | All required packages installed
 [PASS]   | ADB Toolchain            | Found at: .../adb.EXE
 [PASS]   | Port Availability        | Port :8098 is free and ready to bind
 [PASS]   | Directory Permissions    | All required directories writable
------------------------------------------------------------------
 OVERALL STATUS: [DEPLOYMENT READY]
==================================================================
```

### 3.3 Launch Standalone Server
Run the standalone server on dedicated port `:8098`:
```bash
# Direct Python invocation:
python run_standalone.py

# Or on Windows using batch script:
run_standalone.bat

# Or on Linux / macOS using shell script:
./run_standalone.sh
```
Open your browser at `http://127.0.0.1:8098/` to access the Web Control Studio UI.

---

## 4. Test Execution & Verification

### 4.1 Standalone Test Suite (177 Tests)
Run the full standalone test suite:
```bash
python -m pytest -q
```
Expected result: `177 passed in ~39s`.

### 4.2 KELVRA Bench Integration Suite (24 Tests)
Run the hybrid ecosystem integration tests from `Kelvra/kelvra-bench/`:
```bash
python -m pytest -q tests/test_device_lab_integration.py
```
Expected result: `24 passed in ~5s`.

### 4.3 Total Ecosystem Pass Rate
Combined test execution confirms:
- **Total Tests:** 201 tests.
- **Pass Rate:** 100% (0 failures, 0 regressions).

---

## 5. Architectural Directory Layout

```
Kelvra/KELVRA Device Lab/
|-- src/                         # Python backend source code (22 modules)
|   |-- server.py                # FastAPI REST API, WebSocket router, static files
|   |-- domain_model.py          # 10-state FSM, Pydantic v2 schemas
|   |-- device_registry.py       # Thread-safe device registry with event dispatch
|   |-- session_manager.py       # Single-writer lease exclusivity manager
|   |-- android_provider.py      # Physical ADB provider (shell=False)
|   |-- avd_manager.py           # Android Virtual Device (AVD) supervisor
|   |-- apple_provider.py        # Apple iOS usbmuxd inspector (port 27015)
|   |-- screen_streamer.py       # JPEG screen streaming engine
|   |-- scrcpy_streamer.py       # WebCodecs 60 FPS H.264 Annex-B streaming engine
|   |-- input_controller.py      # Normalized coordinate touch and key injector
|   |-- automation_engine.py     # 10-step declarative DSL workflow runner
|   |-- artifact_manager.py      # Partitioned artifact vault with 500 MB LRU quota
|   `-- logcat_service.py        # Circular buffer logcat with regex credential scrubbing
|-- static/                      # Zero-dependency Vanilla ES6 Control Studio UI
|   |-- index.html               # Main SPA DOM structure, Studio HUD, Matrix Grid
|   |-- style.css                # Anthropic editorial dark theme tokens
|   |-- app.js                   # Client navigation, WebSocket client, touch handlers
|   `-- decoder_worker.js        # WebCodecs background worker for OffscreenCanvas
|-- tests/                       # 177 automated test cases
|-- deploy/                      # Deployment automation (systemd, Windows service)
`-- docs/                        # Authoritative project documentation
    |-- DEVICE_LAB_STATUS.md     # Current state, subsystem health, test counts
    |-- DEVICE_LAB_CHANGELOG.md  # Engineering ledger (Phases 1-30)
    |-- DEVICE_LAB_ROADMAP.md    # Strategic horizons and future milestones
    |-- DEVICE_LAB_KNOWLEDGE.md  # Comprehensive technical and architectural guide
    |-- DEVICE_LAB_FINAL_PROJECT_REVIEW.md # Phase 30 final project review
    `-- DEVICE_LAB_HANDOFF_GUIDE.md        # This handoff runbook
```

---

## 6. Operating Workflows & Runbooks

### 6.1 Connecting an Android Physical Device
1. Enable **Developer Options** on the Android device (tap Build Number 7 times).
2. Enable **USB Debugging**.
3. Connect the device via USB.
4. If an RSA fingerprint prompt appears on the phone screen, select **"Always allow from this computer"** and tap **Allow**.
5. Device Lab automatically detects the device, transitions it to `AVAILABLE`, and displays it in the Fleet Overview at `http://127.0.0.1:8098/#/devices`.

### 6.2 Starting a Teleoperation Session
1. Navigate to `#/devices` in the Control Studio.
2. Select a connected device and click **Launch Studio**.
3. The UI requests an exclusive Single-Writer Lease (`POST /api/devices/{serial}/session/acquire`).
4. Select desired streaming codec (Default: WebCodecs H.264; fallback: JPEG).
5. Touch, swipe, and hardware buttons (Back, Home, Recents, Power, Volume) are immediately active.

### 6.3 Multi-Device Matrix Grid View
1. In the Studio viewport, click the **Grid View (2x2)** layout button (`#studio-layout-select`).
2. The UI switches to the 4-cell matrix viewport.
3. The focused device streams at full framerate; background inventory devices render periodic previews via batch thumbnail polling (`GET /api/devices/thumbnails/batch`) at 0.33 FPS.
4. Click any cell to switch focus instantaneously without restarting streaming sockets.

### 6.4 Running Automated Verification Workflows
1. Navigate to `#/automation`.
2. Select a pre-configured template (e.g., Smoke Test, Settings Navigation, Gesture Matrix) or author a custom 10-step DSL workflow.
3. Click **Execute Workflow**.
4. The system tracks step-by-step progress with per-step timeouts, capturing screenshots into the Artifact Vault.
5. Review the execution report and download timestamped JSON logs.

---

## 7. Troubleshooting & Common Pitfalls

| Issue Observed | Root Cause | Remediation Procedure |
| :--- | :--- | :--- |
| **Port :8098 Already in Use** | Previous server process did not terminate or another service is listening | Run `netstat -ano \| findstr :8098` on Windows (or `lsof -i :8098` on Linux) to identify PID, then terminate with `taskkill /PID <PID> /F`. |
| **Device Appears as `UNAUTHORIZED`** | Physical Android screen locked or RSA authorization prompt not accepted | Unlock screen, disconnect and reconnect USB cable, and tap "Always allow" on the authorization prompt. |
| **AVD Fails to Boot** | Virtualization disabled in BIOS or missing WHPX/KVM | Enable Windows Hypervisor Platform in "Turn Windows features on or off" or ensure KVM permissions exist on Linux. |
| **WebCodecs Video Black Screen** | Client browser lacks WebCodecs API support | Switch the Studio codec selector dropdown to **JPEG Stream**. |
| **Artifact Vault Quota Full** | Storage exceeds 500 MB limit | Quota manager automatically evicts oldest artifacts via LRU; manually clear via `DELETE /api/artifacts` if needed. |

---

## 8. Where Development Should Continue (Horizon 3)

Incoming engineers should refer to `docs/DEVICE_LAB_ROADMAP.md` for Horizon 3 planning:
1. **Priority 3 (Native macOS iOS Teleoperation):** Implement native macOS hooks using QuickTime AVFoundation screen capture and WebDriverAgent touch injection for physical iOS devices.
2. **Priority 4 (Enterprise Token Authentication):** Enforce cryptographic `kbt-*` Bearer token validation and role-based access control (Admin, Operator, Viewer) when deploying to non-loopback environments.
3. **Priority 5 (Dynamic Audio Streaming):** Add WebRTC/AAC audio capture pipeline alongside video streaming.
