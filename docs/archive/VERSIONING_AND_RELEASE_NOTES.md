# KELVRA Device Lab — Versioning & Release Notes (v1.0.0)

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/VERSIONING_AND_RELEASE_NOTES.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Release Status:** Ready for Release
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Versioning Policy

KELVRA Device Lab adheres to **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`):
- **MAJOR:** Incompatible API changes, breaking architectural contracts, or breaking REST/WebSocket schema modifications.
- **MINOR:** Backward-compatible new functionality (e.g., additional platform providers, new automation step types).
- **PATCH:** Backward-compatible bug fixes, performance optimizations, and security remediations.

---

## 2. Release v1.0.0 Highlights

### 2.1 Autonomous Mobile Fleet Teleoperation
- **Unified Device Registry:** Real-time discovery and tracking of physical Android devices, virtual emulators, and Apple devices via a deterministic 10-state lifecycle FSM.
- **Low-Latency Streaming:** WebSocket screen streamer delivering up to 30 FPS dynamic JPEG frames with backpressure dropping and sliding-window FPS computation.
- **Remote Teleoperation:** Precision pointer taps, drag/swipe gestures, alphanumeric physical keyboard input, and hardware button controls (`BACK`, `HOME`, `APP_SWITCH`, `POWER`, `VOLUME`).
- **Single-Writer Exclusivity:** `SessionManager` preventing concurrent multi-operator collision while allowing unlimited read-only viewers.

### 2.2 Android Virtual Device (AVD) Hub
- **Toolchain Auto-Discovery:** Automated resolution of host Android SDK tools (`sdk_root`, `emulator.exe`, `avdmanager.bat`).
- **Headerless INI Parser:** Custom parser accurately extracting emulator configurations without standard parser crashes.
- **Headless Process Supervision:** Safe emulator launching with dynamic port allocation (stepping from 5554) and boot completion monitoring (`sys.boot_completed=1`).
- **One-Click Studio Streaming:** Booted emulators register directly as `AVAILABLE` for instant interaction.

### 2.3 Apple iOS / iPadOS Hardware Inspection
- **Native Host usbmuxd Connectivity:** Windows AMDS daemon communication on loopback TCP port 27015.
- **Generation Mapping:** Normalizes 30+ internal product identifiers (e.g., `iPhone16,1` -> iPhone 15 Pro) into human-readable commercial models.
- **GPLv3 Clean Boundary:** External CLI tools run out-of-process without in-process Python licensing contamination.
- **Platform Honesty:** Live hardware inspection mode reporting authentic UDID, build version, and battery levels while honestly rejecting screen streaming on Windows host.

### 2.4 Declarative Automation & Observability
- **Multi-Step Automation Engine:** Declarative JSON workflows supporting typed actions (`WAIT`, `DELAY`, `TAP`, `SWIPE`, `KEY`, `TYPE_TEXT`, `SCREENSHOT`, `LAUNCH_APP`, `STOP_APP`, `ASSERT_STATE`).
- **Single-Runner Locking:** Per-device concurrency lock rejecting overlapping workflow runs with HTTP 400.
- **Partitioned Artifact Storage:** Directory partitioning (`screenshots/`, `recordings/`, `logs/`, `reports/`) with catalog index, path traversal defense, and a 500 MB quota with automatic LRU pruning.
- **Sanitized Logcat:** Circular memory-bounded stream (2,000 entries) with inline regex scrubbing of Bearer tokens, passwords, and API keys.

### 2.5 KELVRA Bench Integration Support
- **Approach 4 Hybrid Adapter:** Out-of-process HTTP/WS bridge (`kelvra-bench/src/integrations/device_lab_bridge.py`).
- **Swarm MCP Tools:** 8 mobile automation tools registered into the Bench agent runtime.
- **Zero-Downtime Rollback:** Feature flag `KELVRA_DEVICE_LAB_ENABLED=true/false` providing instantaneous degradation.

---

## 3. Upstream & Ecosystem History

- **v0.1.0-standalone (Phase 15):** Standalone laboratory foundation, core streaming, AVD hub, Apple usbmuxd integration, and 155 unit/integration tests.
- **v0.2.0-integrated (Phases 16–17):** Bench integration adapter, Swarm MCP tools, FastAPI router mount, and 24 integration tests.
- **v1.0.0-release (Phases 18–19):** Full integration stabilization, PEP 517/621 packaging, self-contained wheel artifact generation, and release documentation.
