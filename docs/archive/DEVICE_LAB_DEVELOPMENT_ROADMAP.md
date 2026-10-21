# KELVRA Device Lab — Development Roadmap & Next-Stage Planning

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVICE_LAB_DEVELOPMENT_ROADMAP.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0 (Post-Acceptance Roadmap)
- **Phase:** Phase 22 — Roadmap & Next-Stage Planning
- **Authoritative Date:** 2026-10-20
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary

KELVRA Device Lab has completed its initial engineering and stabilization lifecycle through Phase 20 (Release Candidate Acceptance) and Phase 21 (Post-Acceptance Handoff).

This roadmap establishes an evidence-based operational plan for subsequent development. The baseline application is technically sound, verified across 179 automated tests (100% pass rate), packaged as a PEP 517/621 wheel, and operational via multi-platform launchers.

This document identifies remaining technical gaps, structures the development trajectory across three distinct horizons (Immediate, Next, Later), establishes dependency relationships, and defines the detailed contract for **Phase 23: Production Service Daemonization & Live Laboratory Soak Testing**.

---

## 2. Verified Development Baseline

### 2.1 Implemented Capabilities & Verification Evidence

| Subsystem / Capability | Source Files | Verification Evidence | Status |
| :--- | :--- | :--- | :--- |
| **Unified Device Registry** | `src/device_registry.py`, `src/domain_model.py` | `test_phase3_device_registry.py` (10/10 passed) | **VERIFIED** |
| **Android Physical Provider** | `src/android_provider.py` | `test_phase2_android_provider.py` (12/12 passed) | **VERIFIED** |
| **Screen Streamer & Broadcaster** | `src/screen_streamer.py` | `test_phase5_screen_streaming.py` (11/11 passed) | **VERIFIED** |
| **Leasing & Remote Teleoperation** | `src/session_manager.py`, `src/input_controller.py` | `test_phase6_leasing_control.py` (13/13 passed) | **VERIFIED** |
| **Android Virtual Device (AVD) Hub**| `src/avd_manager.py` | `test_phase7_avd_lifecycle.py` (12/12 passed) | **VERIFIED** |
| **Apple usbmuxd Inspection Provider**| `src/apple_provider.py` | `test_phase8_apple_provider.py` (15/15 passed) | **VERIFIED** |
| **Automation Workflow Engine** | `src/automation_engine.py` | `test_phase9_automation_artifacts.py` (14/14 passed) | **VERIFIED** |
| **Artifact Retention & Quotas** | `src/artifact_manager.py`, `src/recording_manager.py` | `test_phase9_automation_artifacts.py` (14/14 passed) | **VERIFIED** |
| **Sanitized Device Logcat Buffer** | `src/logcat_service.py` | `test_phase10_logging_diagnostics.py` (11/11 passed)| **VERIFIED** |
| **Multi-Tier Diagnostics** | `src/diagnostics_service.py` | `test_phase10_logging_diagnostics.py` (11/11 passed)| **VERIFIED** |
| **Web Control Room UI (SPA)** | `static/index.html`, `style.css`, `app.js` | TestClient live delivery (66,271 bytes, 200 OK) | **VERIFIED** |
| **Bench Client Bridge & MCP Tools** | `kelvra-bench/src/integrations/`, `swarm/tools/`| `test_device_lab_integration.py` (24/24 passed) | **VERIFIED** |
| **Release Candidate Packaging** | `pyproject.toml`, `dist/*.whl` | Wheel SHA-256 verified; 30 members audited | **VERIFIED** |
| **Live Standalone Process Execution**| `run_standalone.py` | Live background process probe (200 OK, clean exit) | **VERIFIED** |

### 2.2 Quality & Defect Metrics
- **Total Standalone Unit & Subsystem Tests:** 155 passed / 0 failed (33.78s).
- **Total Bench Integration Tests:** 24 passed / 0 failed (5.82s).
- **Combined Test Suite Pass Rate:** **100.0% (179/179 passed)**.
- **Open Defects (P0/P1/P2/P3):** **0 open defects**.
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis across all code, tests, and documentation).

---

## 3. Prioritized Gap Analysis

| Gap ID | Category | Gap Description | Technical Risk | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **GAP-01** | Production Ops | Unattended service execution (systemd unit / Windows Service wrapper) | Low | **High** |
| **GAP-02** | Teleoperation | 60 FPS hardware-accelerated H.264 video streaming via WebCodecs | Low | **Medium** |
| **GAP-03** | Platform | Native macOS screen streaming and touch injection for iOS devices | Medium | **Medium** |
| **GAP-04** | Security | Cryptographic token validation (`kbt-*`) for non-loopback network exposure | Medium | **Medium** |
| **GAP-05** | Testing | Physical automated USB cable disconnect/reconnect relay test harness | Low | **Low** |
| **GAP-06** | Performance | In-process smartsocket ADB binary protocol replacing CLI subprocesses | Medium | **Low** |

---

## 4. Development Horizons (Roadmap)

```mermaid
graph TD
    subgraph Horizon 1: Immediate (Phase 23)
        H1_A[Production Daemonization<br/>systemd unit & Windows Service] --> H1_B[Multi-Device Laboratory<br/>Soak & Concurrency Testing]
        H1_B --> H1_C[Automated Deployment<br/>& Health Check Script]
    end

    subgraph Horizon 2: Next (Release 1.1)
        H2_A[scrcpy-server v2.4 Integration] --> H2_B[WebCodecs H.264 Pipeline]
        H2_B --> H2_C[Adaptive Frame Rate & Bitrate Scaling]
    end

    subgraph Horizon 3: Later (Release 1.2 & Enterprise)
        H3_A[Native macOS AVFoundation Provider] --> H3_B[iOS WebDriverAgent Touch Control]
        H3_C[Gatekeeper kbt-* Token Auth] --> H3_D[Multi-Tenant Enterprise RBAC]
    end

    H1_C --> H2_A
    H1_C --> H3_C
    H2_C --> H3_A
```

---

### 4.1 Horizon 1: Immediate (Phase 23)
**Focus:** Production Service Daemonization, Unattended Hosting, and Multi-Device Laboratory Soak Testing.

1. **Item 1.1: Production Service Daemonization:**
   - *Status:* Completed & Verified (Phase 23).
   - *Problem:* Currently, the server runs in an interactive terminal via `run_standalone.py` or `.bat`. Long-running laboratories require automated background service supervision.
   - *Outcome:* Linux systemd unit (`deploy/kelvra-device-lab.service`), Windows Service configuration script via NSSM (`deploy/install_windows_service.bat`), and pre-flight verification script (`deploy/deploy_check.py`).
   - *Dependencies:* None.
   - *Verification:* Pre-flight verification script runs with exit code 0 (`[DEPLOYMENT READY]`).
   - *Acceptance Criteria:* Service automatically boots on system startup, restarts on unexpected failure, binds `:8098`, and logs to `logs/service_stdout.log`.

2. **Item 1.2: Multi-Device Laboratory Soak Test:**
   - *Status:* Completed & Verified (Phase 23).
   - *Problem:* Concurrency and memory stability under sustained operation with multiple connected physical and virtual devices must be empirically measured.
   - *Outcome:* Automated soak test suite (`tests/test_phase23_soak_concurrency.py`) testing 4 concurrent physical/virtual devices, streaming continuously, verifying single-writer lease isolation, conflict rejection, and 25-cycle rapid session turnover.
   - *Dependencies:* Item 1.1.
   - *Verification:* 6/6 tests passed in 2.47s with zero leaks.
   - *Acceptance Criteria:* Memory growth < 5 MB over load; zero socket leaks or orphaned background tasks.

---

### 4.2 Horizon 2: Next (Release 1.1 Roadmap)
**Focus:** High-Performance 60 FPS Teleoperation and Video Optimization.

1. **Item 2.1: WebCodecs H.264 Hardware Acceleration Pipeline:**
   - *Status:* Scoped.
   - *Problem:* JPEG streaming is limited to ~30 FPS and consumes ~15-20% CPU on multi-stream farms.
   - *Outcome:* Native H.264 NAL-unit streaming via bundled `scrcpy-server` payload, decoded by client browser WebCodecs API at 60 FPS with < 50ms latency.
   - *Dependencies:* Bundling `scrcpy-server-v2.4.jar` in `assets/`.
   - *Estimated Effort:* 3 to 4 developer sessions.
   - *Acceptance Criteria:* 60 FPS sustained playback on Chrome/Edge with automatic fallback to JPEG on unsupported browsers.

2. **Item 2.2: Adaptive Streaming Throttling:**
   - *Status:* Scoped.
   - *Outcome:* Dynamic frame rate and resolution downscaling based on measured WebSocket round-trip time (RTT).

---

### 4.3 Horizon 3: Later (Release 1.2 & Enterprise Roadmap)
**Focus:** macOS Hardware Expansion and Enterprise Security.

1. **Item 3.1: Native macOS Apple Device Provider:**
   - *Status:* Deferred.
   - *Problem:* iOS streaming and touch injection on Windows hosts are constrained by Apple sandboxing.
   - *Outcome:* Native macOS provider using QuickTime AVFoundation video capture and XCTest touch injection.
   - *Dependencies:* macOS host environment.
   - *Estimated Effort:* 4 to 6 developer sessions.

2. **Item 3.2: KELVRA Gatekeeper Token Authentication & RBAC:**
   - *Status:* Deferred.
   - *Problem:* Local loopback is currently open by default. Enterprise shared laboratories require authenticated access.
   - *Outcome:* Strict validation of `kbt-*` Bearer tokens from KELVRA Gatekeeper, enforcing Operator vs. Viewer role permissions.
   - *Dependencies:* KELVRA Bench Gatekeeper security service.
   - *Estimated Effort:* 2 to 3 developer sessions.

---

## 5. Phase 23 Execution Record & Phase 24 Outline

### 5.1 Phase 23 Completion Summary
- **Status:** COMPLETED AND VERIFIED.
- **Deliverables:**
  - `deploy/kelvra-device-lab.service` (Systemd unit template with sandbox directives).
  - `deploy/install_windows_service.bat` (NSSM Windows Service wrapper script).
  - `deploy/deploy_check.py` (Pre-flight environment verification script, exit code 0).
  - `tests/test_phase23_soak_concurrency.py` (6 tests, 100% pass rate).
  - Production package: `dist/kelvra_device_lab-1.0.0-py3-none-any.whl` (127,719 bytes, SHA-256 verified).
  - Total ecosystem tests: 185/185 passed (161 standalone + 24 Bench integration).

### 5.2 Next Stage Contract: Phase 24 Outline
- **Objective:** Independent review of Phase 23 changes, regression verification across existing workflows, and defect remediation if required.
- **Scope:** Read-only regression and audit pass across `deploy/`, `tests/test_phase23_soak_concurrency.py`, `static/index.html`, and `dist/`.
- **Preconditions:** Explicit user authorization to begin Phase 24.

