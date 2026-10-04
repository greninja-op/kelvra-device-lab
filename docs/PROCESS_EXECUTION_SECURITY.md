# KELVRA Device Lab — Process Execution Security & Isolation Standards

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PROCESS_EXECUTION_SECURITY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Subprocess Security & Host OS Execution Policy
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Process Execution Security Principles

Device Lab interacts with underlying toolchains by spawning local child subprocesses. To ensure host system stability, prevent command injection, and block privilege escalation:

1. **Zero Shell String Concatenation (`shell=False` Invariant):** All child processes are spawned exclusively with structured argument arrays (e.g. `["adb", "-s", serial, "shell", "input", "tap", x, y]`). Shell interpreters (`cmd.exe`, `powershell.exe`, `/bin/sh`) are strictly forbidden as intermediary runners.
2. **Explicit Executable Allowlist:** Subprocesses may only invoke verified executables matching an explicit allowlist. Arbitrary binaries cannot be executed.
3. **Least Privilege User Execution:** The entire application runs as a standard, unprivileged user process. It does **not** run as Administrator on Windows or root on POSIX systems.
4. **Deterministic Lifetime & Orphan Prevention:** All spawned child processes are tracked in an active PID registry and tied to host OS termination jobs.

---

## 2. Approved Executable Allowlist & Verification

| Binary Identifier | Canonical Location / Source | Verification Mechanism | Permitted Invocations |
|---|---|---|---|
| **`adb.exe`** | Host Platform Tools (`PATH` or `ANDROID_HOME`) | Version verification (`adb version`) | Device enumeration, forward, install, logcat, input |
| **`emulator.exe`** | Host Android SDK (`$ANDROID_SDK_ROOT/emulator/`) | Version verification (`emulator -version`) | Headless AVD start, snapshot, shutdown |
| **`avdmanager.bat`** | Host Android SDK Tools (`$ANDROID_SDK_ROOT/cmdline-tools/`) | SDK path check | List virtual devices |
| **`scrcpy-server.jar`**| Local `assets/scrcpy-server-v2.4.jar` | Cryptographic SHA-256 hash match | Pushed to `/data/local/tmp` via ADB and run via `app_process` |
| **`pymobiledevice3.exe`** | Dedicated Python Virtual Environment (`venv/Scripts/`) | Executable path resolution | Lockdown query, syslog stream (CLI subprocess only) |

Any attempt to invoke an unlisted binary (e.g. `curl.exe`, `powershell.exe`, `net.exe`, `bash`) is rejected immediately with a security fault.

---

## 3. Working Directory & Environment Variable Jailing

- **Restricted Working Directory:** All child processes execute with their current working directory (`cwd`) set strictly to Device Lab's dedicated scratch directory:
  `Kelvra/KELVRA Device Lab/scratch/`
- **Sanitized Environment Variables:** Subprocesses do not inherit arbitrary host shell environments. Child process environments are constructed from a sanitized dictionary:
  ```python
  SAFE_ENV = {
      "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
      "PATH": sanitized_path,
      "ANDROID_HOME": os.environ.get("ANDROID_HOME", ""),
      "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT", ""),
      "TEMP": str(SCRATCH_DIR),
      "TMP": str(SCRATCH_DIR)
  }
  ```
  Sensitive credentials, parent session tokens, and unrelated environment variables are stripped.

---

## 4. Execution Guardrails: Timeouts & Output Buffering

- **Hard Process Timeouts:** Every spawned subprocess is bound by an explicit `asyncio.wait_for` deadline:
  - Standard command (tap, metadata query, keyevent): `3.0 seconds`.
  - Heavy operation (screenshot capture, app launch): `8.0 seconds`.
  - Package installation (`adb install`): `45.0 seconds`.
  - Emulator boot (`emulator -avd`): `60.0 seconds`.
- **Output Stream Size Caps:** When capturing stdout/stderr from child processes, output streams enforce a maximum memory buffer cap of **10 Megabytes**. If an errant process produces unbounded output, the pipe consumer halts and terminates the process with `OutputLimitExceededError`.
- **Exit Code Verification:** Non-zero exit codes are inspected, mapped to structured error codes, and sanitized before returning to API clients, ensuring raw system paths or stack traces are not leaked.
