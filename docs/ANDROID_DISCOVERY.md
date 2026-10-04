# KELVRA Device Lab — Android ADB Discovery Specification

## 1. Overview

The `AndroidDeviceProvider` handles native detection, status classification, and hardware property extraction for Android physical hardware, virtual emulators, and network TCP/IP endpoints.

---

## 2. ADB Path Resolution Strategy

The provider locates the ADB executable using the following deterministic search priority:
1. Custom path explicitly supplied in constructor (`adb_path`).
2. Environment variable `ADB_PATH` (if defined and points to valid file).
3. System `PATH` via `shutil.which("adb")`.
4. Standard Windows Android SDK path: `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe`.
5. Standard Linux/macOS paths: `~/Android/Sdk/platform-tools/adb`.

If no valid executable is resolved, the provider transitions to `status=UNAVAILABLE` and emits descriptive diagnostics without crashing.

---

## 3. Subprocess Execution & Security

All external commands executed by `AndroidDeviceProvider` comply with the security architecture defined in Phase 5:
- **`shell=False`:** Prohibits shell expansion to prevent command injection vulnerabilities.
- **Strict Timeouts:** `devices -l` queries timeout after 5.0 seconds; `getprop` queries timeout after 3.0 seconds.
- **Fail-Closed:** Subprocess exceptions (`TimeoutExpired`, `FileNotFoundError`, `OSError`) are caught and logged without propagating uncaught exceptions to the HTTP server.

---

## 4. ADB Devices Parsing Specification

Output from `adb devices -l` is processed line-by-line:
```text
List of devices attached
8TCABAIFWOZTDICI       device usb:1-1 product:oriole model:Pixel_6 device:oriole
192.168.1.105:5555     device product:coral
emulator-5554          device product:sdk_gphone64_x86_64
R58M32B123A            unauthorized usb:1-2
OFFLINE1234            offline usb:1-3
```

### Parsing Rules
1. **Header Stripping:** First line ("List of devices attached") is ignored.
2. **Serial & Status:** Token 0 is hardware serial; Token 1 is raw state (`device`, `unauthorized`, `offline`).
3. **Transport Classification:**
   - Serial matching `^\d+\.\d+\.\d+\.\d+:\d+$` -> `transport = WIFI`.
   - Serial starting with `emulator-` -> `transport = EMULATOR_PIPE`, `platform = ANDROID_VIRTUAL`.
   - All others -> `transport = USB`, `platform = ANDROID_PHYSICAL`.
4. **Hardware Introspection:** For devices in `device` state, static properties (`ro.product.manufacturer`, `ro.product.model`, `ro.build.version.release`, `ro.build.version.sdk`, `ro.product.cpu.abi`) are read via `getprop` and cached per serial.
5. **Unauthorized Handling:** Devices reporting `unauthorized` transition to `UNAUTHORIZED` state with clear user guidance ("Unlock device screen and tap 'Allow USB debugging' prompt").
