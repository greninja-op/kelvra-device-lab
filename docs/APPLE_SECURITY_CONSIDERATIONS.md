# Apple Device Integration Security & Threat Model
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Security Architecture & Threat Vectors

Integrating Apple devices into a shared or multi-tenant lab workstation presents unique attack vectors and security boundaries:

```
+---------------------------------------------------------------+
|                       Threat Model Scope                      |
+---------------------------------------------------------------+
|  Vector 1: Host Pairing Record Theft                          |
|    - Threat: Malicious process reads <UDID>.plist on host     |
|    - Impact: Attacker gains persistent lockdown access        |
|    - Mitigation: Restrict %ProgramData%\Apple\Lockdown ACLs   |
+---------------------------------------------------------------+
|  Vector 2: PII Leakage via Syslog Streaming                   |
|    - Threat: Device syslog exposes tokens, auth cookies, GPS  |
|    - Impact: Sensitive test data leaked across sessions       |
|    - Mitigation: Session isolation & log sanitization filter  |
+---------------------------------------------------------------+
|  Vector 3: Copyleft Licensing Contamination                   |
|    - Threat: In-process import of GPLv3 dependencies          |
|    - Impact: Legal risk to proprietary Device Lab IP          |
|    - Mitigation: Strict CLI subprocess isolation boundary     |
+---------------------------------------------------------------+
```

---

## 2. Lockdown Storage Security

1. **Host-Side Key Protection**:
   - Lockdown records contain cryptographic certificates enabling unrestricted communication with the target device.
   - On Windows, `%ProgramData%\Apple\Lockdown` is secured by Windows Access Control Lists (ACLs) permitting read access only to `SYSTEM` and members of the `Administrators` group.
   - KELVRA Device Lab runs under the operator's user account and accesses pairing files in read-only mode during discovery.
2. **Device Trust Revocation**:
   - Operators can instantly invalidate host trust directly from the physical device:
     `Settings > General > Transfer or Reset iPhone > Reset > Reset Location & Privacy`.
   - Once reset, the host's pairing certificate is rejected by `lockdownd`, immediately transitioning the device to `UNAUTHORIZED` state in KELVRA Device Lab.

---

## 3. Data Sanitization & Session Privacy

Physical Apple test devices frequently run real-world developer builds that log sensitive payloads to the console:
- **Session Purge Protocol**: When a testing session terminates, temporary diagnostic logs and crash artifacts captured during that session are purged from the host cache.
- **Redaction Rules**: Device Lab's logging engine applies regex masks to scrub sensitive credentials (e.g. `Bearer [a-zA-Z0-9_\-\.]+`, `password=`, `session_token=`) before emitting logs to client browsers or external diagnostics collectors.

---

## 4. Software Supply Chain & GPL Isolation

- **Zero In-Process GPL Linking**:
  KELVRA Device Lab backend explicitly prohibits importing GPLv3-licensed packages (`pymobiledevice3`) into the Python interpreter memory space.
- **Process Boundary**: All third-party tools are invoked exclusively via isolated subprocess execution (`subprocess.run`), adhering to the GNU General Public License boundary criteria.
- **Auditing**: Automated CI/CD dependency checkers audit `requirements.txt` to ensure no copyleft-licensed packages are added to the direct dependency tree.
