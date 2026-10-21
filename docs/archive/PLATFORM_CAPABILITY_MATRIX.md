# KELVRA Device Lab — Platform Capability Matrix

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PLATFORM_CAPABILITY_MATRIX.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Host Environment Context:** Windows 10/11 Host Workstation with Android SDK platform-tools
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Capability States Definition

Every capability in this matrix is classified into one of six rigorous technical states:
- **`Supported`:** Verified, fully functional on the target platform using available host toolchains with no non-standard prerequisites.
- **`Supported with prerequisites`:** Functional provided explicit prerequisites are satisfied (e.g. developer mode, USB debugging authorization, pairing confirmation, or pre-installed SDK components).
- **`Limited`:** Partially functional; specific features, frame rates, or control mechanisms are constrained by operating system or host boundaries.
- **`Research required`:** Feasibility is established in literature or open source, but concrete implementation requires host profiling or protocol reverse engineering.
- **`Not supported`:** Cannot be achieved on the current host architecture due to hard OS, hardware, or licensing boundaries (e.g. running iOS Simulator on Windows).
- **`Deferred`:** Intentionally postponed to future phases or out of scope for the local-first KELVRA workstation.

---

## 2. Platform Capability Matrix

| Capability Area | Android Physical Hardware | Android Virtual Device (AVD) | iPhone / iPad Physical Hardware | Apple iOS Simulator |
|---|---|---|---|---|
| **Device Discovery** | `Supported with prerequisites` (USB debugging enabled; RSA key authorized) | `Supported` (Automatic via local ADB emulator daemon port scan) | `Supported with prerequisites` (Requires usbmuxd service + "Trust This Computer" confirmation) | `Not supported` (Requires macOS host with Xcode Developer Tools) |
| **Hardware Telemetry** | `Supported` (Real CPU, RAM, battery %, charging state, temperature via `dumpsys`) | `Limited` (Emulated battery/thermals; reported values are synthetic) | `Supported with prerequisites` (Battery, cycle count, serial, thermals via `pymobiledevice3` lockdown) | `Not supported` (Synthetic host-bound metrics only; macOS required) |
| **Live Screen Viewing (Baseline)** | `Supported` (15-30 FPS via WebSocket JPEG frames / ADB screencap) | `Supported` (15-30 FPS via WebSocket JPEG frames / ADB screencap) | `Research required` (Requires MJPEG streaming via usbmuxd or WDA HTTP endpoint) | `Not supported` (No iOS Simulator runtime exists on Windows host) |
| **Live Screen Viewing (High-FPS H.264)** | `Supported with prerequisites` (60 FPS via `scrcpy-server` MediaCodec; 120 FPS provisional) | `Supported with prerequisites` (60 FPS via `scrcpy-server` with host GPU acceleration) | `Deferred` (Requires macOS AVFoundation video bridge or low-level AirPlay receiver) | `Not supported` (macOS only) |
| **Touch Interaction & Gestures** | `Supported` (Normalized coordinates via `input tap`, `input swipe`, or scrcpy socket) | `Supported` (Normalized coordinates via `input tap`, `input swipe`, or emulator pipe) | `Deferred` (Requires XCUITest WebDriverAgent runner with developer certificate) | `Not supported` (macOS only) |
| **Keyboard & Text Input** | `Supported` (Keycodes via `input keyevent`; UTF-8 text via `input text` or ADB IME) | `Supported` (Keycodes and text via ADB or QEMU console) | `Deferred` (Requires active WebDriverAgent typing session) | `Not supported` (macOS only) |
| **Hardware Button Emulation** | `Supported` (Back, Home, Recents, Power, Volume via Android keycodes) | `Supported` (Back, Home, Recents, Power, Volume via Android keycodes) | `Limited` (Volume/Lock via lockdown service; Home requires assistive touch or WDA) | `Not supported` (macOS only) |
| **Application Installation** | `Supported with prerequisites` (`adb install -r -d`; install-multiple for split APKs) | `Supported` (`adb install -r -d` directly to emulator data partition) | `Limited` (Developer IPA installation requires enterprise cert or free dev profile via `pymobiledevice3`) | `Not supported` (macOS only) |
| **Application Lifecycle Control** | `Supported` (`am start`, `am force-stop`, `pm clear`, `pm uninstall`) | `Supported` (`am start`, `am force-stop`, `pm clear`, `pm uninstall`) | `Limited` (App launch/kill via mobile_image_mounter / DDI or WDA) | `Not supported` (macOS only) |
| **Real-Time Logs & Diagnostics** | `Supported` (Live logcat stream via `adb logcat -v time` with regex/tag filters) | `Supported` (Live logcat stream via `adb logcat -v time` with regex/tag filters) | `Supported with prerequisites` (Real-time syslog extraction via `pymobiledevice3 syslog`) | `Not supported` (macOS only) |
| **Screenshot & Video Recording** | `Supported` (High-res uncompressed PNG capture; MP4 recording via `screenrecord`) | `Supported` (High-res uncompressed PNG capture; MP4 recording via `screenrecord`) | `Supported with prerequisites` (PNG capture via screenshotr developer service) | `Not supported` (macOS only) |
| **UI Automation & Assertions** | `Supported` (UI hierarchy dump via `uiautomator dump` or Maestro integration) | `Supported` (UI hierarchy dump via `uiautomator dump` or Maestro integration) | `Deferred` (Requires full XCUITest runner infrastructure) | `Not supported` (macOS only) |
| **Virtual Device Lifecycle** | `Not applicable` (Physical device) | `Supported with prerequisites` (Headless cold/warm boot and shutdown via `emulator` CLI) | `Not applicable` (Physical device) | `Not supported` (macOS only) |

---

## 3. Technical Basis and Platform Restrictions

### 3.1 Android Physical vs Virtual Parity
- **Physical Advantage:** Accurately exercises hardware-backed security (Android Keystore P-256 key generation, hardware-backed AES-256-GCM encryption), on-device speech models (Google SODA, whisper-onnx), Bluetooth LE advertising, real battery drain, and thermal throttling.
- **Virtual Advantage:** Clean snapshot rollback, deterministic fresh test states, headless execution in background environments without occupying physical desk space or USB cables.

### 3.2 Apple iOS on Windows Host Reality
- **Clear Demarcation:** Physical iPhone and iPad devices connected via USB can be enumerated, inspected, and monitored for battery/thermal health, and have their diagnostic syslog streamed via `pymobiledevice3` over `usbmuxd`.
- **Hard Platform Boundary:** Running an Apple iOS Simulator is strictly bound to macOS by Apple licensing and architecture (Darwin kernel, Metal, Cocoa). It cannot run natively on Windows.
- **Teleoperation Boundary:** Interactive screen teleoperation and UI test automation on iOS require compiled XCUITest test runners (such as Appium WebDriverAgent) signed with an active Apple Developer Certificate. This capability is classified as `Deferred` for future macOS-hosted integration agents.
