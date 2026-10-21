# KELVRA Device Lab — Integration Verification & Test Plan

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/INTEGRATION_TEST_PLAN.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Scope:** Post-Authorization Integration Acceptance Verification
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Test Strategy & Objectives

The Integration Test Plan defines the comprehensive suite of tests required to validate that KELVRA Device Lab and KELVRA Bench operate cohesively as an integrated system without compromising standalone teleoperation or stability.

```
+-----------------------------------------------------------------------------------------+
|                                INTEGRATION TEST MATRIX                                  |
+-------------------+--------------------+------------------------+-----------------------+
|  Tier 1: Connect  |  Tier 2: EventBus  |  Tier 3: Control &     |  Tier 4: Standalone   |
|   & Health Probe  |     Sync Loop      |    Agent Execution     |     Parity Gate       |
| (HTTP/WS Handshake| (Fleet & State Bus | (Leases, Taps, In-line | (155/155 regression   |
|   Latency Check)  |    Subscription)   |   Workflow Runners)    |   100% pass guarantee)|
+-------------------+--------------------+------------------------+-----------------------+
```

---

## 2. Granular Test Suite Matrix

### Tier 1: Service Connectivity & Health Handshake
| Test ID | Objective | Preconditions | Verification Procedure | Expected Outcome |
|:---|:---|:---|:---|:---|
| **INT-CON-01** | Loopback HTTP Connection | Device Lab running on `:8098` | Bench client issues `GET http://127.0.0.1:8098/api/providers/health` | HTTP 200 OK returned with structured provider status within < 50ms. |
| **INT-CON-02** | Unreachable Service Degradation | Device Lab stopped | Bench client issues `GET /api/devices` with flag enabled | Caught gracefully; returns `ServiceUnavailable` without unhandled exception. |
| **INT-CON-03** | WebSocket Stream Handshake | Device online in Registry | Bench client opens `ws://127.0.0.1:8098/ws/stream/{serial}` | Binary handshake completes; JPEG binary frames stream continuously. |

---

### Tier 2: Fleet Discovery & EventBus Synchronization
| Test ID | Objective | Preconditions | Verification Procedure | Expected Outcome |
|:---|:---|:---|:---|:---|
| **INT-EVT-01** | Device Discovered Event | Bench EventBus listening on `:8099` | New mock/physical device attached in Device Lab | `DEVICE_DISCOVERED` event posted to `http://127.0.0.1:8099/api/events`; EventBus appends record. |
| **INT-EVT-02** | Device Disconnected Event | Device registered in fleet | Device disconnected or provider teardown | `DEVICE_DISCONNECTED` event posted; Bench fleet inventory updates within 100ms. |
| **INT-EVT-03** | Thermal Alert Propagation | Device battery reporting 43 C | Diagnostics threshold tripped | `DEVICE_THERMAL_ALERT` event delivered; Bench Kanban triggers alert banner. |

---

### Tier 3: Swarm Agent Leases & Control Execution
| Test ID | Objective | Preconditions | Verification Procedure | Expected Outcome |
|:---|:---|:---|:---|:---|
| **INT-CTL-01** | Agent Exclusive Lease Acquisition | Device state `AVAILABLE` | Bench Agent requests lease via `POST /api/leases/{serial}/acquire` | HTTP 200 returned with valid `lease_id`. State transitions to `BUSY`. |
| **INT-CTL-02** | Mutual Exclusion Defense | Device leased by Agent A | Agent B requests lease on same device | HTTP 409 Conflict returned. Agent A's lease remains undisturbed. |
| **INT-CTL-03** | Swarm Automation Workflow Run | Lease active | Bench dispatches `POST /api/automation/execute-inline` | Declarative steps run; artifacts generated; execution report URL returned. |
| **INT-CTL-04** | Normalized Coordinate Injection | Leased device online | POST `/api/devices/{serial}/input/tap` with normalized `{x: 0.5, y: 0.5}` | Device Lab converts to physical pixel bounds; dispatches `adb shell input tap`. |

---

### Tier 4: Security, Redaction & Sandbox Gates
| Test ID | Objective | Preconditions | Verification Procedure | Expected Outcome |
|:---|:---|:---|:---|:---|
| **INT-SEC-01** | Bench Token Authentication | Valid `kbt-` token | Request sent with `Authorization: Bearer kbt-...` | Bridge translates token to scoped Device Lab role; request succeeds. |
| **INT-SEC-02** | Unauthenticated Access Rejection | No token provided | Direct request sent to protected endpoint | HTTP 401 Unauthorized returned. |
| **INT-SEC-03** | Logcat Secret Redaction | Device logging active | Simulated auth failure containing API key written to log | Redacted marker `[REDACTED]` replaces key in circular buffer and export. |
| **INT-SEC-04** | Artifact Directory Anchoring | Artifact catalog populated | Path traversal query `GET /api/artifacts/..%2F..%2Fpasswords/download` | Rejection with HTTP 400 Bad Request; zero traversal beyond `artifacts/`. |

---

### Tier 5: Standalone Parity & Regression Baseline
| Test ID | Objective | Preconditions | Verification Procedure | Expected Outcome |
|:---|:---|:---|:---|:---|
| **INT-REG-01** | Full Device Lab Regression Pass | Independent environment | Run `python -m pytest -q` in `Kelvra/KELVRA Device Lab/` | Exactly 155/155 tests pass at 100% with zero regressions. |
| **INT-REG-02** | Standalone Web UI Verification | Service on `:8098` | Navigate directly to `http://localhost:8098/` in independent browser | Complete 6-route navigation, device studio, and streaming operate autonomously. |
| **INT-REG-03** | Zero Emoji Sweep | Changed and created files | Automated regex sweep for Unicode emoji codepoints | 0 violations found across all files. |

---

## 3. Execution Protocol & Verification Sign-Off

Upon authorized execution of synchronization:
1. Run Tier 5 Standalone Regression baseline (must achieve 155/155 pass).
2. Start both services (`:8098` and `:8099`).
3. Run Tier 1 and Tier 2 connectivity and event tests.
4. Execute Tier 3 agent control and lease tests.
5. Verify Tier 4 security and secret scrubbing.
6. Record full test execution log and attach to formal release audit.
