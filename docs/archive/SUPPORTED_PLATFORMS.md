# KELVRA Device Lab — Supported Platforms & Platform Honesty Matrix

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SUPPORTED_PLATFORMS.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Host Operating Systems

| Host OS | Architecture | Support Tier | Prerequisites | Capabilities Supported | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Windows 11** | x86_64 / AMD64 | **Tier 1 (Primary)** | Python 3.10+, ADB 1.0.41+, AMDS service | Full Android Physical, Full AVD, iOS Inspection Mode | Primary development & verification target |
| **Windows 10** | x86_64 / AMD64 | **Tier 1 (Supported)** | Python 3.10+, ADB 1.0.41+, AMDS service | Full Android Physical, Full AVD, iOS Inspection Mode | Identical runtime behavior to Windows 11 |
| **Linux (Ubuntu 22.04+ LTS)** | x86_64, aarch64 | **Tier 2 (Compatible)** | Python 3.10+, `android-tools-adb`, `usbmuxd` | Full Android Physical, Full AVD, iOS Inspection Mode | Headless AVD requires KVM virtualization |
| **macOS (Sonoma 14+)** | Apple Silicon, Intel | **Tier 2 (Compatible)** | Python 3.10+, Android Platform Tools | Full Android Physical, Full AVD, iOS Inspection Mode | Native macOS streaming hooks planned for v1.1 |

---

## 2. Target Device Platforms

### 2.1 Android Physical Hardware

- **Supported OS Versions:** Android 8.0 (Oreo, API 26) through Android 15 (Vanilla Ice Cream, API 35).
- **Architectures:** arm64-v8a, armeabi-v7a, x86_64.
- **Connection Transports:** USB Debugging, Wi-Fi ADB (`adb connect <ip>:<port>`).
- **Prerequisites:** USB Debugging enabled in Developer Options; host computer RSA key authorized on device.
- **Capabilities Matrix:**
  - Device Discovery: **SUPPORTED** (3-second continuous ADB polling)
  - Hardware & Battery Introspection: **SUPPORTED** (`getprop`, `dumpsys battery`)
  - Screen Streaming: **SUPPORTED** (WebSocket JPEG / WebCodecs H.264 up to 30 FPS)
  - Input Injection: **SUPPORTED** (Touch, swipe, text, hardware keycodes)
  - Single-Writer Lease Exclusivity: **SUPPORTED** (HTTP 409 conflict prevention)
  - Screen Recording: **SUPPORTED** (`screenrecord` container with SIGINT finalization)
  - Screenshot Capture: **SUPPORTED** (`screencap -p` with LANCZOS downsampling)
  - Live Logcat: **SUPPORTED** (Circular 2,000-line buffer with credential scrubbing)

---

### 2.2 Android Virtual Devices (AVD)

- **Supported System Images:** Google APIs, Google Play system images (x86_64, arm64).
- **API Levels:** API 28 (Pie) through API 35.
- **Prerequisites:** Android SDK installed with `emulator.exe`, `avdmanager.bat`, and valid system image.
- **Capabilities Matrix:**
  - AVD Inventory Scanning: **SUPPORTED** (Headerless INI configuration parsing)
  - Headless Process Launch: **SUPPORTED** (`-no-window -no-audio -no-snapshot`)
  - Windowed Process Launch: **SUPPORTED** (Standard emulator GUI)
  - Boot Tracking: **SUPPORTED** (Non-blocking loop checking `sys.boot_completed=1`)
  - Port Allocation: **SUPPORTED** (Dynamic stepping from 5554, 5556 to prevent collisions)
  - Studio Streaming & Input: **SUPPORTED** (Registers automatically as `AVAILABLE`)
  - AVD Creation & Deletion: **SUPPORTED** (Path-traversal defended, confirmed deletion)

---

### 2.3 Apple iOS & iPadOS Physical Devices

- **Supported OS Versions:** iOS 14.0 through iOS 18.x.
- **Supported Formats:** iPhone (iPhone 8 through iPhone 16 Pro Max), iPad (iPad 5th gen through iPad Pro M4).
- **Connection Transports:** USB connection to Windows host with active Apple Mobile Device Support (AMDS) daemon.
- **Prerequisites:** "Trust This Computer" confirmed on device screen with passcode entered.
- **Capabilities Matrix:**
  - USB Device Discovery: **SUPPORTED** (Native loopback TCP 27015 polling)
  - Lockdown Store Parsing: **SUPPORTED** (`%ProgramData%\Apple\Lockdown` record extraction)
  - Model Identification: **SUPPORTED** (30+ generation hardware mapping)
  - Battery & OS Telemetry: **SUPPORTED** (Live status from lockdown query)
  - Pairing State FSM: **SUPPORTED** (Passcode-locked maps to `UNAUTHORIZED`)
  - Screen Streaming on Windows: **UNSUPPORTED** (Honest HTTP 400 rejection; no fake streams)
  - Touch Injection on Windows: **UNSUPPORTED** (Honest HTTP 400 rejection)
  - Screen Recording on Windows: **UNSUPPORTED** (Honest HTTP 400 rejection)
  - Inspection Mode: **SUPPORTED** (Full hardware overview, UDID, battery, pairing diagnostics)

---

## 3. Platform Honesty Standard

KELVRA Device Lab enforces a strict platform honesty policy:
1. **Zero Simulated Frames:** If a platform or transport cannot deliver authentic screen captures, the system displays an honest "Inspection Mode" badge and provides technical rationale rather than generating fake or looped frames.
2. **Zero Fake Touch Events:** If input cannot be injected directly into the operating system kernel, input endpoints return HTTP 400 Bad Request with an explicit error description.
3. **Transparent Capability Matrix:** Every device reports its exact capability set via `/api/devices/{id}` so clients (such as KELVRA Bench) know in advance which actions are valid.
