# iOS & iPadOS Capability Matrix
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Overview & Capability Classification Model

KELVRA Device Lab strictly adheres to truthful capability reporting. Device Lab categorizes all device features into four discrete capability tiers:

1. **SUPPORTED**: Fully functional, verified, and operational within current architecture without additional third-party dependencies.
2. **SUPPORTED_WITH_PREREQUISITES**: Operationally functional once specific host tooling or user authorization prerequisites are satisfied.
3. **EXPERIMENTAL**: Partial functionality available under restricted configurations, subject to host OS limitations or degraded performance.
4. **UNAVAILABLE**: Infeasible or architecturally unsupported on the current host operating system (e.g. Windows) due to OS-level sandboxing, missing display drivers, or Apple ecosystem restrictions.

---

## 2. Comprehensive Capability Matrix: Windows Host vs macOS Host

The table below provides a granular capability breakdown for physical iOS and iPadOS devices connecting to KELVRA Device Lab across Windows and macOS host workstations.

| Capability Identifier | Capability Name | Windows Host Status | macOS Host Status | Minimum iOS Version | Prerequisites & Required Tooling |
|---|---|---|---|---|---|
| `DISCOVERY` | Device Discovery & UDID Resolution | **SUPPORTED** | **SUPPORTED** | iOS 10+ | AMDS / usbmuxd (TCP port 27015 active) |
| `HARDWARE_METADATA` | Device Specs & Model Mapping | **SUPPORTED** | **SUPPORTED** | iOS 10+ | Device paired (`AVAILABLE` state) |
| `PAIRING_TRUST_FLOW` | Lockdown Pairing & Trust State Verification | **SUPPORTED** | **SUPPORTED** | iOS 10+ | Device screen unlocked; user accepts trust prompt |
| `BATTERY_TELEMETRY` | Battery Level & Charging Status | **SUPPORTED** | **SUPPORTED** | iOS 10+ | Device paired; `com.apple.mobile.diagnostics` |
| `STORAGE_TELEMETRY` | Disk Usage & Storage Telemetry | **SUPPORTED_WITH_PREREQUISITES** | **SUPPORTED** | iOS 10+ | `ideviceinfo` or `pymobiledevice3` installed |
| `SYSLOG_STREAMING` | Real-Time Unified System Logs | **SUPPORTED_WITH_PREREQUISITES** | **SUPPORTED** | iOS 10+ | `idevicesyslog` CLI utility on host PATH |
| `CRASH_REPORT_COLLECTION` | Crash Log Extraction | **SUPPORTED_WITH_PREREQUISITES** | **SUPPORTED** | iOS 10+ | `idevicecrashreport` CLI utility on host PATH |
| `APP_INVENTORY` | Installed Application Inspection | **SUPPORTED_WITH_PREREQUISITES** | **SUPPORTED** | iOS 10+ | `ideviceinstaller` CLI utility on host PATH |
| `SCREENSHOT_CAPTURE` | Static Frame Capture | **EXPERIMENTAL** | **SUPPORTED** | iOS 10+ (iOS 17+ tunnel required) | Developer Disk Image (DDI) mounted on target device |
| `SCREEN_STREAMING` | Low-Latency Live Screen Stream | **UNAVAILABLE** | **EXPERIMENTAL** | iOS 11+ | Requires QuickTime AVFoundation capture or pre-signed WDA |
| `TOUCH_INPUT_INJECTION` | Remote Touch & Gestures | **UNAVAILABLE** | **SUPPORTED_WITH_PREREQUISITES** | iOS 12+ | Pre-signed WebDriverAgent / XCUITest runner active |
| `KEYBOARD_INJECTION` | Remote Keystroke Injection | **UNAVAILABLE** | **SUPPORTED_WITH_PREREQUISITES** | iOS 12+ | Pre-signed WebDriverAgent / XCUITest runner active |

---

## 3. Comparison with Android Physical & Virtual Capabilities

To maintain transparency across the multi-platform fleet, the matrix below highlights the operational differences between Android and Apple devices in KELVRA Device Lab on Windows workstations:

| Subsystem Feature | Android Physical (Phase 9-10) | Android Virtual / AVD (Phase 11) | Apple Physical (Phase 12) |
|---|---|---|---|
| **Underlying Protocol** | Android Debug Bridge (`adb`) | `adb` via loopback TCP | `usbmuxd` (TCP port 27015) + `lockdownd` |
| **Discovery Mechanism** | `adb devices -l` poll + state parser | `emulator -list-avds` + process PID | usbmux ping + `%ProgramData%\Apple\Lockdown` |
| **Trust Model** | RSA Keypair (`~/.android/adbkey.pub`) | Trusted Localhost | Lockdown Pairing Record (`<UDID>.plist`) |
| **Screen Streaming** | H.264 / MJPEG via `scrcpy-server` | H.264 / MJPEG via `scrcpy-server` | **Not Supported on Windows** (Inspection Mode) |
| **Touch Injection** | `scrcpy` control socket binary protocol | `scrcpy` control socket binary protocol | **Not Supported on Windows** (No remote driver) |
| **Hardware Keys** | Keycode injection (`BACK`, `HOME`, etc.) | Keycode injection | **Not Supported on Windows** |
| **Lifecycle State Machine**| `DISCOVERED` -> `AVAILABLE` <-> `CONNECTED` | `REGISTERED` -> `BOOTING` -> `ONLINE` | `DISCOVERED` -> `AVAILABLE` (or `UNAUTHORIZED`) |
| **Operator Lease Control**| Exclusive token-based lease lock | Exclusive token-based lease lock | Read-only inspection / Telemetry monitoring |

---

## 4. UI Representation of Capabilities

In the KELVRA Device Lab user interface:
1. **Badges**: Apple physical devices are clearly identified with the `Apple Physical` badge and styled with the accent tint.
2. **Action Triggers**: The primary action button for available Apple devices reads **Inspect Device** rather than **View Screen**.
3. **Viewer Studio**: Opening an Apple device transitions the Studio into **Inspection Mode**, rendering device hardware specifications, OS build details, and trust state while disabling stream negotiation and touch controls.
4. **Unauthorized Banner**: When a device is locked with a passcode or awaiting user trust confirmation, an informative recovery banner instructs: *"Trust Required: Unlock your iPhone/iPad and tap 'Trust This Computer' on the screen."*
