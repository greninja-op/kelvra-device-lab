# KELVRA Device Lab — Device Trust, Pairing & Hardware Identity

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVICE_TRUST_AND_PAIRING.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Hardware Trust & Device Cryptographic Identity
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Android Device Trust Architecture

### 1.1 ADB Cryptographic Authorization (RSA Keypair)
- **Mechanism:** When a physical Android device is connected to a host workstation for the first time via USB, Android's `adbd` daemon requires the host to authenticate using an asymmetric RSA-2048 keypair stored on the host (`~/.android/adbkey` and `~/.android/adbkey.pub`).
- **Zero-Bypass Policy:** Device Lab **never** attempts to circumvent, spoof, or automate the acceptance of this authorization dialog. Android's security model dictates that physical user confirmation is mandatory.
- **Unauthorized State UX:** When a device returns status `unauthorized`, Device Lab:
  1. Identifies the device serial and hardware model.
  2. Renders an explicit warning banner on the screen viewport.
  3. Displays guidance: *"Device [Model / Serial] requires authorization. Please unlock your physical phone and tap 'Allow USB debugging' on the screen."*
  4. Runs a non-blocking background poll (2-second interval) checking for state transition to `device` (authorized).

### 1.2 Device Identity & Serial Number Integrity
- **Unique Hardware Identity:** A device's authoritative identity is anchored to its permanent hardware serial number reported by ADB (`ro.serialno` or transport ID).
- **Collision Prevention for Identical Models:** When multiple identical devices are attached (e.g. two POCO X6 Pro devices with the same model number `2311DRK48I`), Device Lab partitions them strictly by their unique serial numbers (e.g. `8TCABAIFWOZTDICI` vs `9ABCD123456789EF`).
- **Stale Record Invalidation:** If a device is unplugged, its in-memory status transitions to `OFFLINE`. If it remains offline for > 15 minutes, its transient runtime leases and cached telemetry are purged from active memory while preserving historical test records in SQLite.

### 1.3 Wireless ADB Pairing Trust (Android 11+ / API 30+)
- **Pairing Protocol:** Wireless ADB pairing uses Wi-Fi Protected Setup (WPS) with a 6-digit one-time pairing code and TLS certificate exchange (`adb pair <ip>:<port> <code>`).
- **Local Network Boundary:** Wireless ADB will only be established upon explicit developer initiation; Device Lab will never automatically scan or attach to unauthorized wireless ports on the local network.

---

## 2. Apple iOS Device Trust Architecture

### 2.1 Lockdown Pairing Records & The "Trust This Computer" Handshake
- **Mechanism:** Physical iOS devices require an encrypted SSL pairing certificate exchange managed by Apple's `lockdownd` service. When connected via USB, the iOS device presents the system dialog: *"Trust This Computer?"* requiring the device passcode.
- **Host Pairing Storage:** Successful pairing generates a host certificate stored securely by the host OS (`%ProgramData%\Apple\Lockdown` on Windows).
- **Zero-Bypass Policy:** Device Lab does **not** attempt to inject synthetic touch events or bypass the Apple passcode trust prompt. If pairing is unverified or revoked, the device state is marked as `UNPAIRED / UNAUTHORIZED`.

### 2.2 iOS Developer Mode Requirement (iOS 16+)
- **Security Constraint:** On iOS 16, 17, and 18, developer services (mounting Developer Disk Images, debugging apps, collecting advanced telemetry) require physical activation of **Developer Mode** on the device (`Settings -> Privacy & Security -> Developer Mode`), followed by a device reboot and passcode confirmation.
- **Reporting:** Device Lab inspects the `DeveloperModeStatus` property via lockdown and informs the developer if Developer Mode is disabled.

### 2.3 Signing and Provisioning Boundaries
- **IPA Installation Limits:** Installing applications on iOS devices requires valid cryptographic codesigning:
  - *Enterprise Distribution:* Requires an active enterprise mobileprovision profile.
  - *Development Builds:* Requires an Apple Developer Certificate matching the device's UDID.
- **Fail-Safe Validation:** Device Lab checks whether an IPA bundle is signed before attempting installation via `pymobiledevice3`, preventing silent installation failures.
