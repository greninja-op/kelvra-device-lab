# KELVRA Device Lab — Development Priority Register

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVELOPMENT_PRIORITY_REGISTER.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Phase:** Phase 21 — Post-Acceptance Handoff & Maintenance Readiness
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Prioritization Framework

Priorities are established according to:
1. Production deployment readiness and operator automation.
2. High-performance video streaming enhancements.
3. Expanded hardware support and macOS integration.
4. Security and multi-tenant authentication integration.

---

## 2. Top Development Priorities

### Priority 1: Production Deployment Automation & Operator Runbook
- **Objective:** Provide automated systemd service definitions (Linux) and NSSM / Windows Service wrappers for unattended background execution, accompanied by an interactive physical test runbook.
- **Reason for Priority:** The release candidate v1.0.0 has passed acceptance; the immediate next operational step is enabling continuous background hosting.
- **Affected Project / Modules:** `Kelvra/KELVRA Device Lab/` (`deploy/`, `scripts/`, `docs/`).
- **Dependencies:** None.
- **Acceptance Criteria:** Service unit starts on system boot, binds port `:8098`, redirects logs to `logs/server.log`, and cleanly restarts on failure.
- **Tests Required:** Service install, start, stop, restart, and health probing.
- **Risks:** Service permissions on Windows/Linux host.
- **Approval Required:** **YES** (Requires user authorization before deployment).

---

### Priority 2: WebCodecs H.264 60 FPS Hardware Streaming (Release 1.1)
- **Objective:** Implement opt-in low-latency H.264 video streaming using bundled `scrcpy-server` payload and browser WebCodecs API.
- **Reason for Priority:** Enhances teleoperation frame rate from 30 FPS to 60 FPS while lowering CPU utilization on multi-device farms.
- **Affected Project / Modules:** `src/screen_streamer.py`, `static/app.js`.
- **Dependencies:** `scrcpy-server-v2.4.jar` in `assets/`.
- **Acceptance Criteria:** Chrome/Edge/Firefox WebCodecs decoding sustains 60 FPS with < 50ms end-to-end latency; falls back to JPEG streaming on incompatible clients.
- **Tests Required:** WebSocket binary H.264 packet stream tests, browser frame rate benchmark.
- **Risks:** Client browser WebCodecs hardware decoding support variation.
- **Approval Required:** **YES**.

---

### Priority 3: Native macOS Apple Device Streaming & Remote Control (Release 1.2)
- **Objective:** Implement native macOS provider hooks using QuickTime screen capture and WebDriverAgent for full streaming and touch injection on iOS devices connected to macOS hosts.
- **Reason for Priority:** Removes the Windows-host limitation for Apple hardware when running on Apple Silicon / macOS developer workstations.
- **Affected Project / Modules:** `src/apple_provider.py`.
- **Dependencies:** macOS host, Xcode Command Line Tools.
- **Acceptance Criteria:** Full 30/60 FPS streaming and touch injection on connected iPhone/iPad devices on macOS.
- **Tests Required:** macOS CI / physical host integration suite.
- **Risks:** Host OS dependency (macOS only).
- **Approval Required:** **YES**.

---

### Priority 4: KELVRA Gatekeeper Token Authentication & RBAC (Enterprise Tier)
- **Objective:** Support cryptographic `kbt-*` Bearer token validation and multi-tenant role-based access control (Admin, Operator, Viewer) on Device Lab endpoints.
- **Reason for Priority:** Protects remote laboratories when exposed beyond local loopback on shared enterprise networks.
- **Affected Project / Modules:** `src/server.py`, `src/session_manager.py`.
- **Dependencies:** KELVRA Bench Gatekeeper security service.
- **Acceptance Criteria:** Requests without valid authorization tokens are rejected with HTTP 401 Unauthorized; viewers cannot acquire operator leases.
- **Tests Required:** Auth unit tests, role permission matrix tests.
- **Risks:** Developer workstation ergonomic overhead if forced on localhost.
- **Approval Required:** **YES**.
