# KELVRA Device Lab — Operational Maintenance Guide

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/MAINTENANCE_GUIDE.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Phase:** Phase 21 — Post-Acceptance Handoff & Maintenance Readiness
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. System Maintenance Overview

KELVRA Device Lab is an autonomous mobile device teleoperation, screen streaming, telemetry, and automated test orchestration service. This guide defines standard operational procedures, startup and shutdown lifecycles, environment configuration, dependency maintenance, and diagnostic runbooks.

---

## 2. Service Startup and Shutdown

### 2.1 Supported Launch Mechanisms

| Method | Command | Target Use Case |
| :--- | :--- | :--- |
| **Direct Script** | `python run_standalone.py` | Developer workstation execution, debugging |
| **Windows Launcher** | `run_standalone.bat` | One-click Windows desktop startup |
| **POSIX Launcher** | `./run_standalone.sh` | Linux / macOS headless server execution |
| **Installed CLI** | `kelvra-device-lab` | System service, virtual environment CLI |
| **Uvicorn Explicit** | `python -m uvicorn src.server:app --port 8098 --host 127.0.0.1` | Custom port, hot-reload development (`--reload`) |

### 2.2 Startup Lifecycle & Health Verification
When started, the application initializes services in the following order:
1. `AndroidDeviceProvider` searches host PATH for `adb.exe` and queries version.
2. `AppleDeviceProvider` initializes native Windows AMDS daemon connectivity on TCP port 27015.
3. `DeviceRegistry` registers all providers (`android_adb`, `test_mock_provider`, `apple_device_provider`).
4. `SessionManager` initializes the single-writer lease scheduler.
5. `ArtifactManager` verifies the `artifacts/` partition and indexes `artifacts/catalog.json`.
6. FastAPI binds to `127.0.0.1:8098`.

To verify operational health:
```bash
curl -s http://127.0.0.1:8098/api/health
```
Expected response:
```json
{"status": "healthy", "service": "kelvra-device-lab", "port": 8098, "active_devices": 0}
```

### 2.3 Graceful Shutdown Lifecycle
On receiving `SIGINT` (Ctrl+C) or `SIGTERM`:
1. The server stops accepting new WebSocket connections.
2. Active screen streamers are terminated, releasing video buffers.
3. In-flight automation steps complete or cancel cleanly.
4. Active leases are released.
5. The process exits with code 0 without leaving dangling child processes.

---

## 3. Configuration & Environment Variables

Configuration is loaded from environment variables, optionally customized via a local `.env` file copied from `.env.example`:

| Variable Name | Default | Description |
| :--- | :--- | :--- |
| `KELVRA_DEVICE_LAB_PORT` | `8098` | Dedicated HTTP/WS port for Device Lab |
| `KELVRA_DEVICE_LAB_HOST` | `127.0.0.1` | Host loopback interface (do not bind 0.0.0.0 directly) |
| `LOG_LEVEL` | `INFO` | Application log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ADB_PATH` | `adb` | Path to Android Debug Bridge binary |
| `ADB_POLL_INTERVAL_SECONDS` | `3.0` | Interval between background device inventory scans |
| `SCREEN_STREAM_FPS` | `15` | Default target frame rate for MJPEG streaming |
| `SCREEN_STREAM_QUALITY` | `70` | JPEG compression quality (1-100) |
| `SCREEN_STREAM_MAX_WIDTH` | `1080` | Maximum scaled frame dimension |
| `KELVRA_BENCH_URL` | `http://127.0.0.1:8099` | Upstream Bench service URL for event forwarding |
| `KELVRA_BENCH_SYNC_ENABLED` | `true` | Enables bi-directional telemetry synchronization |

---

## 4. Dependencies & Packaging Maintenance

### 4.1 Dependency Manifests
- **Runtime:** [`requirements.txt`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/requirements.txt) & [`pyproject.toml`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/pyproject.toml)
- **Install command:** `pip install -r requirements.txt`

### 4.2 Building Release Distributions
To rebuild the release wheel package:
```bash
python -m pip wheel . -w dist --no-deps --no-build-isolation
```
Output artifact: `dist/kelvra_device_lab-1.0.0-py3-none-any.whl`.

---

## 5. Artifact Storage & Quota Management

All generated screenshots, recordings, exported logs, and workflow reports reside inside `artifacts/`:
- `artifacts/screenshots/`: Captured JPEG/PNG frames.
- `artifacts/recordings/`: Captured MP4 video sessions.
- `artifacts/logs/`: Exported logcat captures.
- `artifacts/reports/`: JSON workflow execution reports.
- `artifacts/catalog.json`: Primary index of all artifacts.

**Maintenance Policy:**
- `ArtifactManager` enforces a 500 MB quota with automatic Least Recently Used (LRU) pruning.
- Manual cleanup: Delete older files in `artifacts/screenshots/` and `artifacts/recordings/` as needed; reset `artifacts/catalog.json` to `{}` if full catalog clearing is desired.

---

## 6. Diagnostic Runbook & Common Failures

| Symptom | Probable Cause | Remediation Procedure |
| :--- | :--- | :--- |
| **No Android devices discovered** | ADB daemon is not running or device is unauthorized | Run `adb devices` in terminal. Verify USB debugging is enabled and accept RSA prompt on device screen. |
| **Device stuck in UNAUTHORIZED** | Host RSA key unaccepted or passcode locked | Unlock mobile screen; tap "Always allow from this computer". |
| **Port 8098 collision error** | Stale Python or Uvicorn instance running | Check running processes with `netstat -ano \| findstr 8098` on Windows, then terminate the stale PID. |
| **iOS device shows UNAUTHORIZED** | Apple trust record missing or passcode locked | Unlock device with PIN; tap "Trust This Computer"; verify AMDS service is running on Windows. |
| **Screen streaming lag / high latency** | Network congestion or low CPU throttling | Lower `SCREEN_STREAM_QUALITY=50` and `SCREEN_STREAM_MAX_WIDTH=720` in `.env`. |
| **Lease conflict error (HTTP 409)** | Another operator or agent holds control lock | Release lease via `/api/leases/{serial}/release` or wait for the 300s TTL timeout. |
