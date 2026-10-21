# KELVRA Device Lab — Feature Catalog

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/FEATURE_CATALOG.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Classification Categories:** `MVP`, `Release 1.x`, `Future`, `Deferred`
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Catalog Schema
Each feature in this catalog is systematically documented with:
- **Feature ID & Name**
- **Purpose:** Core functional intent.
- **User Value:** Concrete benefit to developer or autonomous agent.
- **Dependencies:** Required host binaries, libraries, or protocols.
- **Platform Support:** Android Physical, Android Virtual, iOS Physical, iOS Simulator.
- **Complexity:** Low, Medium, High.
- **Security Implications:** Sandboxing, permissions, network, or data privacy risks.
- **Acceptance Criteria:** Verifiable pass/fail criteria.
- **Release Classification:** MVP, Release 1.x, Future, Deferred.

---

## 2. Feature Entries

### F-01: Real-Time Fleet Discovery
- **Purpose:** Automatically detect, query, and track connected devices via USB and ADB sockets.
- **User Value:** Eliminates manual terminal discovery commands (`adb devices`); provides instant visibility of connected test hardware.
- **Dependencies:** Host ADB binary (`127.0.0.1:5037`).
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Low.
- **Security Implications:** Read-only ADB socket queries; no elevated privileges required.
- **Acceptance Criteria:** Detects physical device within 2.0s of USB insertion; displays model, serial, and status.
- **Release Classification:** `MVP`.

### F-02: Live Screen Streaming (Baseline WebSocket JPEG)
- **Purpose:** Capture device screen frames and stream them over binary WebSockets to an HTML5 `<canvas>` viewport.
- **User Value:** Zero-dependency, highly reliable live screen visualizer that works out-of-the-box across 100% of Android devices.
- **Dependencies:** ADB screencap / minicap fallback, Pillow / libjpeg, WebSocket server.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Transmits live screen pixel data over localhost WebSocket.
- **Acceptance Criteria:** Renders continuous screen stream at >= 15 FPS with < 120ms latency over localhost loopback without freezing.
- **Release Classification:** `MVP`.

### F-03: Interactive Mouse Touch & Gesture Injection
- **Purpose:** Translate browser mouse events into normalized Android touchscreen taps, drag-swipes, and long-presses.
- **User Value:** Enables direct interactive teleoperation of physical and virtual devices directly from the browser window.
- **Dependencies:** ADB input command or persistent control socket.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Sends simulated user input directly to the mobile OS.
- **Acceptance Criteria:** Left click clicks exact target coordinates (+/- 3px accuracy); click-and-drag scrolls list views smoothly.
- **Release Classification:** `MVP`.

### F-04: Hardware Navigation Buttons & Text Injection
- **Purpose:** Provide virtual buttons for Back, Home, App Switcher, Power, Volume, and pass physical keyboard typing into device text fields.
- **User Value:** Complete control of Android navigation without needing to touch physical device buttons.
- **Dependencies:** ADB `input keyevent` and `input text`.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Low.
- **Security Implications:** Text injection must escape shell metacharacters to prevent command injection.
- **Acceptance Criteria:** Right-click or Back button navigates back; typing into a focused Android text field inserts characters accurately.
- **Release Classification:** `MVP`.

### F-05: Real-Time Virtualized Logcat Streamer
- **Purpose:** Stream device logcat messages over WebSockets with real-time severity, tag, and regex filtering.
- **User Value:** Instant debugging of mobile crashes, companion events, and audio engine logs without opening separate console windows.
- **Dependencies:** `adb logcat -v time`.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Potential exposure of sensitive data in system logs. Requires client-side and server-side secret redaction.
- **Acceptance Criteria:** Streams live logcat at up to 1,000 lines/sec without browser UI lag; regex filtering updates view within 100ms.
- **Release Classification:** `MVP`.

### F-06: Hardware Telemetry & Thermal Health Monitor
- **Purpose:** Poll and display CPU load, RAM usage, storage availability, battery percentage, charging state, and battery temperature.
- **User Value:** Protects test devices from overheating during intensive agent test loops and detects battery depletion.
- **Dependencies:** `dumpsys battery`, `dumpsys cpuinfo`, `proc/meminfo`.
- **Platform Support:** Android Physical.
- **Complexity:** Low.
- **Security Implications:** Read-only system metrics.
- **Acceptance Criteria:** Polls metrics every 3s; alerts if temperature exceeds 42°C or battery drops below 15%.
- **Release Classification:** `MVP`.

### F-07: Single-Click & Programmatic Screenshot Capture
- **Purpose:** Capture high-resolution uncompressed screenshots from the device display and save them with timestamped metadata.
- **User Value:** Instant visual evidence generation for bugs and test verification checkpoints.
- **Dependencies:** ADB screencap.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Low.
- **Security Implications:** Stores image files in local test artifact directory.
- **Acceptance Criteria:** Generates PNG screenshot matching native resolution in < 800ms; returns accessible file path and base64 preview.
- **Release Classification:** `MVP`.

### F-08: Autonomous Test Runner (Smoke & APK Verification)
- **Purpose:** Install build APK, launch main activity, verify process health, capture checkpoint screenshots, and terminate application.
- **User Value:** Allows autonomous Bench agents to verify that compiled companion APKs install and launch cleanly on real hardware.
- **Dependencies:** `adb install`, `am start`, `am force-stop`.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Installs executable binaries. Rejects non-verified or corrupted APK packages.
- **Acceptance Criteria:** Installs APK in < 15s; launches package; records pass/fail status and output logs in JSON report.
- **Release Classification:** `MVP`.

### F-09: High-Performance Hardware MediaCodec Streaming (scrcpy-server H.264)
- **Purpose:** Deploy `scrcpy-server.jar` to capture hardware-encoded H.264 video at 60 FPS (with provisional 120 FPS support on capable devices).
- **User Value:** Drastically reduces teleoperation latency (sub-45ms) and bandwidth consumption, providing a native-feeling display.
- **Dependencies:** `scrcpy-server.jar`, browser WebCodecs API (`VideoDecoder`).
- **Platform Support:** Android Physical (API 21+), Android Virtual.
- **Complexity:** High.
- **Security Implications:** Requires pushing server JAR to `/data/local/tmp` via ADB and executing via `app_process`.
- **Acceptance Criteria:** Achieves stable 60 FPS with < 50ms latency on 1080p display on supported hardware.
- **Release Classification:** `Release 1.x`.

### F-10: Android Virtual Device (AVD) Headless Lifecycle Manager
- **Purpose:** Discover, boot, snapshot, and shut down Android emulators programmatically via CLI without Android Studio GUI.
- **User Value:** Enables fully automated CI and agent testing when physical hardware is unavailable or disconnected.
- **Dependencies:** Android SDK Command-line Tools (`emulator`, `avdmanager`).
- **Platform Support:** Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Executes local emulator processes consuming significant host CPU/RAM.
- **Acceptance Criteria:** Discovers installed AVDs; boots AVD in headless mode in < 45s; establishes ADB connection and shuts down cleanly.
- **Release Classification:** `Release 1.x`.

### F-11: Wireless ADB Discovery and Pairing
- **Purpose:** Pair and connect Android 11+ devices over local Wi-Fi network using mDNS and pairing code exchange.
- **User Value:** Untethers companion devices from physical USB cables while maintaining full teleoperation and testing capabilities.
- **Dependencies:** `adb pair`, `adb connect`, mDNS discovery.
- **Platform Support:** Android Physical (Android 11+ / API 30+).
- **Complexity:** Medium.
- **Security Implications:** Wireless ADB port exposure on local network. Requires PIN handshake authentication.
- **Acceptance Criteria:** Successfully pairs device with 6-digit PIN; establishes persistent wireless ADB session over Wi-Fi.
- **Release Classification:** `Release 1.x`.

### F-12: Apple iOS Device Discovery and Telemetry (Windows Host)
- **Purpose:** Enumerate connected iPhone/iPad devices via `usbmuxd`, extract model info, iOS version, battery telemetry, and stream syslog.
- **User Value:** Gives KELVRA visibility into connected Apple hardware for companion verification without requiring full macOS toolchains.
- **Dependencies:** `pymobiledevice3`, usbmuxd Windows service.
- **Platform Support:** iOS Physical.
- **Complexity:** Medium.
- **Security Implications:** Requires device pairing trust confirmation ("Trust This Computer").
- **Acceptance Criteria:** Discovers iPhone/iPad; reads battery percentage and serial; streams syslog entries.
- **Release Classification:** `Release 1.x`.

### F-13: Maestro Declarative UI Test Flow Execution
- **Purpose:** Execute human-readable YAML UI test scripts against Android companion applications.
- **User Value:** Standardized declarative mobile testing flows that integrate cleanly with Bench agent test plans.
- **Dependencies:** Maestro CLI runner, accessibility service.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** Medium.
- **Security Implications:** Injects high-level accessibility actions.
- **Acceptance Criteria:** Parses YAML flow, executes multi-step assertion sequence, and outputs structured failure traces.
- **Release Classification:** `Release 1.x`.

### F-14: Full iOS Interactive Screen Teleoperation & Automation
- **Purpose:** Stream live iOS screen and inject touch events using WebDriverAgent (WDA).
- **User Value:** Complete parity with Android teleoperation for Apple companion devices.
- **Dependencies:** WebDriverAgent runner, Apple Developer Codesigning Identity, macOS host or pre-signed runner.
- **Platform Support:** iOS Physical, iOS Simulator.
- **Complexity:** High.
- **Security Implications:** Developer mode certificate requirements.
- **Acceptance Criteria:** Renders iOS screen at >= 15 FPS; injects touch taps on iOS interface.
- **Release Classification:** `Future`.

### F-15: Cross-Device Multi-Screen Studio Grid
- **Purpose:** Stream and control multiple connected devices simultaneously in a tiled multi-monitor grid.
- **User Value:** Comparative testing across different screen sizes, aspect ratios, and OS versions simultaneously.
- **Dependencies:** Multi-channel WebSocket streamer, high host USB bandwidth.
- **Platform Support:** Android Physical, Android Virtual.
- **Complexity:** High.
- **Security Implications:** High host resource consumption (USB bus saturation).
- **Acceptance Criteria:** Streams 2+ devices simultaneously with synchronized broadcast inputs.
- **Release Classification:** `Future`.

### F-16: Commercial Multi-Tenant Cloud Device Farm Federation
- **Purpose:** Provision remote device sessions across distributed cloud device pools with multi-tenant billing.
- **User Value:** Massive parallel device testing across hundreds of device models.
- **Dependencies:** Heavy distributed orchestration, remote VPN tunnels, database clusters.
- **Platform Support:** Cloud Android/iOS.
- **Complexity:** Very High.
- **Security Implications:** Multi-tenant credential isolation and data wiping between sessions.
- **Acceptance Criteria:** N/A (Intentionally excluded from KELVRA scope).
- **Release Classification:** `Deferred`.
