# KELVRA Device Lab — Authorization Policy & Operation Scopes

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/AUTHORIZATION_POLICY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** KELVRA Security & Authorization Governance (`kelvra-security` / `kelvra-bench`)
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Authorization Architecture & Scope Model

Device Lab does not invent an independent credential store. It operates under two operational modes:
1. **Local Development Posture (Default):** Bound to `127.0.0.1:8098`. Requests from localhost are assumed to originate from the authenticated local workstation owner. Sensitive actions still require explicit confirmation modals.
2. **Bench Swarm & Enterprise Posture (`KELVRA_AUTH_REQUIRED=1`):** Every HTTP request and WebSocket handshake must present an authorized KELVRA Bearer token (`kbt-` token) possessing specific composable RBAC scopes.

### Composable RBAC Scopes
- `device:read`: Query fleet, view device metadata, inspect telemetry.
- `device:stream`: Initiate and receive live screen video frames.
- `device:control`: Inject touch coordinates, gestures, keyboard typing, and hardware buttons.
- `device:app:manage`: Install APKs, launch applications, terminate packages.
- `device:app:destructive`: Clear package data, uninstall applications.
- `device:virtual:admin`: Start, snapshot, wipe, or shut down virtual AVD emulators.
- `device:log:read`: Stream live logcat and syslog feeds.
- `device:automation:run`: Dispatch automated test runner scripts and screenshot assertions.
- `device:admin`: Lease preemption, host configuration, diagnostic export.

---

## 2. Granular Operations Authorization Matrix

| Operation | Required Scope | Authorization Authority | Confirmation Modal Needed? | Audit Event Emitted? | Automatable by Agents? | Included in MVP? |
|---|---|---|---|---|---|---|
| **Discover Devices** | `device:read` | Local / Bench Gate | No | No (High frequency) | Yes | Yes |
| **View Device Metadata** | `device:read` | Local / Bench Gate | No | No | Yes | Yes |
| **Connect to Device** | `device:read` | Local / Bench Gate | No | Yes (`DEVICE_CONNECTED`) | Yes | Yes |
| **Approve Device Trust** | Physical Display | Device OS (Android/iOS) | Yes (On Phone Display) | Yes (`DEVICE_AUTHORIZED`) | No (Physical Gate) | Yes |
| **Start Live Stream** | `device:stream` | Local / Bench Gate | No | Yes (`STREAM_STARTED`) | Yes | Yes |
| **Send Touch Input** | `device:control` | Single-Writer Lease | No | No (Telemetry log only) | Yes | Yes |
| **Send Keyboard Input** | `device:control` | Single-Writer Lease | No | No | Yes | Yes |
| **Hardware Key Emulation** | `device:control` | Single-Writer Lease | No | No | Yes | Yes |
| **Install Application (APK)**| `device:app:manage` | Local / Ward Attestation| Operator Confirm / Auto | Yes (`APP_INSTALLED`) | Yes (Test Runner) | Yes |
| **Launch / Stop Application**| `device:app:manage` | Single-Writer Lease | No | Yes (`APP_LIFECYCLE`) | Yes | Yes |
| **Clear Application Data** | `device:app:destructive`| Local Owner / Admin | Yes (Two-Step Modal) | Yes (`APP_DATA_CLEARED`)| Yes (Explicit Flag) | Yes |
| **Uninstall Application** | `device:app:destructive`| Local Owner / Admin | Yes (Two-Step Modal) | Yes (`APP_UNINSTALLED`) | No | Yes |
| **Start / Stop Emulator** | `device:virtual:admin` | Local Owner / Admin | No | Yes (`EMULATOR_STATE`) | Yes | Release 1.x |
| **Wipe Virtual Device** | `device:virtual:admin` | Local Owner / Admin | Yes (Destructive Modal) | Yes (`EMULATOR_WIPED`) | No | Release 1.x |
| **Capture Screenshot** | `device:read` | Local / Bench Gate | No | Yes (`SCREENSHOT_TAKEN`)| Yes | Yes |
| **Record Screen Session** | `device:stream` | Local Owner / Admin | No | Yes (`RECORDING_SAVED`) | Yes | Release 1.x |
| **Read Live Logcat Feed** | `device:log:read` | Local / Bench Gate | No (Secret Redacted) | No | Yes | Yes |
| **Export Diagnostics Bundle**| `device:admin` | Local Owner / Admin | No (Pre-Screened) | Yes (`DIAG_EXPORTED`) | Yes | Yes |
| **Run Automation Suite** | `device:automation:run`| Local Owner / Bench QA | No | Yes (`TEST_SUITE_RUN`) | Yes | Yes |
| **Upload APK / File** | `device:app:manage` | Local / Path Jail | No (Size Checked) | Yes (`FILE_UPLOADED`) | Yes | Yes |
| **Download Screenshot/Log**| `device:read` | Local / Path Jail | No | No | Yes | Yes |
| **Terminate Session / Lease**| `device:control` | Session Owner / Admin | No | Yes (`LEASE_RELEASED`) | Yes | Yes |
| **Reboot Physical Device** | `device:admin` | Local Owner Only | Yes (Destructive Modal) | Yes (`DEVICE_REBOOTED`) | No | Release 1.x |

---

## 3. Dynamic Execution-Time Authorization Verification

To prevent authorization bypass via stale sessions:
1. **Per-Request Scope Check:** Scopes are not evaluated solely at WebSocket connection establishment; every individual privileged command (such as `install_app` or `clear_data`) verifies that the active session token still possesses the required scope at the exact moment of execution.
2. **Lease Validity Check:** Before injecting touch coordinates or keycodes, the `InputController` verifies that the caller's `client_id` matches the current active lease holder registered in `DeviceManager`. If the lease has expired or was revoked by an administrator, the input is immediately dropped with HTTP 403 Forbidden.
3. **Hardware Trust Re-Verification:** If a physical device transitions from `online` to `unauthorized` (e.g. if the developer revoked USB debugging authorizations on the device), all active teleoperation and test leases are immediately revoked.
