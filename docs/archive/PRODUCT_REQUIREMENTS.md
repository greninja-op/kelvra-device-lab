# KELVRA Device Lab — Product Requirements Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PRODUCT_REQUIREMENTS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Authority:** KELVRA Product Architecture
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Module A: Device Dashboard

### 1.1 Purpose & Scope
The Device Dashboard provides a centralized, real-time fleet overview of all connected physical and virtual mobile devices. It serves as the primary navigation and monitoring surface.

### 1.2 Functional Requirements
- **Fleet Enumeration:** Enumerate all available devices within 2 seconds of connection via ADB and platform discovery services.
- **Classification:** Distinguish physical hardware from virtual emulators (AVD) using system properties (`ro.product.model`, `ro.kernel.qemu`, `ro.hardware`).
- **Connection Status:** Track discrete connection states: `online`, `offline`, `unauthorized`, `booting`, `busy`, `error`.
- **Hardware Metadata Display:**
  - *Reliable Properties:* Manufacturer (`ro.product.manufacturer`), Model (`ro.product.model`), Serial Number / Transport ID, OS Version (`ro.build.version.release`), API Level (`ro.build.version.sdk`), Display Resolution (e.g. `1220x2712`), Pixel Density (DPI), CPU Architecture (`ro.product.cpu.abi`).
  - *Platform-Dependent Properties:* Battery level (%) and charging status (via `dumpsys battery`), device thermal state, network type (Wi-Fi, Cellular, Airplane Mode).
- **Active Session Indicator:** Display whether a device is currently engaged in an active teleoperation session, automated test execution, or idle.
- **Health Indicators:** Surface warnings if battery temperature exceeds 42°C, storage is >90% full, or battery is <15% without charging.

---

## 2. Module B: Device Discovery and Connection

### 2.1 Android Discovery
- **Transport Support:**
  - *USB Cable (Primary):* Continuous discovery via `adb devices -l` and direct ADB server socket polling (`127.0.0.1:5037`).
  - *Wireless ADB (Secondary / Phase 1.x):* Discovery via mDNS / Zeroconf (`adb mdns services`) and manual IP:port connection (`adb connect <host>:<port>`).
- **Authorization Lifecycle:**
  - When status is `unauthorized`, render an explicit actionable banner: "Device unauthorized. Please check device screen and accept RSA key fingerprint."
  - Auto-poll authorization status every 2 seconds without requiring manual page refresh.
- **Multi-Device Handling:**
  - Support multiple connected devices simultaneously. Each device is assigned an isolated session handle and internal transport lock to prevent command cross-talk.

### 2.2 Apple iOS Discovery
- **Physical iPhone / iPad:**
  - Discovery via native `usbmuxd` socket or `pymobiledevice3` client over USB.
  - Surface device name, model identifier, iOS version, serial, and pairing status.
  - Require explicit user confirmation if the device displays "Trust This Computer".
- **Platform Limitations on Windows Host:**
  - Clearly disclose that on Windows hosts, iOS discovery is restricted to device metadata, battery readings, syslog extraction, and developer image inspection. Interactive screen teleoperation and UI test automation on iOS require a macOS host or pre-signed WebDriverAgent runners.

---

## 3. Module C: Device Viewer

### 3.1 Display & Streaming Pipeline
- **Aspect-Ratio Preservation:** The display stage computes dynamic pillarbox/letterbox boundaries to render the device screen without stretching or aspect-ratio distortion.
- **Orientation Adaptation:** Automatically detect and rotate viewport when device orientation changes between Portrait (`0`, `180`) and Landscape (`90`, `270`).
- **Fullscreen & Zoom Modes:** Support 1:1 pixel mapping, Fit-to-Window, and Fullscreen modes.
- **Stream Controls:** Provide stream pause, reconnect, quality adjustment (resolution downscaling: 100%, 75%, 50%), and bitrate throttle controls.

### 3.2 High-Refresh Streaming Feasibility & Refresh Targets
- **Baseline Target (MVP):** 15–30 FPS with latency < 120ms using WebSocket binary frame streaming (JPEG/PNG compression). This ensures 100% host and device compatibility without external binary dependencies.
- **Target 60 FPS (Release 1.x):** Sub-50ms latency using `scrcpy-server` hardware MediaCodec H.264 video encoding streamed over WebSocket to browser WebCodecs (`VideoDecoder`).
- **Target 120 FPS Feasibility Evaluation:**
  - *Prerequisites:* Physical display hardware supporting 120 Hz (e.g. POCO X6 Pro 120 Hz AMOLED), host monitor capable of 120 Hz refresh rate, hardware encoder throughput supporting 120 FPS at 1080p, and low USB 3.0 controller latency.
  - *Technical Reality:* 120 FPS is feasible on supported hardware via `scrcpy-server` (`--max-fps=120`), but is **provisional** and cannot be a universal acceptance guarantee across all devices or host configurations.

---

## 4. Module D: Device Interaction (Teleoperation)

### 4.1 Input Mapping
- **Mouse Touch Emulation:**
  - *Left Click Down / Move / Up:* Mapped to normalized `(x / width, y / height)` touchscreen down, move, and up events.
  - *Click and Drag:* Mapped to smooth touchscreen swipe gestures.
  - *Mouse Scroll Wheel:* Mapped to vertical scroll drag gestures.
- **Hardware Button Emulation:**
  - Dedicated on-screen toolbar buttons for:
    - *Back:* Android `KEYCODE_BACK` (Key code 4). Also mapped to mouse right-click.
    - *Home:* Android `KEYCODE_HOME` (Key code 3). Also mapped to mouse middle-click.
    - *App Switcher / Recents:* Android `KEYCODE_APP_SWITCH` (Key code 187).
    - *Power / Sleep:* Android `KEYCODE_POWER` (Key code 26).
    - *Volume Up / Down:* Android `KEYCODE_VOLUME_UP` (24) / `KEYCODE_VOLUME_DOWN` (25).
- **Physical Keyboard Typing:**
  - Browser keyboard input captured when viewport is focused, transmitted via WebSocket, and injected via ADB text injection (`input text "<escaped_string>"`) or UTF-8 IME protocol.
- **Sensitive Operation Confirmations:**
  - Operations that can disrupt device state (reboot, wipe cache, factory reset, uninstall system apps) require a two-step confirmation modal with clear impact warnings.

---

## 5. Module E: Virtual Device Management (Android Virtual Devices)

### 5.1 CLI Integration & Lifecycle
- **AVD Discovery:** Inspect installed virtual devices via `emulator -list-avds` or `avdmanager list avd`.
- **Virtual Device Lifecycle:**
  - *Start Emulator:* Launch virtual device with headless flags (`-no-window -no-audio`) for background agent testing, or standard windowed mode.
  - *Stop / Shutdown:* Gracefully shut down emulator via `adb -s <emulator-id> emu kill`.
  - *Cold Boot vs Snapshot:* Provide options to start from a clean state (`-no-snapshot-load`) or restore from snapshot for instant startup.
- **Licensing & SDK Boundary:**
  - Device Lab does not bundle or redistribute proprietary Android SDK or emulator binaries. It leverages the developer's pre-installed Android SDK (`ANDROID_HOME` or `ANDROID_SDK_ROOT`). If the SDK is missing, Device Lab surfaces clear setup guidance.

---

## 6. Module F: Application Management

### 6.1 Package Operations
- **APK Installation:**
  - Drag-and-drop APK upload or programmatic file path installation (`adb install -r -d <path>`).
  - Support streaming install for Android 11+ (`adb install-multiple`).
- **Application Lifecycle Control:**
  - *Launch:* `monkey -p <package> -c android.intent.category.LAUNCHER 1` or explicit activity launch (`am start -n <package>/<activity>`).
  - *Force Stop:* `am force-stop <package>`.
  - *Clear Data / Cache:* `pm clear <package>` (requires confirmation).
  - *Uninstall:* `pm uninstall <package>` (requires confirmation).
- **Package Inspection:**
  - Query installed packages, filter between 3rd-party (`-3`) and system packages, extract version name, version code, and target SDK.

---

## 7. Module G: Automation and Testing

### 7.1 Automated Workflows
- **Scriptable Device Actions:** Support structured sequence definitions:
  - `tap(x, y)`
  - `swipe(x1, y1, x2, y2, duration_ms)`
  - `type_text(text)`
  - `press_key(key_code)`
  - `wait(ms)`
  - `assert_visible(text_or_selector)`
  - `capture_screenshot(checkpoint_name)`
- **Assertion Gates:** Verify UI hierarchy via UIAutomator dump (`adb exec-out uiautomator dump /dev/tty`).
- **Evidence Bundles:** Package checkpoint screenshots, logcat slices during the test window, and execution summary into an auditable JSON+ZIP report for KELVRA Ward attestation.

---

## 8. Module H: Logs and Diagnostics

### 8.1 Live Logcat Streaming
- **High-Velocity Stream:** Stream Android logcat over WebSocket using circular ring buffers (capacity: 5,000 lines).
- **Filters:**
  - Real-time text search.
  - Package / PID filtering.
  - Tag filtering.
  - Severity level filtering (Verbose, Debug, Info, Warn, Error, Fatal).
- **Performance Virtualization:** Viewport renders only visible rows using DOM virtualization to prevent browser freezing during high-rate logging.
- **Privacy & Secret Redaction:** Automated regex filter redacts API keys, bearer tokens, passwords, and private key strings before streaming to the client.

---

## 9. Module I: Device Sessions

### 9.1 Session Model
- **Single-Writer / Multiple-Reader Pattern:**
  - A device allows multiple concurrent read-only viewers (e.g. human supervisor + telemetry logger).
  - Teleoperation input and test automation lock the device to a single active writer session to prevent conflicting touch inputs.
- **Heartbeat & Resource Cleanup:**
  - Sessions maintain a 15-second heartbeat. If the client disconnects or times out, the stream pipeline, ADB socket forwards, and temporary buffers are automatically cleaned up.

---

## 10. Module J: Future Extensions Classification

| Extension | Classification | Justification |
|---|---|---|
| **Wireless ADB Pairing** | Release 1.x | High value for desk ergonomics; requires pairing code handshake |
| **H.264 WebCodecs 60 FPS** | Release 1.x | Dramatic latency and bandwidth reduction over JPEG |
| **Provisional 120 FPS Target** | Release 1.x | Requires hardware support verification |
| **Maestro YAML Runner** | Release 1.x | Declarative testing framework integration |
| **Cross-Platform iOS Teleoperation** | Future | Requires macOS runner / pre-signed WDA |
| **Multi-Device Grid View** | Future | Useful for swarm multi-device testing; high bandwidth |
| **Cloud Device Farm Federation** | Deferred | Out of scope for local-first developer bench |
| **AI Vision-Based Auto-Healing Tests** | Deferred | Belongs in KELVRA Agent runtime, not Device Lab core |

---

## 11. Performance and Reliability Requirements

### 11.1 Quantitative Targets
- **Device Discovery Time:** < 2.0 seconds from physical USB connection.
- **Connection Handshake:** < 1.0 second from device selection to stream initialization.
- **Viewer Latency (Provisional Baseline):** < 120ms (JPEG WebSocket); < 45ms (scrcpy H.264).
- **Stream Frame Rate (Provisional):** 15–30 FPS baseline; 60 FPS on hardware-accelerated H.264.
- **Host CPU Utilization:** < 8% CPU usage on modern 8-core host during active 1080p 30 FPS streaming.
- **Host Memory Consumption:** < 180 MB RSS for standalone Python backend server.
- **Session Cleanup:** < 500ms after client disconnect.
- **Stability:** Capable of running continuous 2-hour streaming and telemetry capture without memory leaks or crash.
