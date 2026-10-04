# KELVRA Device Lab — Security Test Plan & Verification Procedures

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SECURITY_TEST_PLAN.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Security Assurance & Automated Verification Suites
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Security Testing Strategy

Security verification in Device Lab is integrated into the automated PyTest suite. All tests execute deterministically against mock hardware providers or loopback interfaces to ensure repeatable, regression-proof validation without requiring physical devices.

---

## 2. Security Test Cases Specification

| Test ID | Security Dimension | Test Description & Inputs | Expected Pass Condition |
|---|---|---|---|
| **ST-01** | Authorization Failure | Request `POST /api/devices/{serial}/input/tap` with no auth token when auth mode is active. | Immediate HTTP `401 Unauthorized` response with standard error envelope. |
| **ST-02** | Missing Scope | Request `POST /api/devices/{serial}/apps/install` using token possessing only `device:read`. | Immediate HTTP `403 Forbidden` (`code: INSUFFICIENT_SCOPE`). |
| **ST-03** | Expired Token | Send WebSocket handshake with token past its `exp` timestamp. | WebSocket connection rejected with status code `4401`. |
| **ST-04** | Invalid Session ID | Send input payload referencing non-existent `session_id`. | HTTP `404 Not Found` (`code: SESSION_NOT_FOUND`). |
| **ST-05** | Command Injection (Text) | Call `POST /api/devices/{serial}/input/text` with body: `{"text": "test; rm -rf /sdcard\n"}`. | Metacharacters `;` and `\n` are sanitized or rejected; zero shell chaining occurs. |
| **ST-06** | Command Injection (Args) | Provide shell metacharacters in package name parameter: `com.kelvra.mobile; reboot`. | Regex validation rejects package name with HTTP `422 Unprocessable Entity`. |
| **ST-07** | Path Traversal (Upload) | Attempt upload with filename `../../../../Windows/System32/evil.apk`. | Filename stripped to `evil.apk`; file stored strictly inside `scratch/`. |
| **ST-08** | Path Traversal (Download) | Request `GET /api/artifacts/download?file=../../../../Windows/win.ini`. | Path jail check rejects request with HTTP `403 Forbidden` (`code: PATH_TRAVERSAL_DETECTED`). |
| **ST-09** | Symlink Escape | Attempt to read target file that is a symlink pointing outside `artifacts/evidence/`. | Symlink resolution check detects boundary violation; access denied. |
| **ST-10** | Oversized Upload | Attempt upload of APK payload exceeding 150 Megabytes (155 MB payload). | HTTP `413 Payload Too Large` returned before buffering into memory. |
| **ST-11** | Malformed Input | Submit malformed JSON body missing required fields to `/api/devices/{serial}/input/tap`. | HTTP `422 Unprocessable Entity` with Pydantic field error details. |
| **ST-12** | Secret Redaction | Inject synthetic log line: `Bearer kbt-99887766554433221100aabbccddeeff` into logcat feed. | Streamed output replaces credential with `[REDACTED_SECRET]`. |
| **ST-13** | Concurrent Control Collision | Session A acquires lease. Session B attempts `POST /api/devices/{serial}/input/tap`. | Session B receives HTTP `409 Conflict` (`code: DEVICE_ALREADY_LEASED`). |
| **ST-14** | Process Timeout Enforcement | Simulate hanging child process taking > 10s. | Subprocess terminated via `asyncio.wait_for`; HTTP `504 Gateway Timeout` returned. |
| **ST-15** | Child Process Cleanup | Abruptly close video WebSocket during active stream. | Stream worker process reaped within <= 500ms; zero zombie PIDs remain. |
| **ST-16** | System App Protection | Request `POST /api/devices/{serial}/apps/uninstall` with `com.android.settings`. | Hard block triggered; HTTP `403 Forbidden` (`code: SYSTEM_PACKAGE_PROTECTED`). |
