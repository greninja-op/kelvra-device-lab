# Android SDK Environment Discovery & Resolution

## 1. Overview
The Android Virtual Device (AVD) subsystem in KELVRA Device Lab requires access to specific toolchains provided by the Android Software Development Kit (SDK). Because Device Lab adheres to strict self-containment and zero-unapproved-binary-redistribution policies, all Android toolchains must be detected dynamically on the host machine rather than bundled within the project repository.

This document describes the environment discovery mechanism, search precedence, binary resolution contracts, and fallback guidance when host toolchains are incomplete.

---

## 2. Environment Variables & Directory Precedence
The `SdkEnvironmentDetector` probes the host operating system using the following hierarchical discovery order:

1. **Explicit Custom SDK Root**: If passed via configuration or test fixtures (`custom_sdk_root`).
2. **Standard Environment Variables**:
   - `ANDROID_HOME`: Legacy standard path.
   - `ANDROID_SDK_ROOT`: Modern official standard path.
3. **Platform Default Locations**:
   - **Windows**: `%LOCALAPPDATA%\Android\Sdk` (e.g. `C:\Users\<User>\AppData\Local\Android\Sdk`).
   - **macOS / Linux**: `$HOME/Android/Sdk` or `$HOME/Library/Android/sdk`.
4. **AVD Home Directory**:
   - `ANDROID_AVD_HOME` environment variable if defined.
   - Fallback to standard `$HOME/.android/avd` (or `%USERPROFILE%\.android\avd` on Windows).

```
   +-------------------------------------------------------------+
   |                  SdkEnvironmentDetector                     |
   +-------------------------------------------------------------+
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
  [1] Custom SDK Root (tests)           [2] Environment Variables
                                            ANDROID_SDK_ROOT
                                            ANDROID_HOME
                                                  |
                                                  v
                                        [3] Platform Default
                                            Windows: %LOCALAPPDATA%/Android/Sdk
                                            POSIX:   ~/Android/Sdk
```

---

## 3. Toolchain Binary Resolution
Within the resolved SDK root, the detector identifies and verifies the executable permissions of the following critical utilities:

| Tool | Relative Path (Windows) | Relative Path (POSIX) | Subsystem Function |
|---|---|---|---|
| `adb` | `platform-tools/adb.exe` | `platform-tools/adb` | Device transport, shell commands, boot polling |
| `emulator` | `emulator/emulator.exe` | `emulator/emulator` | Hypervisor engine, headless QEMU virtualization |
| `avdmanager` | `cmdline-tools/latest/bin/avdmanager.bat` | `cmdline-tools/latest/bin/avdmanager` | AVD configuration creation and deletion |
| `sdkmanager` | `cmdline-tools/latest/bin/sdkmanager.bat` | `cmdline-tools/latest/bin/sdkmanager` | System image package inspection and license verification |

### Legacy Path Fallbacks
If `cmdline-tools/latest` is not present, the detector searches:
- `cmdline-tools/<version>/bin/avdmanager` (discovering the latest version directory).
- `tools/bin/avdmanager` (legacy Android SDK tools directory).

If a custom SDK root is NOT specified, the detector falls back to `shutil.which("<tool>")` to discover tools exposed directly on the host system `PATH`. When an explicit `custom_sdk_root` is passed, system `PATH` resolution is strictly bypassed to ensure deterministic test isolation.

---

## 4. System Image Discovery
The emulator cannot launch an AVD without an installed system image. The detector inspects the `system-images/` directory within the SDK:

```
<SDK_ROOT>/system-images/
  └── android-34/
      └── google_apis/
          └── x86_64/
              ├── system.img
              ├── ramdisk.img
              └── source.properties
```

The detector traverses up to 3 directory tiers (`system-images/<api>/<variant>/<abi>`) and maps detected paths to standard Android package identifiers:
`system-images;<api>;<variant>;<abi>` (e.g. `system-images;android-34;google_apis;x86_64`).

---

## 5. Status Reporting & Host Guidance
When toolchains or images are missing, the detector does not crash or raise fatal errors. Instead, it compiles an `SdkEnvironmentStatus` object with concrete remediation guidance for the operator:

```json
{
  "sdk_detected": true,
  "sdk_root": "C:\\Users\\User\\AppData\\Local\\Android\\Sdk",
  "adb_available": true,
  "adb_path": "C:\\Users\\User\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
  "emulator_available": false,
  "emulator_path": null,
  "avdmanager_available": true,
  "sdkmanager_available": true,
  "system_images": [],
  "avd_home_dir": "C:\\Users\\User\\.android\\avd",
  "guidance": [
    "Install Android Emulator via SDK Manager: sdkmanager \"emulator\"",
    "Download at least one system image: sdkmanager \"system-images;android-34;google_apis;x86_64\""
  ]
}
```

The Web UI surfaces this guidance in a dedicated setup strip within the AVD Hub, preventing silent failures.
