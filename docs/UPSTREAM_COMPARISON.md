# KELVRA Device Lab — Upstream Project Comparison & Trade-Off Analysis

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/UPSTREAM_COMPARISON.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Evaluation Dimensions:** 11-Dimension Technical Rigor Framework
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Multi-Dimensional Comparison Framework

Each candidate project is evaluated against eleven architectural criteria:

| Dimension | Definition |
|---|---|
| **1. Functional Fit** | Does the candidate solve the specific requirement without extraneous bloat? |
| **2. Platform Coverage** | Does it run reliably on the Windows host and support target mobile OS versions? |
| **3. Maintenance Activity** | Is there continuous commit history, rapid security patching, and active issue triage? |
| **4. License Compatibility** | Is the license permissive (Apache/MIT/BSD) or does it impose copyleft boundaries (GPL)? |
| **5. Integration Complexity** | Can it be integrated via a clean adapter without deep invasive codebase refactoring? |
| **6. Performance** | Does it meet latency (< 45ms), frame rate (30–60 FPS), and resource (< 6% CPU) budgets? |
| **7. Security & Sandbox** | Does it operate with least privilege without creating network or host vulnerabilities? |
| **8. Dependency Footprint** | Does it require external runtimes (Node.js, Docker, databases) or run standalone? |
| **9. Extensibility** | Can it be wrapped by KELVRA's abstract `BaseDeviceProvider` interface? |
| **10. Architectural Fit** | Does it align with KELVRA's local-first, single-process, asynchronous model? |
| **11. Operational Burden** | What is the engineering cost of debugging, updating, and maintaining the integration? |

---

## 2. Upstream Comparison Matrix

| Project | Primary Domain | License | Maintenance | Host OS | Dependency Footprint | Latency / FPS | Architecture Fit |
|---|---|---|---|---|---|---|---|
| **Genymobile scrcpy** | Android Video & Control | Apache 2.0 | Very Active | Windows, macOS, Linux | Standalone jar + ADB | Sub-45ms / 60-120 FPS | Excellent (Adapter) |
| **Native ADB Screencap** | Android Fallback Video | Apache 2.0 | Active (AOSP) | Windows, macOS, Linux | Host ADB only | ~80-120ms / 15-30 FPS | Excellent (Native) |
| **DeviceFarmer STF** | Device Farm & Web | Apache 2.0 | Sporadic | Linux only (Fragile Win) | Heavy (RethinkDB, ZeroMQ, Node) | ~100-200ms / 15-25 FPS | Poor (Heavy monolithic stack) |
| **Appium Device Farm** | Automation Routing | Apache 2.0 | Active | Windows, macOS, Linux | Heavy (Node.js, Appium 2.x) | N/A (Not for streaming) | Redundant with Bench |
| **pymobiledevice3** | iOS Lockdown & Syslog | GPLv3 | Very Active | Windows, macOS, Linux | Python library | N/A (Diagnostics only) | High (Isolated Subprocess) |
| **libimobiledevice** | iOS C Library | LGPL 2.1+ | Active | Linux, macOS, Win (DLLs) | Native C toolchain | N/A (Diagnostics only) | Moderate (Build friction on Win) |
| **Appium WebDriverAgent** | iOS UI Automation | BSD 3-Clause | Active | macOS only (Host) | Xcode, CocoaPods | ~150-250ms / 15-30 FPS | Deferred (Requires macOS) |
| **adbutils** | Python ADB Socket Client | MIT | Active | Windows, macOS, Linux | Lightweight Python lib | Sub-5ms queries | High (External Dependency) |
| **uiautomator2** | Android UI Automation | MIT | Active | Windows, macOS, Linux | Android helper APK | ~50-100ms per action | High (Adapter Integration) |
| **Maestro** | Declarative Mobile Test | Apache 2.0 | Very Active | Windows, macOS, Linux | Standalone CLI | ~80-150ms per action | High (Adapter Integration) |

---

## 3. Deep-Dive Trade-Off Analysis by Subsystem

### 3.1 Android Screen Capture & Teleoperation: scrcpy vs STF vs Native ADB
- **scrcpy vs STF minicap:**
  - `minicap` was designed in the Android 4.x/5.x era, capturing unencoded virtual display frames and sending raw JPEG buffers. It requires building architecture-specific native binaries (`.so`) for every Android NDK ABI and Android API level.
  - `scrcpy` leverages modern Android `MediaCodec` and `SurfaceControl` APIs through a single Java server JAR executed via `app_process`. It requires no NDK compilation per device, supports hardware H.264/H.265 encoding, and delivers 60 FPS with dramatically lower bandwidth.
  - *Outcome:* `scrcpy` is overwhelmingly superior to STF minicap in performance, maintainability, and compatibility.
- **scrcpy vs Native ADB Screencap:**
  - Native ADB screencap is universally available and requires zero jar deployment, but CPU overhead limits it to ~15–30 FPS with ~100ms latency.
  - *Outcome:* Deploy Native ADB screencap as the zero-dependency **MVP baseline**, and upgrade to `scrcpy-server` as the high-performance **Release 1.x adapter**.

### 3.2 Apple iOS Device Communication: pymobiledevice3 vs libimobiledevice
- **pymobiledevice3:** Written in pure Python. Runs natively on Windows 10/11 without requiring MSYS2, MinGW, or complex cross-compilation. Easily installed in Device Lab's isolated virtual environment. Actively maintained by modern security researchers who promptly update protocol changes for iOS 17/18.
- **libimobiledevice:** C libraries require compiling and distributing Windows DLLs (`libimobiledevice.dll`, `libplist.dll`, `libusbmuxd.dll`), which frequently suffer from ABI mismatches and broken builds on Windows.
- *Outcome:* `pymobiledevice3` is the clear choice for Windows host environments, deployed in an isolated subprocess to maintain GPLv3 license boundaries.

### 3.3 Test Automation: Native ADB vs Maestro vs Appium
- **Appium:** Requires running a heavyweight Node.js server, installing drivers, managing mobile-json-wire protocols, and navigating high command overhead.
- **Maestro:** Modern declarative runner using human-readable YAML. It interacts with the device via ADB and accessibility dumps with built-in tolerance for mobile UI animations and layout delays.
- **Native ADB (`input tap` + `uiautomator dump`):** Zero-dependency, instantaneous execution, perfect for basic smoke tests and screenshot assertion gates.
- *Outcome:* Native ADB for **MVP**; Maestro YAML adapter for **Release 1.x**. Appium is rejected as core infrastructure.
