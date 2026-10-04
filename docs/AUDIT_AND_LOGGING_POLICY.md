# KELVRA Device Lab — Audit & Logging Security Policy

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/AUDIT_AND_LOGGING_POLICY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Audit Governance, Observability & Data Retention
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Distinction: Security Audit Events vs Operational Diagnostics

Device Lab maintains a strict architectural division between two logging streams:

| Dimension | Security Audit Events | Operational Diagnostics & Logcat |
|---|---|---|
| **Purpose** | Non-repudiable record of state changes, access, and privileged operations. | High-frequency technical debugging and application troubleshooting. |
| **Storage Target** | SQLite `audit_events` table + KELVRA Bench EventBus (`/api/events`). | In-memory circular ring buffer (5,000 lines) + ephemeral WebSocket feed. |
| **Data Payload** | Structured JSON metadata, actor IDs, correlation IDs, authorization status. | Raw system text lines, debug messages, stack traces. |
| **Retention Policy** | Bounded durable retention: 30 days or maximum 10,000 records. | Ephemeral: discarded upon session teardown unless explicitly saved as test evidence. |
| **Privacy Rules** | Strictly forbids personal data, passwords, or raw screen image payloads. | Automated regex filtering redacts API keys and Bearer tokens in real time. |

---

## 2. Canonical Security Audit Event Schema

Every privileged or state-altering operation generates an audit event complying with the canonical schema:

```json
{
  "event_id": "aud-8f2c3a10-91bc",
  "timestamp": "2026-10-04T00:57:00Z",
  "actor": {
    "type": "agent",
    "identity": "agent-qa-worktree-2",
    "client_ip": "127.0.0.1"
  },
  "device": {
    "serial": "8TCABAIFWOZTDICI",
    "platform": "android_physical",
    "model": "POCO X6 Pro 5G"
  },
  "session": {
    "session_id": "sess-39fa1b82",
    "correlation_id": "bench-card-4819"
  },
  "operation": "APP_INSTALL",
  "authorization": {
    "scope_checked": "device:app:manage",
    "outcome": "ALLOWED"
  },
  "result": {
    "status": "SUCCESS",
    "duration_ms": 3420,
    "failure_category": null,
    "details": {
      "package": "com.kelvra.mobile",
      "version_code": 523
    }
  }
}
```

---

## 3. Audited Operations & Event Catalog

The following operations mandate the generation of an immutable security audit event:
1. `DEVICE_ATTACHED` / `DEVICE_DETACHED` (Physical hardware connection changes).
2. `DEVICE_AUTHORIZED` (RSA public key accepted on device display).
3. `LEASE_ACQUIRED` / `LEASE_RELEASED` / `LEASE_REVOKED` (Teleoperation lock transitions).
4. `APP_INSTALLED` / `APP_UNINSTALLED` / `APP_DATA_CLEARED` (Package modifications).
5. `AUTOMATION_RUN_STARTED` / `AUTOMATION_RUN_FINISHED` (Test suite executions).
6. `SECURITY_GATE_BLOCKED` (Attempted unauthorized action, command injection, path traversal).
7. `THERMAL_ALERT_TRIGGERED` (Device battery temperature exceeding 42°C).
8. `DIAGNOSTICS_EXPORTED` (Exporting diagnostic bundles or log archives).

---

## 4. Log Retention & Automatic Purge Policy

To prevent uncontrolled disk growth on developer workstations:
- **Audit Event Table Retention:** The SQLite `audit_events` table maintains an upper bound of **10,000 events** or **30 calendar days**, whichever threshold is reached first. An automatic pruning routine executes at server startup and during daily maintenance sweeps.
- **Evidence Storage Quota:** Test screenshots and evidence reports in `artifacts/evidence/` enforce a storage quota of **2.0 Gigabytes**. If evidence exceeds this cap, the oldest test runs are automatically archived or purged.
