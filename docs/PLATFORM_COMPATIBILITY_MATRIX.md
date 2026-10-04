# KELVRA Device Lab — Platform Compatibility & Hardening Matrix

## 1. Executive Summary

KELVRA Device Lab is engineered to run as a robust standalone mobile device orchestration service across development host operating systems, interfacing with diverse mobile targets. This matrix details the verified compatibility tiers, platform-specific adaptations, and architectural hardening measures implemented through Phase 14.

---

## 2. Platform Support & Compatibility Matrix

| Platform / Target | Operating Tier | Verification Status | Key Supported Capabilities | Known Host Prerequisites |
| :--- | :--- | :--- | :--- | :--- |
| **Windows 10 / 11 Host** | Tier 1 (Primary) | Fully Verified | Native FastAPI ASGI, async I/O, subprocess management | Python 3.11+, Android Platform-Tools in PATH |
| **Linux (Ubuntu / Debian)** | Tier 1 | Architecture-Ready | Identical asyncio/FastAPI runtime, native udev USB rules | Python 3.11+, `android-tools-adb` |
| **macOS (Apple Silicon / Intel)** | Tier 1 | Architecture-Ready | Native USB device discovery, native iOS libimobiledevice | Python 3.11+, Homebrew ADB |
| **Android Physical (USB)** | Tier 1 | Fully Verified | Discovery, Streaming, Touch/Key/Text Input, Logcat, Artifacts | USB Debugging enabled, RSA key approved |
| **Android Physical (Wi-Fi)** | Tier 1 | Fully Verified | Wireless pairing & teleoperation via ADB over TCP/IP | Device on routable subnet (`adb connect`) |
| **Android Virtual (AVD)** | Tier 1 | Fully Verified | Headless VM creation, boot supervision, auto-discovery | Android SDK Emulator + System Images installed |
| **iOS / iPadOS Physical** | Tier 2 (Bridge) | Architecture-Ready | Device identity, diagnostics, pairing state, tunnel socket | Loopback daemon (`127.0.0.1:27015`) or macOS host |

---

## 3. Cross-Platform Engineering Hardening

### 3.1 Path Normalization & File Separators
- **Problem:** Windows file systems employ backslashes (`\`), whereas web endpoints, ADB shell environments, and Unix paths require forward slashes (`/`).
- **Hardening:**
  - All file path construction utilizes Python's `pathlib.Path` objects.
  - Relative artifact paths stored in `catalog.json` are explicitly converted to POSIX forward slashes via `Path.as_posix()`.
  - Artifact path validation employs strict `.resolve()` boundary checks to prevent Windows drive escapes (`C:\...`) and traversal sequences (`..`).

### 3.2 Subprocess Invocation Safety
- **Problem:** Using `shell=True` in subprocess calls introduces command injection risks and subtle behavioral discrepancies across Windows `cmd.exe`/PowerShell versus Unix shells.
- **Hardening:**
  - All command invocations (`subprocess.Popen`, `subprocess.run`, `asyncio.create_subprocess_exec`) use parameter lists (`List[str]`) with `shell=False`.
  - Binary executables (`adb.exe`, `emulator.exe`, `avdmanager.bat`) are resolved dynamically via `shutil.which()` and Android SDK environment variable discovery (`ANDROID_HOME`, `ANDROID_SDK_ROOT`).

### 3.3 Newline & Output Stream Parsing
- **Problem:** Windows ADB processes emit CRLF (`\r\n`) line endings, while mock environments or Unix pipes may emit LF (`\n`).
- **Hardening:**
  - Discovery parsers (`adb devices -l`, `avdmanager list avd`) split stdout with `.splitlines()`, automatically stripping both `\r\n` and `\n` without leaving trailing carriage returns.

### 3.4 Process Termination Signals
- **Problem:** Windows does not support Unix-style POSIX signals (`SIGINT`, `SIGHUP`) across arbitrary child process trees.
- **Hardening:**
  - Process supervisors in `RecordingManager` and `AvdManager` attempt graceful shutdown before falling back to `terminate()` and `kill()`, ensuring child processes terminate reliably on Windows without hanging.
