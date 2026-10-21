# KELVRA Device Lab — Upstream Project Evaluation & Candidate Taxonomy

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/UPSTREAM_EVALUATION.md`
- **Subsystem:** KELVRA Device Lab
- **Scope:** Technical evaluation of mature open-source projects for device capture, control, inventory, and automation
- **Evaluation Criteria:** Architecture, feature coverage, maintenance, license, security, performance, compatibility, dependency footprint, extensibility, integration cost
- **Classification Categories:**
  - `External Dependency`: Installed via package manager or bundled binary as a standard library/runtime.
  - `Adapter Integration`: Custom wrapper interfacing with upstream protocol or daemon over socket/CLI.
  - `Selective Source Adaptation`: Carefully audited algorithms, protocol parsers, or scripts adapted directly into our codebase.
  - `Fork`: Upstream repository cloned and modified when deep architectural divergences are necessary.
  - `Independent Implementation`: Clean-room implementation tailored strictly to KELVRA architecture.
  - `Deferred`: Out of scope for immediate standalone phases; earmarked for future roadmap.
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Android Screen Capture and Remote Control

### 1.1 Genymobile scrcpy
- **Architecture:** Client-server model. A lightweight Java server JAR (`scrcpy-server`) is pushed to the device via ADB and executed through `app_process`. It captures the screen via `SurfaceControl` or `MediaProjection`, encodes video via hardware `MediaCodec` (H.264/H.265/AV1), and streams raw frames over an ADB socket. A control socket accepts binary input events.
- **Feature Coverage:** High-performance video streaming (up to 120 FPS, sub-50ms latency), mouse/touch injection, clipboard synchronization, physical button simulation, audio forwarding.
- **Maintenance:** Actively maintained by Romain Vimont and Genymobile (thousands of commits, widely adopted).
- **License:** Apache 2.0 (Permissive, commercial-friendly).
- **Security:** Requires ADB authorization. Operates within device-level Android sandbox. Zero cloud telemetry.
- **Performance:** Industry gold standard. Hardware accelerated encoding and ultra-low latency.
- **Compatibility:** Android 5.0+ (API 21+); advanced features require Android 10+.
- **Dependency Footprint:** Requires ADB host binary and `scrcpy-server.jar`.
- **Classification:** `Adapter Integration` (Primary high-FPS streaming and low-latency control engine).
- **Integration Plan:** In Phase D/E, bundle pre-built `scrcpy-server.jar` and implement a Python socket client (`scrcpy_client.py`) that launches the server via ADB forward and translates the raw H.264/control stream into browser WebSockets.

### 1.2 ws-scrcpy
- **Architecture:** Node.js server wrapping `scrcpy-server` with WebSocket transport and in-browser H.264 decoding (Broadway / tinyh264 / WebCodecs).
- **Feature Coverage:** Multi-device web streaming, touch injection, audio decoding.
- **Maintenance:** Moderately active, primarily maintained by NetrisTV.
- **License:** MIT.
- **Security:** Node.js process with WebSocket endpoints. Requires local authentication.
- **Performance:** Excellent browser decoding via WebCodecs; higher server memory overhead due to Node runtime.
- **Compatibility:** Broad web browser support.
- **Dependency Footprint:** Heavy (Node.js runtime, npm dependencies).
- **Classification:** `Selective Source Adaptation` (Reference architecture for browser WebCodecs decoding and touch mapping; avoid importing entire Node.js stack into Python backend).

### 1.3 Native ADB Screencap / Exec-Out (Fallback Engine)
- **Architecture:** `adb exec-out screencap -p` or ADB minicap frame extraction over standard ADB shell.
- **Feature Coverage:** Single-frame capture, fallback streaming at 5-15 FPS.
- **Maintenance:** Maintained directly by Google Android Open Source Project.
- **License:** Apache 2.0.
- **Security:** Standard ADB authorization.
- **Performance:** Moderate to low (higher CPU utilization, lower framerate compared to hardware MediaCodec).
- **Compatibility:** 100% of Android devices with USB debugging enabled.
- **Dependency Footprint:** Minimal (uses existing ADB binary).
- **Classification:** `Independent Implementation` (Already implemented in `src/screen_streamer.py` as reliable zero-dependency baseline fallback).

---

## 2. ADB Communication and Device Management

### 2.1 adbutils (Python)
- **Architecture:** Pure Python socket client communicating directly with the local ADB server daemon (`127.0.0.1:5037`) using the canonical ADB client-server protocol.
- **Feature Coverage:** Device enumeration, shell execution, file push/pull, port forwarding, package installation, logcat streaming, process tracking.
- **Maintenance:** Active (openatx project, widely used in mobile test automation).
- **License:** MIT.
- **Security:** Localhost socket communication only.
- **Performance:** High (direct socket calls bypass process spawn overhead of `subprocess.run(["adb", ...])`).
- **Compatibility:** Python 3.8+, all OS platforms (Windows, macOS, Linux).
- **Dependency Footprint:** Very low (lightweight Python package).
- **Classification:** `External Dependency` (Candidate to augment or streamline `src/device_manager.py`).

### 2.2 pure-python-adb (ppadb)
- **Architecture:** Pure Python ADB client implementation.
- **Feature Coverage:** Basic device discovery, shell, install, screencap.
- **Maintenance:** Stale / low maintenance (several unresolved issues upstream).
- **License:** MIT.
- **Dependency Footprint:** Low.
- **Classification:** `Selective Source Adaptation` (Extract protocol constants if needed, but prefer `adbutils` or direct subprocess wrapping for long-term stability).

---

## 3. Android Virtual Devices & Emulator Management

### 3.1 Android SDK Emulator CLI (`emulator`, `avdmanager`)
- **Architecture:** Official QEMU-based virtualization toolchain provided by Google Android SDK.
- **Feature Coverage:** Headless startup (`-no-window`), snapshot management, hardware profile configuration, cold/warm boot control, dynamic port assignment.
- **Maintenance:** Authoritative upstream maintenance by Google.
- **License:** Android Software Development Kit License.
- **Security:** Local virtualization sandbox.
- **Performance:** Hardware accelerated via Windows Hypervisor Platform (WHPX) or KVM on Linux.
- **Compatibility:** Windows, macOS, Linux.
- **Dependency Footprint:** Requires Android SDK Command-line Tools and system images.
- **Classification:** `Adapter Integration` (Wrap via Python service `src/emulator_manager.py` in Phase D).

---

## 4. Apple iOS Device Communication and Teleoperation

### 4.1 pymobiledevice3 (Python)
- **Architecture:** Pure Python implementation of Apple's Lockdown, usbmuxd, AFC, and mobile services protocols. Communicates directly with Apple devices over USB or Wi-Fi.
- **Feature Coverage:** Device discovery via usbmuxd, syslog streaming, app installation, crash log extraction, battery and thermal telemetry, developer image mounting.
- **Maintenance:** Very active (DoronZ, security researchers).
- **License:** GPLv3 (Requires strict boundary isolation to ensure KELVRA proprietary and permissive licenses remain uncontaminated).
- **Security:** Complies with iOS pairing protocol (requires user confirmation on device).
- **Performance:** Excellent for diagnostics, metadata, and installation.
- **Compatibility:** iOS 12 through iOS 18+. Supports Windows, macOS, and Linux.
- **Dependency Footprint:** Python package with crypto dependencies (cryptography).
- **Classification:** `Adapter Integration` (Isolated subprocess service to prevent GPL viral propagation into KELVRA Bench core).

### 4.2 go-ios (Golang)
- **Architecture:** Standalone Go binary implementing usbmuxd and developer disk image interaction without requiring iTunes or Xcode.
- **Feature Coverage:** Device info, screenshot extraction, app launch, process listing.
- **Maintenance:** Moderately active (DanielPaulus).
- **License:** MIT.
- **Performance:** High (compiled native binary).
- **Classification:** `Adapter Integration` (Optional companion CLI binary for cross-platform iOS discovery).

### 4.3 Appium WebDriverAgent (WDA) & idb (iOS Development Bridge)
- **Architecture:** WDA runs as an XCUITest test runner process on the iOS device, exposing an HTTP REST server for touch, typing, element inspection, and screen streaming. Facebook `idb` provides companion daemon capabilities.
- **Feature Coverage:** Full interactive control, UI hierarchy inspection, screenshot streaming.
- **Maintenance:** WDA is actively maintained by the Appium team. `idb` has slower maintenance.
- **License:** BSD 3-Clause / Apache 2.0.
- **Security:** Requires iOS Developer Mode and codesigning identity.
- **Performance:** 10-30 FPS screen streaming via MJPEG endpoint.
- **Compatibility:** Requires macOS host for signing and mounting, or pre-signed WDA runner.
- **Classification:** `Deferred` (iOS remote control deferred to Phase D/E given requirement for macOS developer signing).

---

## 5. Device Farms & Fleet Management

### 5.1 OpenSTF / Device Farmer (STF)
- **Architecture:** Distributed multi-process system in Node.js with RethinkDB, ZeroMQ, and WebSocket coordination.
- **Feature Coverage:** Full device farm orchestration, remote booking, user management.
- **Maintenance:** OpenSTF is unmaintained; Device Farmer fork is maintained sporadically.
- **License:** Apache 2.0.
- **Security:** Complex multi-tenant security architecture with separate auth layer.
- **Critique & Fit:** Excessive architectural complexity, heavyweight external dependencies (RethinkDB, ZeroMQ), and monolithic design that conflicts with KELVRA's local-first, lightweight ethos.
- **Classification:** `Deferred` (Do not adopt; implement lightweight KELVRA native fleet manager).

---

## 6. Test Automation Frameworks

### 6.1 UIAutomator2 (Python `uiautomator2`)
- **Architecture:** Android service APK pushed to device exposing a local JSON-RPC server over port 7912. Python client sends UI interaction commands.
- **Feature Coverage:** Fast UI hierarchy dumping, selector-based clicks (`d(text="Settings").click()`), OCR, watchdogs, toast capture.
- **Maintenance:** Active (openatx community).
- **License:** MIT.
- **Performance:** Substantially faster than Appium for Android-only verification.
- **Classification:** `Adapter Integration` (Candidate engine for autonomous test pipelines in Phase E).

### 6.2 Maestro
- **Architecture:** Modern declarative YAML-driven mobile UI test automation tool. Runs locally, interacts with accessibility hierarchies.
- **Feature Coverage:** Declarative flows (`- tapOn: "Login"`, `- assertVisible: "Welcome"`), tolerance to UI flakiness.
- **Maintenance:** Very active (Mobile.dev).
- **License:** Apache 2.0.
- **Performance:** Fast, developer-friendly.
- **Classification:** `Adapter Integration` (Candidate runner for high-level user journey verification).

---

## 7. Streaming Transport Protocols

### 7.1 Binary WebSocket with JPEG Frames
- **Architecture:** Server encodes screencap to JPEG in memory and broadcasts binary chunks over WebSocket. Browser draws chunks directly to HTML5 Canvas via `ImageBitmap` or `URL.createObjectURL`.
- **Latency:** ~60-120ms over local loopback.
- **Bandwidth:** Moderate (~2-4 MB/s at 1080p 15-20 FPS).
- **Implementation Cost:** Minimal; already operational in `src/screen_streamer.py`.
- **Classification:** `Independent Implementation` (Active baseline).

### 7.2 WebCodecs with WebSocket H.264 NAL Units
- **Architecture:** Server streams raw H.264 NAL units from `scrcpy-server` over WebSocket. Client browser utilizes native `VideoDecoder` API to decode and paint frames directly to canvas.
- **Latency:** Ultra-low (~20-40ms).
- **Bandwidth:** Very low (~500 KB/s - 1.5 MB/s at 1080p 60 FPS).
- **Implementation Cost:** Moderate (requires parsing SPS/PPS NAL headers and initializing browser WebCodecs).
- **Classification:** `Selective Source Adaptation` (Planned for Phase E).

### 7.3 WebRTC DataChannel & MediaStream
- **Architecture:** Full peer-to-peer WebRTC session with STUN/turn signaling and VP8/H.264 RTP stream.
- **Latency:** ~30-50ms with jitter buffering.
- **Implementation Cost:** High (requires WebRTC native bindings or Pion WebRTC server).
- **Classification:** `Deferred` (Unnecessary complexity for localhost/LAN workstation teleoperation).

---

## 8. Summary Taxonomy Matrix

| Candidate Project | Domain | License | Classification | Target Phase |
|---|---|---|---|---|
| **Genymobile scrcpy** | Android Video/Control | Apache 2.0 | `Adapter Integration` | Phase D/E |
| **ws-scrcpy** | Web H.264 Decoding | MIT | `Selective Source Adaptation` | Phase E |
| **Native ADB Screencap** | Fallback Video | Apache 2.0 | `Independent Implementation` | Baseline (Ready) |
| **adbutils** | ADB Protocol Client | MIT | `External Dependency` | Phase D |
| **Android SDK Emulator CLI** | Virtual Devices | SDK License | `Adapter Integration` | Phase D |
| **pymobiledevice3** | iOS Diagnostics & Usbmux | GPLv3 | `Adapter Integration` (Isolated) | Phase D/E |
| **go-ios** | iOS Inspection CLI | MIT | `Adapter Integration` | Phase E |
| **Appium WebDriverAgent** | iOS Automation | BSD 3-Clause | `Deferred` | Phase E+ |
| **OpenSTF / Device Farmer** | Fleet Farm | Apache 2.0 | `Deferred` | Not Recommended |
| **uiautomator2** | Android UI Automation | MIT | `Adapter Integration` | Phase E |
| **Maestro** | Declarative Testing | Apache 2.0 | `Adapter Integration` | Phase E |
| **WebCodecs H.264 Streamer** | Video Transport | Custom / MIT | `Selective Source Adaptation` | Phase E |
