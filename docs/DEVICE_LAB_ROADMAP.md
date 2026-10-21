# KELVRA Device Lab — Authoritative Development Roadmap (`docs/DEVICE_LAB_ROADMAP.md`)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVICE_LAB_ROADMAP.md`
- **Subsystem:** KELVRA Device Lab Standalone (`:8098`) & Bench Bridge (`:8099`)
- **Authority:** Canonical Project Record (Document 4 of 4)
- **Status:** Active Roadmap & Open Decisions Ledger
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary & Development Trajectory

With the completion of Phases 1 through 24, KELVRA Device Lab has achieved full standalone operational readiness on port `:8098` and verified bridge integration with KELVRA Bench on port `:8099`. The test suite certifies 185/185 tests passing (161 standalone + 24 Bench integration), 0 open defects, and 5/5 deployment pre-flight checks verified.

The forward trajectory is structured into three distinct horizons:
1. **Horizon 1 (Immediate — Completed in Phases 23–24):** Production service daemonization (systemd unit, NSSM Windows service), pre-flight environment auditing (`deploy/deploy_check.py`), multi-device concurrency and soak testing (`tests/test_phase23_soak_concurrency.py`), and release packaging.
2. **Horizon 2 (Near-Term — Release 1.1):** High-performance WebCodecs H.264 60 FPS video pipeline using bundled `scrcpy-server`, Web Worker `OffscreenCanvas` rendering, and declarative automation runner expansion.
3. **Horizon 3 (Medium-Term — Release 1.2 & Enterprise):** Native macOS Apple provider with QuickTime/WebDriverAgent teleoperation, and enterprise RBAC token authentication via KELVRA Gatekeeper.

```
+-----------------------------------------------------------------------------------------+
|                                    KELVRA DEVICE LAB                                    |
+-----------------------------------------------------------------------------------------+
                                             |
                   +-------------------------+-------------------------+
                   |                                                   |
                   v                                                   v
+------------------------------------+               +------------------------------------+
|             HORIZON 1              |               |             HORIZON 2              |
| Production Daemon & Soak (Ph 23-24)|               | WebCodecs H.264 60 FPS (Ph 25)     |
| [STATUS: VERIFIED & COMPLETED]     |               | [STATUS: NEXT PRIORITY CONTRACT]   |
+------------------------------------+               +------------------------------------+
  - systemd unit & Windows service                     - Bundled scrcpy-server payload
  - deploy/deploy_check.py (5/5 PASS)                  - WebSocket binary H.264 annex-b
  - Multi-device soak & turnover tests                 - OffscreenCanvas Web Worker decoding
  - 185 total passing automated tests                  - Dynamic fallback to JPEG streaming
                   |                                                   |
                   +-------------------------+-------------------------+
                                             |
                                             v
                             +--------------------------------+
                             |           HORIZON 3            |
                             |  macOS Apple & Enterprise Auth |
                             |  [STATUS: FUTURE MILESTONE]    |
                             +--------------------------------+
                               - Native macOS QuickTime stream
                               - WebDriverAgent touch injection
                               - Gatekeeper kbt-* token RBAC
                               - Multi-tenant laboratory leases
```

---

## 2. Three-Horizon Strategic Roadmap

### Horizon 1: Production Service Daemonization & Live Soak (Completed)
- **Status:** `VERIFIED & COMPLETED` (Phases 23–24).
- **Core Deliverables:**
  - `deploy/kelvra-device-lab.service`: Hardened systemd unit with full security sandboxing (`NoNewPrivileges=true`, `ProtectSystem=full`, `ProtectHome=read-only`, `PrivateTmp=true`), automated restart (`Restart=on-failure`, `RestartSec=5s`), and file descriptor limit 65535.
  - `deploy/install_windows_service.bat`: Automated Windows background service setup script using NSSM with log rotation (10 MB / 86400s) and restart on unexpected termination.
  - `deploy/deploy_check.py`: Automated pre-flight environment auditor validating Python version (>= 3.10), dependencies, ADB toolchain resolution, port `:8098` availability, and `artifacts/` write permissions. Returns exit code 0 on full deployment readiness.
  - `tests/test_phase23_soak_concurrency.py`: 6 automated tests validating multi-device registration, concurrent lease isolation, single-writer collision rejection, simultaneous streaming sessions, and rapid session turnover (25 cycles) with complete garbage collection.
  - Production distribution wheel: `dist/kelvra_device_lab-1.0.0-py3-none-any.whl` (127,719 bytes, SHA-256 `e9da26fa2727a990a1314765171c33fdf545ab19c9273c4907b661eb1fb5c5a7`).

### Horizon 2: High-Performance Teleoperation & Automation Expansion (Near-Term / Release 1.1)
- **Status:** `IN PROGRESS — MILESTONE 2.1 COMPLETED (PHASE 25)`.
- **Target Milestones:**
  - **Milestone 2.1: WebCodecs H.264 Streaming Pipeline (Phase 25):** `[COMPLETED]` Implemented low-latency H.264 video feed via `src/scrcpy_streamer.py`, Annex-B NAL unit parser, SPS/PPS parameter extraction and caching, binary WebSocket route `/ws/devices/{serial}/stream/h264`, and background Web Worker `static/decoder_worker.js`.
  - **Milestone 2.2: Web Worker OffscreenCanvas Architecture:** `[COMPLETED IN PHASE 25]` Offloaded video decoding and canvas rendering to background WebCodecs Web Worker, preventing UI thread blocking.
  - **Milestone 2.3: Multi-Device Thumbnail Preview Grid (Phase 27):** `[COMPLETED]` Implemented responsive 2x2 matrix grid (`#studio-matrix-viewport`), REST thumbnail endpoints (`/api/devices/{id}/thumbnail` and `/api/devices/thumbnails/batch`), low-frequency background polling (0.33 FPS), and zero-teardown teleoperation target focus switching.
  - **Milestone 2.4: Declarative Automation Assertion Suite:** Expand `AutomationEngine` with visual template matching and OCR text assertion steps (`ASSERT_TEXT_PRESENT`, `WAIT_FOR_ELEMENT`).

### Horizon 3: Platform Expansion & Ecosystem Hardening (Medium-Term / Release 1.2 & Enterprise)
- **Status:** `PLANNED`.
- **Target Milestones:**
  - **Milestone 3.1: Native macOS Apple Device Teleoperation:** Implement native macOS provider leveraging AVFoundation / QuickTime screen capture and WebDriverAgent for real-time 30/60 FPS video streaming and touch control on physical iPhones and iPads.
  - **Milestone 3.2: KELVRA Gatekeeper Token Authentication & RBAC:** Enforce cryptographic `kbt-*` Bearer token validation and multi-tenant role-based access control (`Admin`, `Operator`, `Viewer`) on all Device Lab endpoints when exposed beyond local loopback.
  - **Milestone 3.3: Fleet Analytics & Health Benchmarking:** Bounded SQLite timeseries logging tracking device battery degradation, thermal throttling, connection stability scores, and automation pass/fail trends over 30-day retention windows.

---

## 3. Prioritized Feature Register & Acceptance Contracts

### Priority 1: Production Deployment Automation & Operator Runbook (Horizon 1)
- **Status:** `COMPLETED` (Phase 23 & Phase 24).
- **Deliverables:** `deploy/kelvra-device-lab.service`, `deploy/install_windows_service.bat`, `deploy/deploy_check.py`, `tests/test_phase23_soak_concurrency.py`.
- **Verified Acceptance Criteria:** Service units bind port `:8098`, auto-restart on failure, log to rotating files, pass 5/5 pre-flight checks, and sustain rapid session turnover under concurrency.

### Priority 2: WebCodecs H.264 60 FPS Hardware Streaming (Horizon 2 / Phase 25 Target)
- **Status:** `READY FOR IMPLEMENTATION`.
- **Objective:** Implement opt-in low-latency H.264 video streaming using bundled `scrcpy-server` payload and browser WebCodecs API.
- **Affected Modules:** `src/screen_streamer.py`, `src/scrcpy_streamer.py`, `static/app.js`, `static/decoder_worker.js`.
- **Dependencies:** Pre-compiled Apache 2.0 `scrcpy-server-v2.4.jar` bundled in `assets/`.
- **Acceptance Criteria:**
  1. Server initiates `scrcpy-server` via ADB forward socket without root requirements.
  2. WebSocket `/ws/devices/{serial}/stream/h264` emits binary Annex-B NAL units (SPS, PPS, IDR, non-IDR).
  3. Client decodes video using `VideoDecoder` WebCodecs API inside an OffscreenCanvas Web Worker.
  4. Teleoperation delivers 60 FPS at 1080p with < 50ms end-to-end latency.
  5. Dynamic fallback to existing JPEG screencap stream occurs automatically on non-supported browsers.
- **Tests Required:** Unit tests for H.264 NAL parsing, mock streaming socket tests, browser benchmark tests.

### Priority 3: Native macOS Apple Device Streaming & Remote Control (Horizon 3)
- **Status:** `PLANNED`.
- **Objective:** Implement native macOS provider hooks using QuickTime screen capture and WebDriverAgent for full streaming and touch injection on iOS devices connected to macOS hosts.
- **Affected Modules:** `src/apple_provider.py`.
- **Dependencies:** macOS host, Xcode Command Line Tools.
- **Acceptance Criteria:** Full 30/60 FPS streaming and touch injection on connected iPhone/iPad devices on macOS.

### Priority 4: KELVRA Gatekeeper Token Authentication & RBAC (Horizon 3)
- **Status:** `PLANNED`.
- **Objective:** Support cryptographic `kbt-*` Bearer token validation and multi-tenant role-based access control (Admin, Operator, Viewer) on Device Lab endpoints.
- **Affected Modules:** `src/server.py`, `src/session_manager.py`.
- **Dependencies:** KELVRA Bench Gatekeeper security service.
- **Acceptance Criteria:** Requests without valid authorization tokens are rejected with HTTP 401 Unauthorized; viewers cannot acquire operator leases.

---

## 4. Open Architectural Decisions Ledger

| ID | Decision Topic | Context & Tradeoffs | Current Consensus & Recommended Resolution | Target Phase |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-01** | **Token Auth Mode (Standalone vs Bench)** | Standalone developer ergonomics favor unauthenticated loopback, whereas enterprise deployment requires strict `kbt-*` Bearer tokens. | Default to open localhost loopback (`127.0.0.1`); enforce strict `kbt-` header validation when `KELVRA_AUTH_REQUIRED=1` or when binding non-loopback interfaces. | Horizon 3 (Priority 4) |
| **DEC-02** | **scrcpy-server Payload Distribution** | Downloading `scrcpy-server.jar` at runtime creates network dependency and potential supply-chain vulnerability; bundling increases wheel size by ~70 KB. | Bundle verified `scrcpy-server-v2.4.jar` (Apache 2.0) inside `assets/` with verified cryptographic SHA-256 hash. Zero network dependency during installation. | Horizon 2 (Phase 25) |
| **DEC-03** | **WebCodecs Offscreen Canvas Worker** | Decoding H.264 on the main UI thread can stutter during high-frequency DOM manipulation; Web Workers add message passing overhead. | Standardize on Web Worker decoding with `OffscreenCanvas` transfer for Release 1.1, with transparent fallback to main-thread canvas if Web Worker transfer is unsupported. | Horizon 2 (Phase 25) |
| **DEC-04** | **Multi-Device Studio Concurrency Cap** | Decoding multiple 60 FPS feeds simultaneously strains client GPU decoders and USB host controllers. | Standardize on exactly 1 active high-framerate stream in the Studio viewport; background inventory devices display low-rate thumbnail previews (1 frame per 3s). | Horizon 2 (Milestone 2.3) |
| **DEC-05** | **Logcat & Syslog Export Format Standard** | Plaintext `.log` is familiar to operators; JSON Lines (`.jsonl`) enables programmatic parsing by swarm agents. | Dual-format export: `/api/devices/{serial}/logs/export?format=txt` delivers standard logcat format, `?format=json` delivers structured JSON array with parsed timestamps and tags. | Implemented & Frozen |

---

## 5. Platform Constraints & Known Blockers Matrix

| Platform / Tool | Operational Limitation | Root Cause | Impact | Mitigation / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Apple iOS on Windows** | No screen streaming or touch injection | Apple lockdown protocol encrypts video; AirPlay mirroring requires native macOS AVFoundation | Apple devices on Windows are restricted to Inspection Mode (specs, pairing status, lockdown records) | Transparent capability catalog; honest UI explanation; macOS provider planned in Horizon 3 |
| **Apple Mobile Device Service** | iOS USB discovery requires AMDS on Windows | AMDS provides the usbmuxd loopback daemon on port 27015 | Device Lab cannot detect USB iOS devices if iTunes or Apple Devices app is not installed | Pre-flight diagnostics report port 27015 status; non-fatal fallback to Android-only mode |
| **Physical Android Devices** | RSA authorization prompt required | Android OS security model requires physical screen confirmation | Device appears in `UNAUTHORIZED` state with HTTP 403 on property endpoints until accepted | Injected recovery hints instruct operator to unlock screen and tap "Always allow" |
| **Android Virtual Devices (AVD)** | Virtualization overhead and SDK dependency | Android Emulator requires Intel HAXM or Windows Hypervisor Platform (WHPX) and system images | Launch fails with HTTP 400 if system image is absent or hypervisor is disabled | `SdkEnvironmentDetector` verifies system images prior to launch; clear remediation banners |
| **WebCodecs API** | Client browser compatibility | Safari on older iOS/macOS versions or legacy Chromium browsers may lack WebCodecs support | H.264 video decoding fails in browser | Dynamic client detection in `app.js` falling back to JPEG stream over WebSocket |

---

## 6. Project Milestone Completion & Developer Handoff
 
### Milestone Status: Horizon 1 & Horizon 2 Complete — Certified Ready for Handoff
- **Verification Summary:** All planned Horizon 1 and Horizon 2 capabilities (Milestones 1.1 through 2.3) are implemented, verified, and certified ready for developer handoff with 201 passing tests (100% pass rate).
- **Authoritative Handover Documents:**
  - `docs/DEVICE_LAB_FINAL_PROJECT_REVIEW.md` — Formal project review, architecture evaluation, and capability matrix.
  - `docs/DEVICE_LAB_HANDOFF_GUIDE.md` — Complete developer runbook, quickstart, testing, and operational workflows.
- **Future Horizon 3 Priorities (Post-Handoff):**
  - Priority 3: Native macOS Apple Device Streaming & Remote Control (QuickTime AVFoundation + WebDriverAgent).
  - Priority 4: KELVRA Gatekeeper Token Authentication & RBAC (`kbt-*` Bearer token validation for non-loopback deployments).
  - Priority 5: Real-time audio streaming pipeline over WebRTC.
