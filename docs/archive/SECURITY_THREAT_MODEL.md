# KELVRA Device Lab — Comprehensive Security Threat Model (STRIDE)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SECURITY_THREAT_MODEL.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Methodology:** STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
- **Authority:** Threat Modeling & Attack Surface Assessment
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Threat Modeling Scope & Assets

The threat model evaluates risks against five primary asset categories:
1. **Host Workstation:** Host OS integrity, filesystem storage, CPU/RAM resources, developer source code.
2. **Connected Mobile Devices:** Device firmware, system partition, user-space data, hardware longevity (battery/thermals).
3. **Application State & Services:** FastAPI server, in-memory device registry, exclusive writer leases, test queues.
4. **Data & Artifacts:** Captured screenshots, video streams, logcat buffers, test evidence, configuration files.
5. **Upstream Integrations:** KELVRA Bench EventBus, sibling repositories, agent swarm communications.

---

## 2. Exhaustive 15-Scenario STRIDE Threat Matrix

### TM-01: Malicious or Malformed APK Upload
- **STRIDE Category:** Tampering / Elevation of Privilege.
- **Asset at Risk:** Target mobile device OS, host storage.
- **Threat Actor:** Malicious user, compromised upstream build artifact, rogue agent.
- **Entry Point:** HTTP `POST /api/devices/{serial}/apps/install` multipart upload.
- **Potential Impact:** Exploit vulnerabilities in Android package manager; install ransomware or persistent spyware on test hardware; zip bomb consuming host disk space.
- **Existing Protection:** Standard Android package installer signature verification.
- **Required Mitigation:** Strict upload size cap (150 MB); pre-install zip/manifest validation; package name inspection; no auto-install on upload; post-install scratch cleanup.
- **Residual Risk:** Low. Android OS sandbox contains unprivileged application execution.
- **Verification Method:** Unit test uploading corrupted and oversized ZIP files; assert HTTP 400 rejection.

### TM-02: Unauthorized Local API Access
- **STRIDE Category:** Elevation of Privilege / Information Disclosure.
- **Asset at Risk:** All connected devices, live screen streams, input teleoperation.
- **Threat Actor:** Malicious local process on developer machine; untrusted browser tab (CSRF).
- **Entry Point:** HTTP REST endpoints on port `:8098`.
- **Potential Impact:** Hijack control of physical device; exfiltrate screen contents.
- **Existing Protection:** Localhost loopback binding (`127.0.0.1`).
- **Required Mitigation:** Origin header validation rejecting cross-origin requests; KELVRA Bench token header verification (`kbt-` tokens) when auth mode is active.
- **Residual Risk:** Low. Requires local machine compromise to access loopback.
- **Verification Method:** Send cross-origin fetch from simulated malicious origin; assert 403 Forbidden.

### TM-03: Device-Control Command Injection
- **STRIDE Category:** Tampering / Elevation of Privilege.
- **Asset at Risk:** Android shell environment (`adbd`), device filesystem.
- **Threat Actor:** Attacker supplying malicious text input via typing teleoperation or API parameters.
- **Entry Point:** `POST /api/devices/{serial}/input/text`.
- **Potential Impact:** Execution of arbitrary shell commands on device (e.g. `input text "hello; rm -rf /sdcard"`).
- **Existing Protection:** ADB command separation.
- **Required Mitigation:** Complete prohibition of shell string concatenation (`shell=False`); strict input regex sanitizing shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `\n`).
- **Residual Risk:** Minimal.
- **Verification Method:** Automated fuzzing test passing command injection vectors into text injection endpoint; verify zero shell execution.

### TM-04: Path Traversal During File Transfer
- **STRIDE Category:** Information Disclosure / Tampering.
- **Asset at Risk:** Host filesystem outside Device Lab workspace.
- **Threat Actor:** Client submitting manipulated file paths.
- **Entry Point:** `GET /api/artifacts/download?path=...` or APK upload filename.
- **Potential Impact:** Arbitrary file read (reading `.ssh/id_rsa`, `.env`) or file overwrite on host.
- **Existing Protection:** Local workspace separation.
- **Required Mitigation:** Canonical path resolution via `pathlib.Path.resolve()`; mandatory prefix check ensuring resolved path begins with `/artifacts/evidence/`; rejection of `..` segments.
- **Residual Risk:** Zero.
- **Verification Method:** Security test requesting `../../../../Windows/System32/drivers/etc/hosts`; verify 403 Forbidden.

### TM-05: Malicious Executable Replacement
- **STRIDE Category:** Tampering / Elevation of Privilege.
- **Asset at Risk:** Host execution environment.
- **Threat Actor:** Malicious software on host replacing `adb.exe` or `scrcpy-server.jar`.
- **Entry Point:** Filesystem replacement of binaries.
- **Potential Impact:** Execution of arbitrary hostile binaries during device management.
- **Existing Protection:** Standard OS filesystem permissions.
- **Required Mitigation:** Cryptographic SHA-256 hash verification for bundled binary payloads (`scrcpy-server.jar`); explicit path allowlisting for host ADB platform-tools.
- **Residual Risk:** Low.
- **Verification Method:** Modify bundled jar byte; verify startup hash check fails closed.

### TM-06: Stolen Session Token / Token Replay
- **STRIDE Category:** Spoofing.
- **Asset at Risk:** Active device teleoperation session.
- **Threat Actor:** Eavesdropping process or rogue browser script.
- **Entry Point:** HTTP Authorization header / WebSocket query parameter.
- **Potential Impact:** Unauthorized actor taking over an active session.
- **Existing Protection:** Local loopback encryption where supported.
- **Required Mitigation:** Bounded token TTL; single-writer lease tied to specific client IDs; token revocation via KELVRA Bench auth manager.
- **Residual Risk:** Low on localhost.
- **Verification Method:** Test token expiry; verify immediate 401 Unauthorized rejection upon expiration.

### TM-07: Unauthorized Screen Viewing
- **STRIDE Category:** Information Disclosure.
- **Asset at Risk:** Confidential mobile screen contents (credentials, source code, personal data).
- **Threat Actor:** Unauthorized local user or unauthorized agent.
- **Entry Point:** WebSocket `/ws/stream/{serial}`.
- **Potential Impact:** Viewing proprietary UI screens or private credentials.
- **Existing Protection:** Token-gated stream endpoint.
- **Required Mitigation:** WebSocket handshake verifies `device:stream` scope; stream closes immediately upon token revocation.
- **Residual Risk:** Low.
- **Verification Method:** Attempt WebSocket handshake without token when auth is required; verify 4401 rejection.

### TM-08: Cross-Session State Access & Input Thrashing
- **STRIDE Category:** Tampering / Denial of Service.
- **Asset at Risk:** Running automated test suite on connected device.
- **Threat Actor:** Concurrent human user or secondary swarm agent attempting simultaneous control.
- **Entry Point:** Input teleoperation endpoints.
- **Potential Impact:** Corrupting active test runs; conflicting clicks causing misclicks and test failures.
- **Existing Protection:** None in naive tools.
- **Required Mitigation:** Single-Writer Lease model. Only one session holds writer lock; all other concurrent attempts receive HTTP 409 Conflict.
- **Residual Risk:** Zero.
- **Verification Method:** Concurrency unit test acquiring lease with Session A; verify Session B input commands are rejected with 409.

### TM-09: Host Privilege Escalation via Device Lab
- **STRIDE Category:** Elevation of Privilege.
- **Asset at Risk:** Host OS administrative permissions.
- **Threat Actor:** Compromised APK or malicious device command attempting to escalate to Administrator/Root.
- **Entry Point:** Subprocess execution layer.
- **Potential Impact:** Full host compromise.
- **Existing Protection:** Standard user privilege boundary.
- **Required Mitigation:** Least privilege invariant. Device Lab runs strictly as standard user; never runs elevated; never invokes `runas` or `sudo`.
- **Residual Risk:** Minimal.
- **Verification Method:** Audit process execution flags; verify zero elevated process tokens.

### TM-10: Host Resource Exhaustion (Denial of Service)
- **STRIDE Category:** Denial of Service.
- **Asset at Risk:** Host CPU, RAM, and disk space.
- **Threat Actor:** High-velocity logcat spam, runaway frame generation, or memory leaks.
- **Entry Point:** Device streaming and logcat consumers.
- **Potential Impact:** Workstation freezes; IDE crashes; other terminal sessions disrupted.
- **Existing Protection:** Process termination.
- **Required Mitigation:** Circular buffer caps on logcat (5,000 lines); WebSocket backpressure frame dropping (max 2 frames queued); adaptive frame rate throttling.
- **Residual Risk:** Low.
- **Verification Method:** Stress test pumping 10,000 lines/sec into logcat stream; verify host RAM remains < 140 MB.

### TM-11: Malformed Device Protocol Responses
- **STRIDE Category:** Tampering / Denial of Service.
- **Asset at Risk:** Device Lab server parser stability.
- **Threat Actor:** Malfunctioning or compromised device returning corrupted ADB or usbmuxd packets.
- **Entry Point:** Local TCP sockets (`5037`, usbmuxd).
- **Potential Impact:** Server buffer overflow, unhandled exception crashing the main server.
- **Existing Protection:** High-level Python socket wrappers.
- **Required Mitigation:** Strict length-prefixed packet validation; exception isolation at provider boundary ensuring individual device errors do not crash the server.
- **Residual Risk:** Minimal.
- **Verification Method:** Unit test feeding malformed bytes to ADB response parser; verify clean exception trapping.

### TM-12: Compromised Third-Party Dependency (Supply Chain)
- **STRIDE Category:** Tampering / Information Disclosure.
- **Asset at Risk:** Entire Device Lab codebase and execution environment.
- **Threat Actor:** Malicious package author publishing compromised wheel on PyPI.
- **Entry Point:** `pip install -r requirements.txt`.
- **Potential Impact:** Host credential theft, arbitrary remote code execution.
- **Existing Protection:** Dependency isolation in project venv.
- **Required Mitigation:** Pinned semantic versions in `requirements.txt` with SHA-256 wheel hashes; automated vulnerability audits via `pip-audit`.
- **Residual Risk:** Low.
- **Verification Method:** Audit `requirements.txt` against vulnerability database.

### TM-13: Unsafe Diagnostic Export (Secret Exfiltration)
- **STRIDE Category:** Information Disclosure.
- **Asset at Risk:** Developer credentials, API keys, private passwords.
- **Threat Actor:** User or agent exporting diagnostic bundles for bug tracking.
- **Entry Point:** `POST /api/diagnostics/export`.
- **Potential Impact:** Secret keys embedded in device logs are published to public trackers.
- **Existing Protection:** None in raw logcat.
- **Required Mitigation:** Automated pre-export regex redaction pass scrubbing Bearer tokens, passwords, and private keys.
- **Residual Risk:** Low.
- **Verification Method:** Export diagnostic log containing fake API key; verify output contains `[REDACTED_SECRET]`.

### TM-14: Unexpected Process Persistence (Zombie Subprocesses)
- **STRIDE Category:** Denial of Service.
- **Asset at Risk:** Host process table, USB port forwards, battery drain.
- **Threat Actor:** Unclean shutdown, abrupt server crash, or unhandled exception.
- **Entry Point:** Host process lifecycle.
- **Potential Impact:** Lingering `scrcpy-server` or `adb logcat` processes consuming background CPU and locking USB ports.
- **Existing Protection:** Manual Task Manager kill.
- **Required Mitigation:** Active PID registry with `atexit` termination handlers; startup orphan cleanup pass removing stale port forwards.
- **Residual Risk:** Low.
- **Verification Method:** Kill server via `taskkill /F`; restart server and verify orphan cleanup pass reaps previous processes.

### TM-15: Unauthorized Wireless ADB Network Access
- **STRIDE Category:** Spoofing / Tampering.
- **Asset at Risk:** Mobile device shell over local network.
- **Threat Actor:** Malicious device or rogue host on same Wi-Fi network.
- **Entry Point:** Wireless ADB port (`tcp:5555`).
- **Potential Impact:** Hijacking mobile device over Wi-Fi without physical USB cable.
- **Existing Protection:** Android 11+ TLS pairing.
- **Required Mitigation:** Wireless ADB pairing requires explicit 6-digit PIN handshake; Device Lab never enables wireless ADB automatically without explicit user trigger.
- **Residual Risk:** Low.
- **Verification Method:** Verify pairing handshake protocol requires explicit PIN input.
