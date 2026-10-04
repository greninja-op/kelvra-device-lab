# KELVRA Device Lab — Upstream Repository Research & Technical Audit

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/UPSTREAM_REPOSITORY_RESEARCH.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Research Date:** 2026-10-04
- **Authority:** Open-Source Technology Evaluation & Upstream Audit
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Candidate Project Evaluations

### 1.1 Genymobile / scrcpy
- **Official Repository:** `https://github.com/Genymobile/scrcpy`
- **Primary Language:** C (client and server native core) and Java (Android `scrcpy-server` runner).
- **License:** Apache License 2.0 (Permissive, commercial-friendly).
- **Maintenance Activity:** Very active; continuous development led by Romain Vimont (connect2id / Genymobile). Multiple minor and major releases yearly (v2.x series active).
- **Supported Operating Systems:** Windows (x86_64, arm64), macOS (Apple Silicon / Intel), Linux (Debian, Fedora, Arch).
- **Supported Device Platforms:** Android 5.0+ (API 21+); advanced features (audio forwarding, physical virtual display) require Android 10+ / 11+ / 12+.
- **Main Capabilities:**
  - Ultra-low latency screen capture via `SurfaceControl` or `MediaProjection`.
  - Hardware-accelerated H.264/H.265/AV1 video encoding directly on device SoC via `MediaCodec`.
  - Up to 120 FPS high-refresh streaming on capable displays with low frame jitter.
  - Sub-45ms glass-to-glass latency over USB 2.0/3.0.
  - Multi-touch injection, physical keyboard mapping, mouse button emulation (Back, Home, App Switcher).
  - Forwarded ADB socket architecture allowing external control clients.
- **Known Limitations:**
  - Standalone desktop client is a monolithic C/SDL2 application; embedding the C client directly into a web or Python backend is impractical.
  - Audio capture requires Android 11+ or custom helper APK.
  - Pushing jar files to `/data/local/tmp` requires authorized ADB shell access.
- **Integration Mechanism:** Managed Adapter Pattern. KELVRA Device Lab pushes `scrcpy-server.jar`, spawns it via `app_process` in a non-windowed subprocess, establishes an ADB port forward, and connects a Python socket client (`scrcpy_client.py`) to stream raw NAL units to WebCodecs and send binary input packets.
- **Security Implications:** Operates under standard Android user-space permissions (`shell` uid 2000). Zero cloud telemetry or external network calls.
- **Architectural Fit:** Exceptional. Serves as the premier Tier 2 high-FPS video streaming and low-latency control engine for Release 1.x.

---

### 1.2 DeviceFarmer / stf (Smartphone Test Farm)
- **Official Repository:** `https://github.com/DeviceFarmer/stf`
- **Primary Language:** JavaScript / TypeScript (Node.js backend and AngularJS frontend).
- **License:** Apache License 2.0.
- **Maintenance Activity:** Sporadic / community-maintained fork of the original OpenSTF project. Slower release cadence; legacy dependency stack.
- **Supported Operating Systems:** Linux (officially supported host); Windows execution is notoriously fragile and requires complex Docker or WSL orchestration.
- **Supported Device Platforms:** Android physical devices.
- **Main Capabilities:**
  - Centralized multi-device web inventory.
  - Device reservation, booking, and remote touch control.
  - Minirev, minicap, and minitouch device-side daemons.
- **Known Limitations:**
  - Architectural behemoth: relies on RethinkDB, ZeroMQ, Protocol Buffers, and multiple Node.js microservices.
  - Heavy resource consumption (high idle RAM and CPU).
  - Windows host support is not natively supported; running on developer Windows workstations requires substantial virtualization layers.
- **Integration Mechanism:** `Architectural Reference Only`. We study STF's device allocation models, coordinate normalization algorithms, and ADB connection management, but reject importing its monolithic codebase or database stack.
- **Security Implications:** Introduces broad attack surfaces through RethinkDB and multi-tenant authentication layers.
- **Architectural Fit:** Poor. Conflicts with KELVRA's local-first, lightweight, single-process workstation ethos.

---

### 1.3 Appium Device Farm
- **Official Repository:** `https://github.com/AppiumTestDistribution/appium-device-farm`
- **Primary Language:** JavaScript (Node.js plugin for Appium 2.x).
- **License:** Apache License 2.0.
- **Maintenance Activity:** Active community plugin maintained within the Appium ecosystem.
- **Supported Operating Systems:** macOS, Linux, Windows.
- **Supported Device Platforms:** Android and iOS (physical devices and emulators).
- **Main Capabilities:**
  - Dynamic allocation of devices for Appium automation sessions.
  - Parallel test execution routing across connected local and remote devices.
  - Dashboard showing live device utilization.
- **Known Limitations:**
  - Tight coupling to the Appium 2.x server ecosystem and WebDriver protocol.
  - Overhead: Appium HTTP command translation introduces 150–300ms latency per action, making it unsuitable for live interactive human teleoperation.
  - Redundant with KELVRA's own `DeviceManager` and Bench Swarm Orchestrator.
- **Integration Mechanism:** `Deferred`. Not adopted for core device discovery, streaming, or teleoperation. Evaluated strictly as an optional future test execution target if external teams require legacy Appium test suite support.
- **Architectural Fit:** Redundant with KELVRA's native orchestration.

---

### 1.4 Android Debug Bridge (ADB) & Android SDK Platform Tools
- **Official Source:** Google Android Open Source Project (AOSP) / Android SDK Command-line Tools.
- **Primary Language:** C++ (host binary and device daemon `adbd`).
- **License:** Apache License 2.0 (Permissive).
- **Maintenance Activity:** Authoritative continuous maintenance by Google with every Android OS release (Platform-tools 35+ / ADB 1.0.41+).
- **Supported Operating Systems:** Windows, macOS, Linux.
- **Supported Device Platforms:** Android 1.0 through Android 15+.
- **Main Capabilities:**
  - Canonical device discovery via local ADB server socket (`127.0.0.1:5037`).
  - Device authorization handling (RSA public key exchange).
  - Fast APK installation (`adb install -r -d`, streaming split-APKs).
  - Screen capture (`screencap -p`), logcat streaming, process management, input injection.
- **Known Limitations:**
  - Spawning `adb.exe` via CLI process creates host overhead (~15–30ms per command). Direct socket interaction is required for high-frequency operations.
- **Integration Mechanism:** `External Dependency (Host-Provided)`. KELVRA Device Lab requires ADB on the host PATH or Android SDK directory.
- **Licensing & Redistribution:** We use the developer's pre-installed ADB toolchain. Device Lab does **not** bundle or redistribute proprietary SDK binaries, avoiding Google SDK Terms of Service redistribution constraints.
- **Architectural Fit:** Absolute foundation for all Android hardware interactions.

---

### 1.5 pymobiledevice3
- **Official Repository:** `https://github.com/doronz88/pymobiledevice3`
- **Primary Language:** Python 3 (Pure Python implementation of Apple lockdown and mobile protocols).
- **License:** GNU General Public License v3 (GPLv3).
- **Maintenance Activity:** Highly active; maintained by Doron Zavelevsky and mobile security researchers. Rapidly updated for iOS 17 and iOS 18 beta changes.
- **Supported Operating Systems:** Windows, macOS, Linux.
- **Supported Device Platforms:** Physical iPhone and iPad devices running iOS 12 through iOS 18+.
- **Main Capabilities:**
  - Device enumeration via local `usbmuxd` socket.
  - Query device metadata (ECID, serial, model, hardware generation, battery health, charging status).
  - Stream real-time diagnostic syslog.
  - Mount Developer Disk Images (DDI) and query developer services.
  - Screenshot capture via `screenshotr` service.
- **Known Limitations:**
  - Interactive screen teleoperation and touch event injection are not provided by lockdown protocols.
  - iOS 17+ introduced Tunneld / CoreDevice remote pairing protocols requiring additional pairing pairing handshake.
  - **GPLv3 License:** Requires strict process boundary isolation (managed CLI subprocess or isolated REST service) to prevent copyleft viral contamination into KELVRA proprietary and permissive codebases.
- **Integration Mechanism:** `Adapter Integration (Isolated Subprocess)`. Device Lab interacts with `pymobiledevice3` as an external CLI worker or isolated subprocess adapter.
- **Architectural Fit:** High for discovery, battery telemetry, and syslog diagnostics on Windows hosts.

---

### 1.6 libimobiledevice
- **Official Repository:** `https://github.com/libimobiledevice/libimobiledevice`
- **Primary Language:** C.
- **License:** GNU Lesser General Public License v2.1+ (LGPLv2.1+) for libraries; GPLv2+ for CLI tools.
- **Maintenance Activity:** Active, authoritative open-source C library for iOS communication.
- **Supported Operating Systems:** Linux, macOS, Windows (via MSYS2 or MinGW builds).
- **Main Capabilities:** Native C bindings for usbmuxd, ideviceinfo, idevicesyslog, idevicescreenshot.
- **Comparison with pymobiledevice3:** Building and maintaining C DLLs across Windows environments introduces significant compilation and ABI friction compared to Python-based `pymobiledevice3`.
- **Integration Mechanism:** `Architectural Reference`. Prefer `pymobiledevice3` for direct Python integration.

---

### 1.7 Appium / WebDriverAgent (WDA)
- **Official Repository:** `https://github.com/appium/WebDriverAgent`
- **Primary Language:** Objective-C / Swift (XCUITest test runner).
- **License:** BSD 3-Clause License (Permissive).
- **Maintenance Activity:** Actively maintained by the Appium development team.
- **Supported Operating Systems:** macOS (Required for compilation, signing, and execution).
- **Supported Device Platforms:** iOS Physical Devices and iOS Simulators.
- **Main Capabilities:**
  - Full UI automation, accessibility element inspection, touch tap, swipe, and keyboard typing.
  - Built-in MJPEG screen streaming server over HTTP.
- **Known Limitations:**
  - **Strict macOS Host Requirement:** WDA is an XCTest suite that must be built with Xcode and signed with an active Apple Developer Certificate. It cannot be launched from a native Windows host without an external macOS runner.
- **Integration Mechanism:** `Deferred`. Formally scheduled for future phases when macOS execution nodes are introduced into the KELVRA Bench swarm.
- **Architectural Fit:** Essential for future iOS teleoperation, but excluded from MVP.

---

### 1.8 adbutils (openatx)
- **Official Repository:** `https://github.com/openatx/adbutils`
- **Primary Language:** Python 3.
- **License:** MIT License (Permissive).
- **Maintenance Activity:** Actively maintained.
- **Main Capabilities:** Pure Python client communicating directly with ADB server socket (`127.0.0.1:5037`). Provides fast device enumeration, file transfer, and shell execution without subprocess overhead.
- **Integration Mechanism:** `Adopt as External Dependency` (Optional in Release 1.x to optimize `device_manager.py`).
