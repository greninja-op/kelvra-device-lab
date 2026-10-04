# KELVRA Device Lab — Failure Models & Recovery Matrix

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/FAILURE_AND_RECOVERY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Authority:** Resilience, Error Handling & Fault Isolation
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Resilience Philosophy

Device Lab operates against volatile physical hardware and developer tools that can disconnect, crash, or enter unauthorized states without warning. 

The system adheres to four resilience rules:
1. **Never Crash the Host Server:** A failure in an individual device, streaming socket, or child process is isolated at the provider layer.
2. **Deterministic Cleanup Before Retry:** Resources (ADB forwards, socket handles, child PIDs) are explicitly torn down before any reconnection attempt is initiated.
3. **Bounded Retries (No Loops):** Automated retries are bounded to a maximum of 3 attempts with exponential backoff.
4. **Zero Destructive Duplication:** Operations that modify state (e.g. app data clear, test runs) are **never** retried automatically.

---

## 2. Comprehensive Failure Models & Recovery Matrix

| Failure Scenario | Detection Mechanism | FSM State Transition | User-Facing Message | Cleanup Behavior | Retry Policy | Manual Action Required? |
|---|---|---|---|---|---|---|
| **1. Physical Device Unplugged** | ADB transport EOF / socket close / discovery poller drops serial. | `STREAMING` / `ONLINE -> UNAVAILABLE -> [*]` | "Device disconnected. Reconnect USB cable to resume." | Closes video WebSocket, removes port forward, halts telemetry poller, reaps child processes within <= 500ms. | 0 retries. Waits for physical reconnect. | Yes (re-plug cable). |
| **2. ADB Daemon Unavailable** | Connection refused on `127.0.0.1:5037`. | `ALL -> ERROR` | "ADB server unavailable. Ensure Android Platform Tools are installed and running." | Resets internal provider pools; logs fatal diagnostic event. | 3 retries (1s, 2s, 4s). Attempts `adb start-server`. | If retries fail, user must start ADB. |
| **3. Device Unauthorized** | `adb devices` reports status `unauthorized`. | `DISCOVERED -> UNAUTHORIZED` | "Device unauthorized. Please accept RSA fingerprint on device screen." | Suspends stream initialization; polls authorization state every 2s. | Infinite non-blocking background poll (2s cadence). | Yes (tap 'Allow' on device screen). |
| **4. Emulator Boot Failure** | `emulator.exe` exits with non-zero code or times out (> 60s). | `CONNECTING -> ERROR` | "Virtual device failed to boot: [stderr details]." | Kills orphan QEMU process via PID; deletes temporary lockfiles. | 1 retry with clean snapshot; then aborts. | No unless image is corrupted. |
| **5. Streaming Subprocess Crash** | `scrcpy-server` process pipe emits EOF or non-zero exit code. | `STREAMING -> CONNECTED` | "Video stream interrupted. Attempting fallback stream..." | Tears down forwarded port; clears frame buffer. | 1 retry; then falls back to baseline JPEG streaming. | No (automatic fallback). |
| **6. Logcat Process Crash** | `adb logcat` pipe closes unexpectedly. | No FSM change (background service) | Inline status badge: "Logcat stream reconnecting..." | Drains residual buffer; flushes ring buffer. | Auto-restarts logcat subprocess after 1s delay (max 3 retries). | No. |
| **7. Automation Suite Timeout** | Test step execution exceeds 45s deadline. | `BUSY -> ERROR` | "Test execution timed out during step [step_name]." | Dispatches `am force-stop` on target app; captures crash screenshot. | 0 retries (destructive safety). | No. |
| **8. Host Resource Exhaustion** | Host available RAM < 500 MB or CPU pegged at 100%. | `STREAMING -> CONNECTED` | "High host resource pressure. Streaming throttled." | Drops frame rate to 10 FPS; suspends non-essential telemetry. | Resumes full rate when host memory recovers. | Recommended to close heavy host apps. |
| **9. Device Reboot During Session** | ADB connection lost, followed by device entering `offline` then `bootloader/recovery`. | `STREAMING -> UNAVAILABLE -> DISCOVERED` | "Device rebooting. Waiting for system boot completion..." | Full session teardown; waits for `sys.boot_completed=1`. | Auto-reconnects when boot completes. | No. |
| **10. Host Server Sudden Shutdown** | `SIGTERM` / `SIGINT` caught by FastAPI lifecycle. | `ALL -> DISCONNECTING -> [*]` | WebSocket broadcast: "Server shutting down." | `atexit` kills all child subprocesses; checkpoints SQLite WAL file. | Immediate clean shutdown within 1.5s. | No. |

---

## 3. Post-Crash Recovery & Orphan Reaping

When Device Lab starts up, it executes an initial **orphan cleanup pass**:
1. Checks for lingering `scrcpy-server` forward rules via `adb forward --list` and removes rules matching `tcp:8098-*`.
2. Inspects running processes for orphaned child processes matching `scrcpy` or `adb logcat` spawned by previous sessions and terminates them cleanly.
3. Resets all device reservation leases in SQLite to `RELEASED`.
