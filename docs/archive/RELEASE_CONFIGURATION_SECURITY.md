# KELVRA Device Lab — Release Configuration & Security Review

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/RELEASE_CONFIGURATION_SECURITY.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Security Architecture & Threat Model

KELVRA Device Lab operates as an autonomous hardware controller and teleoperation service. It implements strict defense-in-depth principles across process execution, network bindings, storage paths, and telemetry streams.

---

## 2. Configuration Safety Audit

### 2.1 Default Network Bindings
- **Default Host:** `127.0.0.1` (Local loopback only).
- **Default Port:** `8098` (Dedicated Device Lab port; zero collision with Bench `:8099`).
- **External Exposure:** The service must never bind to `0.0.0.0` in untrusted networks without reverse proxy authentication (e.g., mTLS, Nginx, or KELVRA Bench Gatekeeper).

### 2.2 Environment Variables & Secrets
The configuration template (`.env.example`) defines all supported runtime variables:
- `KELVRA_DEVICE_LAB_PORT=8098`
- `KELVRA_DEVICE_LAB_HOST=127.0.0.1`
- `LOG_LEVEL=INFO`
- `ADB_PATH=adb`
- `ADB_POLL_INTERVAL_SECONDS=3.0`
- `SCREEN_STREAM_FPS=15`
- `SCREEN_STREAM_QUALITY=70`
- `SCREEN_STREAM_MAX_WIDTH=1080`
- `KELVRA_BENCH_URL=http://127.0.0.1:8099`
- `KELVRA_BENCH_SYNC_ENABLED=true`

**Audit Findings:**
- Zero hardcoded passwords, tokens, API keys, or private certificates exist in the codebase.
- No personal user identifiers or cloud credentials are required for standalone execution.

---

## 3. Subprocess Execution & Sandboxing

### 3.1 Prohibition of Shell Execution
All external process calls (`adb.exe`, `emulator.exe`, `scrcpy.exe`, `ffmpeg.exe`, `avdmanager.bat`) are invoked strictly through `asyncio.create_subprocess_exec` or `subprocess.Popen` with:
- `shell=False`
- Argument lists passing explicit strings (never concatenated command lines)
- Strict binary allowlisting against recognized platform tool binaries
- Dynamic `.exe` resolution on Windows hosts

### 3.2 Output Buffering & Resource Limits
- Subprocess standard output and error streams are strictly bounded to 64 KB per invocation to prevent buffer exhaustion attacks or memory denial of service.
- Hard timeouts (3s to 30s depending on operation type) ensure zombie processes are killed if unresponsive.

---

## 4. Teleoperation Lease & Access Control

### 4.1 Single-Writer Lease Exclusivity
- Unlimited concurrent viewers can connect to the WebSocket screen stream (`/ws/stream/{device_id}`).
- Exactly **one** exclusive single-writer lease can be held per device at any time for control operations (touch tap, swipe, key injection, typing, automation runs).
- Concurrent lease requests return HTTP 409 Conflict with details on the active lease holder.
- Automatic TTL expiration (default 300 seconds) prevents perpetual device locking if a client abruptly disconnects.

---

## 5. Storage Security & Path Traversal Defense

### 5.1 Partitioned Storage Jails
- Artifacts are stored exclusively inside the `artifacts/` tree under designated subdirectories (`screenshots/`, `recordings/`, `logs/`, `reports/`).
- Filenames and IDs are strictly sanitized. Any request containing directory traversal sequences (`../`, `..\`, absolute paths outside the tree) is rejected with HTTP 400 Bad Request.

### 5.2 Storage Quota Management
- Workstation disk usage is bounded to a default quota of 500 MB.
- When disk usage approaches capacity, an automated Least Recently Used (LRU) pruning routine deletes the oldest screenshots and recordings while preserving essential diagnostic reports.

---

## 6. Telemetry & Log Sanitization

### 6.1 Inline Credential Scrubbing
Device logcat output is streamed into a circular in-memory buffer (2,000 entries). Before ingestion, lines are processed by regular expression sanitizers targeting:
- `Bearer\s+[A-Za-z0-9\-._~+/]+=*` -> `[REDACTED_BEARER_TOKEN]`
- `(?i)(password|passwd|pwd)\s*[:=]\s*\S+` -> `[REDACTED_PASSWORD]`
- `(?i)(api[_-]?key|secret[_-]?key|token)\s*[:=]\s*\S+` -> `[REDACTED_SECRET]`

### 6.2 Privacy Policy
KELVRA Device Lab extracts hardware and operational telemetry only (CPU, RAM, battery, thermal status, screen dimensions). It never accesses or extracts SMS, contacts, personal files, browser histories, or user accounts from connected devices.
