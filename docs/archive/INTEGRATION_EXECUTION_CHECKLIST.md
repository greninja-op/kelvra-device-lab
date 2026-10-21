# KELVRA Device Lab — Controlled Integration Execution Checklist

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/INTEGRATION_EXECUTION_CHECKLIST.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Execution State:** READY FOR AUTHORIZATION (Execution Halted Pending Approval)
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Protocol Overview

This checklist serves as the authoritative, sequential gate protocol for executing the synchronization of KELVRA Device Lab into KELVRA Bench.

**MANDATORY RULE:** Do not begin Gate 2 until Gate 1 is 100% verified and explicit user authorization is provided in the prompt.

---

## 2. Sequential Gate Checklist

```
+---------------------------------------------------------------------------------+
|                              EXECUTION GATEWAY                                  |
|                                                                                 |
|  [GATE 1] Pre-Sync Audit & Authorization  --->  [GATE 2] Bench Bridge Files     |
|       |                                               |                         |
|       v                                               v                         |
|  [GATE 3] Configuration & Feature Flag    --->  [GATE 4] EventBus & MCP Tools   |
|       |                                               |                         |
|       v                                               v                         |
|  [GATE 5] End-to-End Verification Testing --->  [GATE 6] Release & Commit Audit |
+---------------------------------------------------------------------------------+
```

### Gate 1: Pre-Execution Authorization & Health Audit
- [ ] **1.1 Explicit User Authorization:** User prompt explicitly commands synchronization/merge execution.
- [ ] **1.2 Clean Workspace Boundaries:** Verify `git status` across `Kelvra/KELVRA Device Lab/` and `Kelvra/kelvra-bench/`.
- [ ] **1.3 Standalone Baseline Pass:** Run `python -m pytest -q` in `Kelvra/KELVRA Device Lab/` (Confirm exactly 155 passed).
- [ ] **1.4 Zero-Emoji Audit:** Execute regex sweep `[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]` across all files.

### Gate 2: Bench Bridge Module Authoring
- [ ] **2.1 Package Initialization:** Create `Kelvra/kelvra-bench/src/integrations/__init__.py`.
- [ ] **2.2 REST & WS Bridge Client:** Author `Kelvra/kelvra-bench/src/integrations/device_lab_bridge.py` implementing asynchronous HTTPX methods:
  - `list_devices()`
  - `acquire_lease(serial, duration)`
  - `release_lease(serial, lease_id)`
  - `send_input(serial, action, payload)`
  - `execute_workflow(serial, workflow)`
  - `get_health()`
- [ ] **2.3 Swarm MCP Tool Adapter:** Author `Kelvra/kelvra-bench/src/integrations/device_lab_mcp.py` registering:
  - `mobile_list_devices`
  - `mobile_device_tap`
  - `mobile_device_swipe`
  - `mobile_device_key`
  - `mobile_device_type`
  - `mobile_capture_screenshot`
  - `mobile_run_smoke_test`

### Gate 3: Configuration & Feature Flag Activation
- [ ] **3.1 Environment Variable Template:** Append to `Kelvra/kelvra-bench/.env.example`:
  ```bash
  KELVRA_DEVICE_LAB_ENABLED=false
  KELVRA_DEVICE_LAB_URL=http://127.0.0.1:8098
  ```
- [ ] **3.2 Configuration Loader Update:** Update `Kelvra/kelvra-bench/src/config.py` to read `KELVRA_DEVICE_LAB_ENABLED`.
- [ ] **3.3 Non-Breaking Verification:** Start Bench server with flag set to `false`; verify 100% normal operation.

### Gate 4: Swarm EventBus & UI Docking
- [ ] **4.1 EventBus Forwarder:** Configure Device Lab's event publisher to dispatch events to `POST http://127.0.0.1:8099/api/events`.
- [ ] **4.2 Bench UI Viewport Docking:** In Bench desktop shell, wire navigation route `/devices` to render Device Lab's studio interface pointing to `http://127.0.0.1:8098`.
- [ ] **4.3 Visual Harmony Audit:** Verify seamless Anthropic dark theme (`#262624`, `#1E1E1C`, `#D97757`) alignment between host and docked viewport.

### Gate 5: End-to-End Verification Testing
- [ ] **5.1 Tier 1 Connection Probes:** Verify `GET /api/providers/health` and WebSocket stream handshake.
- [ ] **5.2 Tier 2 EventBus Sync:** Verify mock device discovery event propagates to Bench EventBus.
- [ ] **5.3 Tier 3 Swarm Agent Execution:** Dispatch automated workflow from Bench agent to Device Lab and inspect results.
- [ ] **5.4 Tier 4 Security & Redaction:** Verify token validation, lease mutual exclusion, and log secret scrubbing.
- [ ] **5.5 Standalone Parity Re-Test:** Verify Device Lab continues to function independently on `:8098` when Bench is terminated.

### Gate 6: Final Release Sign-Off
- [ ] **6.1 Zero-Emoji Final Sweep:** Final sweep across all created and updated files.
- [ ] **6.2 Comprehensive Test Pass:** Pytest execution across both repositories.
- [ ] **6.3 Documentation Update:** Update `docs/PROJECT_STATE.md`, `docs/IMPLEMENTATION_LOG.md`, and `docs/VALIDATION_REPORT.md`.
- [ ] **6.4 Present Completion Report:** Present final synchronization audit report to user.
