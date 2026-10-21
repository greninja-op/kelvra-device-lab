# KELVRA Device Lab — Resource Lifecycle Management Audit

## 1. Executive Summary

This resource lifecycle audit evaluates how KELVRA Device Lab creates, tracks, bounds, and reaps all operating system and runtime resources. Strict lifecycle controls prevent process leaks, socket exhaustion, file handle starvation, and runaway memory usage during sustained operation.

---

## 2. Resource Inventory & Lifecycle Matrix

### 2.1 Child Processes
- **Types:**
  - `adb exec-out screencap -p` (Screen captures)
  - `adb shell screenrecord` (Video capture sessions)
  - `adb logcat -v time` (Real-time log ingestion)
  - `emulator -avd <name>` (AVD virtual machine execution)
- **Tracking:** Each background process is encapsulated within an owning manager (`RecordingManager`, `AvdManager`, `LogcatService`). PIDs are stored in active process tables.
- **Reaping Protocol:**
  1. On orderly termination, SIGTERM/SIGINT is sent to allow internal flushes (e.g. MP4 trailer writes in `screenrecord`).
  2. The process is awaited with a 3.0s timeout.
  3. If still running after timeout, `terminate()` / `kill()` is issued to ensure immediate process death.
  4. Process handles are closed to prevent zombie processes.

### 2.2 Asyncio Tasks & Event Loop Coroutines
- **Types:**
  - `DeviceStreamSession._capture_loop()`
  - `AutomationEngine._run_workflow_task()`
  - `LogcatService` ingestion loops
- **Lifecycle Control:**
  - Tasks are assigned to internal dictionaries (`_capture_task`, `_active_tasks`, `_logcat_tasks`).
  - Cancellation is handled explicitly using `task.cancel()`.
  - Loops catch `asyncio.CancelledError`, clean up local state, and exit cleanly without raising unhandled errors to the top-level loop.

### 2.3 WebSockets & Network Sockets
- **Types:**
  - Screen streaming client connections (`/ws/devices/{serial}/stream`)
  - Logcat stream subscribers (`/ws/devices/{serial}/logcat`)
- **Lifecycle Control:**
  - Connections are held in thread-safe sets (`Set[WebSocket]`).
  - Broadcast loops wrap `send_json()` in try-except blocks.
  - Any connection failing due to client disconnect or socket reset is appended to a `dead_viewers` discard set and removed immediately.
  - When the final viewer disconnects from a stream session, the stream session automatically switches to the 150ms idle throttle loop.

### 2.4 Filesystem Handles & Disk Storage
- **Catalog Management:** `catalog.json` file writes use contextual context managers (`with open(...)`) ensuring file handles are closed immediately upon write completion.
- **Image Processing Buffers:** In-memory BytesIO buffers created during Pillow image resizing and JPEG compression are explicitly closed or garbage-collected upon function return.
- **Artifact Storage Quota:** Capped at 500 MB. Storage usage is tracked continuously, and an LRU eviction mechanism removes the oldest stored files before new writes occur.

### 2.5 Server Lifespan & Clean Shutdown
- **Lifespan Hook (`@asynccontextmanager` in `server.py`):**
  - **On Startup:** Discovery scans initialize providers, enroll existing ADB devices, and verify directory trees.
  - **On Shutdown:**
    1. Active streaming sessions are cancelled and stopped.
    2. Active recordings are cleanly closed.
    3. Active leases are released.
    4. Logcat streams and subprocesses are terminated.

---

## 3. Resource Audit Results

| Resource Category | Leak Potential | Mitigation Mechanism | Verification Status |
| :--- | :--- | :--- | :--- |
| Subprocess handles | High | Explicit PID tracking + kill fallback | Verified (0 orphan processes) |
| Asyncio tasks | Medium | Explicit cancellation + CancelledError catch | Verified (0 orphaned tasks) |
| WebSocket connections | High | Dead viewer set collection on send failure | Verified (clean removal on disconnect) |
| Logcat memory buffer | High | `deque(maxlen=2000)` bounding | Verified (strictly O(1) bound) |
| Disk space | High | 500 MB quota + LRU pruning | Verified (quota strictly enforced) |
| Single-writer leases | Low | Time-based automatic expiration | Verified (deadlock impossible) |
