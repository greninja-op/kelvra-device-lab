# KELVRA Device Lab — User Roles & Permissions Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/USER_ROLES_AND_PERMISSIONS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Authority:** KELVRA Security & Bench Access Governance (`kelvra-security` / `kelvra-bench`)
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Governance & Authority Principles

KELVRA maintains a single, unified security and authorization architecture across all subsystems. Device Lab does **not** invent an independent, competing authentication or user credential store.

Instead:
1. **Local Workstation Trust:** During standalone development on localhost (`127.0.0.1:8098`), the active local developer operates as the authoritative Local Device Owner.
2. **Bench Token & Scope Governance:** When integrated into KELVRA Bench or invoked programmatically, Device Lab honors KELVRA Bench API tokens (`kbt-` tokens) and RBAC scopes managed by `Kelvra/kelvra-bench/src/auth_manager.py`.
3. **Hardware Trust Delegation:** Trust verification on mobile devices is ultimately delegated to the physical device operating system (e.g. Android RSA key fingerprint acceptance, iOS "Trust This Computer" dialog).

---

## 2. Defined Roles

### 2.1 Local Device Owner (Human Developer / Administrator)
- The primary developer with physical access to the host workstation and connected USB hardware.
- Holds full administrative permissions across all connected devices, emulators, configuration, and destructive operations.

### 2.2 Authorized Operator (Interactive Human / Senior Agent)
- An authorized user or supervised agent session actively controlling a device.
- Permitted to teleoperate the screen, launch apps, inject text, trigger automation scripts, and capture screenshots/recordings.
- Cannot perform destructive system operations (wiping devices, clearing system partitions, modifying system settings) without explicit Owner elevation.

### 2.3 Read-Only Viewer (Observer / Human Auditor)
- A passive session monitoring device telemetry, viewing live screen streams, or inspecting logcat output.
- Strictly prohibited from injecting touch input, pressing hardware keys, installing applications, or modifying device state.

### 2.4 Automation Process (Autonomous Swarm Agent / CI Runner)
- Headless programmatic process (e.g. Bench Scout/QA agent, PyTest runner) interacting via REST endpoints and WebSocket protocols.
- Permitted to execute pre-approved test plans, install test APKs, evaluate assertions, capture checkpoint evidence, and query telemetry.
- Bounded by strict execution timeouts and sandbox gates. Cannot perform unapproved device reboots or factory wipes.

---

## 3. Permissions Matrix

| Operational Capability | Local Device Owner | Authorized Operator | Read-Only Viewer | Automation Process | Confirmation Gate Required |
|---|---|---|---|---|---|
| **Enumerate Fleet & View Metadata** | Allowed | Allowed | Allowed | Allowed | No |
| **View Live Screen Stream** | Allowed | Allowed | Allowed | Allowed | No |
| **Inspect Live Logcat Feed** | Allowed | Allowed | Allowed | Allowed (Filtered) | No |
| **View Telemetry & Battery Health** | Allowed | Allowed | Allowed | Allowed | No |
| **Interactive Touch & Swipe Injection** | Allowed | Allowed | Denied | Denied (Direct) | No |
| **Keyboard & Text Typing Injection** | Allowed | Allowed | Denied | Denied (Direct) | No |
| **Hardware Key Emulation (Back/Home/Recents)** | Allowed | Allowed | Denied | Allowed (Scripted) | No |
| **Single-Click Screenshot Capture** | Allowed | Allowed | Allowed | Allowed | No |
| **Screen Video Recording** | Allowed | Allowed | Denied | Allowed | No |
| **Install Test Application (APK/IPA)** | Allowed | Allowed | Denied | Allowed (Verified) | Yes (Operator) / Automatic (Test Runner) |
| **Launch / Stop Target Application** | Allowed | Allowed | Denied | Allowed | No |
| **Clear Application Data / Cache** | Allowed | Allowed | Denied | Allowed (Target App Only) | Yes (Impact Warning) |
| **Uninstall 3rd-Party Application** | Allowed | Allowed | Denied | Denied | Yes (Two-Step Modal) |
| **Uninstall System / Privileged Package** | Denied | Denied | Denied | Denied | Hard Blocked |
| **Start / Stop Android Virtual Device (AVD)** | Allowed | Allowed | Denied | Allowed | No |
| **Wipe / Reset Virtual Device State** | Allowed | Denied | Denied | Denied | Yes (Explicit AVD Reset Modal) |
| **Reboot Physical Device** | Allowed | Denied | Denied | Denied | Yes (Destructive Action Modal) |
| **Export Diagnostic Bundles** | Allowed | Allowed | Allowed | Allowed | No (Auto-Redacted) |

---

## 4. Confirmation Gates for Sensitive and Destructive Operations

To prevent accidental data loss or disruption of development devices during active sessions, Device Lab enforces mandatory confirmation gates:

### Gate 1: Application Data Clear (`pm clear <package>`)
- **Trigger:** Request to purge application user data, database, and preferences.
- **Requirement:** Modal dialog displaying package name, associated data paths, and warning: *"This will permanently erase all local application state, SQLite databases, and saved credentials for this package."*
- **Action Required:** Explicit user click on *"Confirm Data Clear"* button.

### Gate 2: Application Uninstallation (`pm uninstall <package>`)
- **Trigger:** Request to remove an installed application.
- **Requirement:** Two-step confirmation verifying that the package is not a core system component (`/system/app`, `/system/priv-app`).
- **Action Required:** User confirmation with package identifier verification.

### Gate 3: Virtual Device State Wipe (`emulator -wipe-data`)
- **Trigger:** Resetting an emulator snapshot or restoring a clean user data partition.
- **Requirement:** Warning highlighting that all downloaded assets, offline models, and test databases inside the emulator will be destroyed.

### Gate 4: Secret Redaction in Exported Logs
- **Trigger:** Exporting logcat slices or diagnostics bundles for bug reporting or Ward attestation.
- **Requirement:** Automated pre-export screening pass redacting detected secrets (Bearer tokens, API keys, private passwords, and private crypto keys) matching KELVRA Security rules.
