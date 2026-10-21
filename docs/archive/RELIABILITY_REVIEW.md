# KELVRA Device Lab — Reliability Engineering & Failure Recovery Review

## 1. Overview

Reliability in KELVRA Device Lab ensures uninterrupted system availability, graceful degradation during hardware disconnections or communication failures, self-healing background tasks, and zero unhandled exceptions. This review documents the reliability architecture and failure recovery mechanisms implemented across the platform.

---

## 2. Failure Scenarios & Recovery Protocols

### 2.1 Hardware Disconnection During Active Streaming
- **Failure Trigger:** Physical USB detachment, Wi-Fi link drop, or AVD termination while a user is actively viewing a screen stream.
- **Detection:** In `DeviceStreamSession._capture_loop`, consecutive screenshot failures are tracked. Upon 5 consecutive failures, `handle_device_disconnect()` is invoked. Alternatively, provider background sweeps detect missing serials and invoke `notify_device_disconnected()`.
- **Mitigation:**
  1. The capture loop task is cancelled immediately to prevent repeated failing I/O calls.
  2. The session state transitions to `DEVICE_DISCONNECTED`.
  3. A structured JSON error notification (`{"type": "error", "code": "DEVICE_DISCONNECTED", ...}`) is broadcast to all active WebSocket clients.
  4. Client UI displays an explicit disconnected overlay with a reconnect trigger.

### 2.2 Hardware Disconnection During Video Recording
- **Failure Trigger:** Device unplugged while `screenrecord` or capture stream is active.
- **Handling:** `recording_manager.handle_device_disconnected(serial)` terminates the recording subprocess gracefully (SIGINT/SIGTERM), reaps the output file, finalizes the artifact record with `RecordingState.STOPPED`, and logs the premature detachment in the metadata index.

### 2.3 Hardware Disconnection During Automation Execution
- **Failure Trigger:** Device communication lost mid-workflow.
- **Handling:** The failing step catches the connection error and sets its status to `FAILED`. Because the device is unreachable, subsequent non-optional steps are skipped or aborted. The engine marks the workflow report as `FAILED`, populates `error_details`, and releases the execution lock on the device serial so subsequent operations are not deadlocked.

### 2.4 ADB Daemon Crash or External Interruption
- **Failure Trigger:** `adb kill-server` executed externally, or daemon process failure.
- **Handling:** ADB commands fail with non-zero exit codes. Subsystem services wrap invocations with try-except blocks and return typed error models. On the subsequent discovery cycle, `adb start-server` is invoked automatically by the Android provider layer.

### 2.5 Corrupted State and Persistence Recovery
- **Failure Trigger:** Partial writes or malformed JSON in `catalog.json` or workflow definition storage.
- **Handling:** `_load_catalog()` validates JSON syntax and individual record schemas using Pydantic models. Malformed entries are logged as warnings and skipped, ensuring the server boots successfully with all valid artifacts rather than crashing.

---

## 3. Concurrency Safety & Deadlock Prevention

| Component | Concurrency Primitive | Protected Resource | Deadlock Prevention Guarantee |
| :--- | :--- | :--- | :--- |
| `SessionManager` | `threading.RLock` | Lease table & tokens | Short critical sections; no nested I/O calls inside lock |
| `DeviceRegistry` | `threading.Lock` | Device inventory & states | Granular state transition validation |
| `DeviceStreamSession` | `asyncio.Lock` | Stream state transitions | Protects against concurrent `start()` / `stop()` calls |
| `AutomationEngine` | `_device_locks` Dict | Target device exclusivity | Exactly one workflow per device; released in `finally` block |
| `ArtifactManager` | Filesystem Atomic Write | Catalog index & files | In-memory index synchronized with disk |

---

## 4. Stability Verification Matrix

- **Zero Deadlocks Observed:** Verified across multi-client lease contention and rapid disconnect simulation tests.
- **Clean Subprocess Reaping:** All child processes spawned for ADB, logcat, or recordings are explicitly tracked by PID and reaped upon completion or cancellation.
- **Error Containment:** No unhandled runtime exceptions escape API endpoints; all operational failures map cleanly to HTTP 4xx/5xx responses with actionable recovery hints.
