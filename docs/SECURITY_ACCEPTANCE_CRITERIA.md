# KELVRA Device Lab — Security Acceptance Criteria (MVP)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SECURITY_ACCEPTANCE_CRITERIA.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Verification Authority:** Quality Assurance & Security Gatekeeper
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Security Acceptance Criteria Matrix

Every criterion below represents an unconditional security gate required for production and MVP readiness:

| Criteria ID | Category | Observable Test Condition | Mandatory Pass Outcome |
|---|---|---|---|
| **SEC-AC-01** | Process Privileges | Execute `whoami` check on running Device Lab process. | Process must **never** run with elevated Administrator / LocalSystem tokens. |
| **SEC-AC-02** | Shell Safety | Automated fuzzing sweep passing 50 shell injection payloads into `input_controller.py`. | **0 payloads** execute shell chaining; all are sanitized or safely escaped. |
| **SEC-AC-03** | Path Jail | Fuzzing directory traversal vectors (`../`, `..\\`, `%2e%2e`) across download/upload endpoints. | **100% of requests** targeting files outside `artifacts/` or `scratch/` are rejected with HTTP 403. |
| **SEC-AC-04** | Secret Redaction | Streaming 1,000 synthetic log lines containing diverse API keys, tokens, and private keys. | **0 plaintext secrets** appear in WebSocket stream; all are replaced with `[REDACTED_SECRET]`. |
| **SEC-AC-05** | Lease Exclusivity | Dispatched 20 concurrent touch requests from unauthorized Session B while Session A holds lease. | **100% of Session B requests** are rejected with HTTP 409 Conflict. |
| **SEC-AC-06** | Orphan Prevention | Spawning 10 streaming and logcat sessions followed by abrupt process termination (`taskkill`). | **0 lingering child processes** remain active in Windows process table. |
| **SEC-AC-07** | Upload Caps | Submitting an APK upload payload of 151 Megabytes. | Immediate HTTP `413 Payload Too Large` returned within <= 100ms. |
| **SEC-AC-08** | System Protection | Requesting uninstall of `com.android.systemui` or `com.android.settings`. | Hard-blocked; returns HTTP 403 Forbidden with `SYSTEM_PACKAGE_PROTECTED`. |
| **SEC-AC-09** | Localhost Bound | Scanning open ports on host workstation across all interfaces. | Port `:8098` is bound exclusively to `127.0.0.1`; external LAN interfaces return Connection Refused. |
| **SEC-AC-10** | Zero-Emoji Rule | Automated regex sweep (`[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]`) across all files. | **0 violations found** (100% clean). |
