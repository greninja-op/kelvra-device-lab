# Android Virtual Device (AVD) Creation & Validation Workflow

## 1. Overview
Automated virtual device provisioning allows KELVRA Device Lab operators to spin up cleanly configured emulators on demand. Because `avdmanager` creates persistent files on the host filesystem and can execute interactive CLI prompts, the creation workflow must enforce strict input sanitization, non-interactive pipeline automation, and post-creation validation.

This document details the multi-stage creation pipeline implemented in `AvdManager.create_avd()`.

---

## 2. Pipeline Sequence Diagram

```
[Web UI / Client]
       |
       |  POST /api/avd/create { name, package, ... }
       v
+--------------------------------------------------------------+
| 1. Input Sanitization & Path Traversal Guard                 |
|    - Regex: ^[a-zA-Z0-9_\-\.]+$                              |
|    - Path Traversal: ".." rejected (400 Bad Request)         |
+--------------------------------------------------------------+
       |
       v
+--------------------------------------------------------------+
| 2. Duplicate Detection                                       |
|    - Probes ~/.android/avd/<name>.ini                        |
|    - If exists & force=False -> 409 Conflict                 |
+--------------------------------------------------------------+
       |
       v
+--------------------------------------------------------------+
| 3. SDK & Image Precondition Verification                     |
|    - avdmanager executable must exist                        |
|    - Requested package image must exist in system-images/    |
+--------------------------------------------------------------+
       |
       v
+--------------------------------------------------------------+
| 4. Subprocess Execution & Automated Pipe Answering           |
|    - avdmanager create avd -n <name> -k <package> ...        |
|    - stdin.write(b"no\n") (Disables custom hardware prompt)   |
|    - Process timeout: 60s                                    |
+--------------------------------------------------------------+
       |
       v
+--------------------------------------------------------------+
| 5. Post-Creation Configuration Overrides                     |
|    - Append hw.ramSize and sdcard.size to config.ini         |
|    - Validate <name>.ini was written successfully            |
+--------------------------------------------------------------+
       |
       v
 [201 Created] -> Returns AvdConfig representation
```

---

## 3. Input Validation Rules
User-supplied inputs are subject to strict boundary checks prior to spawning any operating system process:

1. **AVD Name Validation**:
   - Must match regex `^[a-zA-Z0-9_\-\.]+$`.
   - Must NOT contain path traversal tokens (`..`, `/`, `\`).
   - Must NOT exceed 64 characters in length.
2. **Package Name Validation**:
   - Must conform to Android SDK package naming syntax (e.g. `system-images;android-34;google_apis;x86_64`).
   - Must correspond to a directory verified on disk inside `<SDK_ROOT>/system-images/`.
3. **RAM & SD Card Allocation Bounds**:
   - `ram_size_mb`: Must fall within range `[512, 16384]` MB.
   - `sdcard_size_mb`: Must fall within range `[128, 65536]` MB.

---

## 4. Non-Interactive CLI Automation
The standard `avdmanager create avd` tool prompts the user on `stdin`:
`Do you wish to create a custom hardware profile? [no]`

In an automated server environment without a TTY, this prompt hangs indefinitely if stdin is left unhandled.

Device Lab solves this deterministically:
1. Spawns `asyncio.create_subprocess_exec` with `stdin=asyncio.subprocess.PIPE`.
2. Emits `b"no\n"` immediately upon stream readiness via `proc.communicate(input=b"no\n")`.
3. Sets a safety timeout of 60 seconds.
4. Checks returncode: if non-zero, captures stderr and raises a formatted `RuntimeError`.

---

## 5. Safe Deletion Workflow
Deletion of an AVD permanently erases all associated user data, application installs, and virtual snapshots.

To protect against accidental data loss:
1. **Mandatory Confirmation**: `DELETE /api/avd/{name}?confirm=true` requires explicit query parameter `confirm=true`. Requests without confirmation are rejected with `400 Bad Request`.
2. **Active Instance Guard**: If an emulator is currently running or booting with that name, deletion is rejected with `409 Conflict`. The instance must be stopped first.
3. **Double Verification**: Both the `.ini` pointer and the target `.avd` directory are safely unlinked and removed recursively using `shutil.rmtree`.
