# KELVRA Device Lab — Connection Workflow & Device Trust UX

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/CONNECTION_WORKFLOW_UX.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Security Architecture & Trust Policies (Phase 5)
- **Status:** Verified Connection Workflow Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Trust Philosophy

Connecting physical hardware to a workstation involves low-level operating system security boundaries (Android ADB RSA keys, USB driver enumeration, Apple iOS Lockdown trust).

The connection user experience must:
1. **Be Honest and Transparent:** Accurately reflect the exact state reported by the ADB daemon or platform driver.
2. **Provide Actionable Recovery Guidance:** Tell users precisely what to do on their physical hardware without ambiguous jargon.
3. **Never Encourage Security Bypasses:** Do not instruct users to disable lock screens, disable verification, or install untrusted certificates.
4. **Differentiate Unavailable vs Failed States:** A feature unavailable due to missing host binaries (e.g. `scrcpy-server` not bundled) is handled differently from an active execution failure.

---

## 2. The 12 Connection Operational States

### 2.1 State 1: No Device Detected
- **Detection Trigger:** `adb devices` returns an empty list, and no local AVD instances are running.
- **Visual Display:** Clean, unhurried empty state on `--bg-canvas` (`#262624`).
- **Heading:** "No mobile devices detected" (Lora 19px, `--text-primary`).
- **Description:** "Connect an Android device via USB with USB Debugging enabled, or boot a local virtual emulator."
- **Direct Guidance Checklist:**
  - Verify USB cable is firmly connected and supports data transfer (not charge-only).
  - Verify Developer Options are enabled on the phone (*Settings > About Phone > Tap Build Number 7 times*).
  - Ensure ADB daemon is active on port 5037.
- **Action Buttons:** `.btn.primary` "Scan for Devices" | `.btn` "Start Virtual Device".

### 2.2 State 2: Device Discovered (Initial Handshake)
- **Detection Trigger:** ADB detects a new USB vendor/product ID in `host` state.
- **Visual Display:** Subtle notification banner with quiet green dot: "New device detected: Negotiating USB transport...".

### 2.3 State 3: Device Unauthorized (RSA Key Prompt)
- **Detection Trigger:** `adb devices` reports status `unauthorized`.
- **Visual Display:** Prominent status card on `--bg-elevated` with an amber status dot (`#F59E0B`).
- **Heading:** "Device authorization required" (Lora 19px).
- **Description:** "Device `POCO X6 Pro 5G (8TCABAIFWOZTDICI)` is attached but has not authorized this computer's RSA key."
- **Actionable Steps:**
  1. Unlock your physical phone.
  2. Look for the system dialog titled **'Allow USB debugging?'**.
  3. Check the box **'Always allow from this computer'**.
  4. Tap **'Allow'**.
- **Live Polling Indicator:** Background poller checks authorization status every 1.5 seconds. As soon as the user taps 'Allow', the screen smoothly transitions to State 6 (Connecting) without a page refresh.

### 2.4 State 4: USB Debugging Disabled / Charge Only Mode
- **Detection Trigger:** Device enumerates on Windows USB bus (visible in Win32 USB controller) but does not respond to ADB daemon.
- **Visual Display:** Informational guidance box:
  - "USB device detected on port, but ADB interface is not responding."
  - "Ensure USB configuration is set to 'File Transfer (MTP)' or 'PTP' rather than 'Charge only', and that USB Debugging is toggled ON in Developer Options."

### 2.5 State 5: Wireless ADB Pairing Required
- **Detection Trigger:** User initiates Wi-Fi pairing from `/devices/connect`.
- **Form Fields:** `Device IP Address`, `Pairing Port`, `6-digit Pairing Code`.
- **Guidance:** "On Android 11+, navigate to *Settings > Developer Options > Wireless Debugging > Pair device with pairing code*."
- **Progress:** Live validation feedback upon submission (`adb pair ip:port code`).

### 2.6 State 6: Connecting & Negotiating Resolution
- **Detection Trigger:** Device authorized; stream pipeline spinning up.
- **Visual Display:** Quiet emerald dot (`#10B981`) with label: "Initializing stream pipeline for POCO X6 Pro 5G... Querying native resolution (1220x2712)...".

### 2.7 State 7: Connection Successful & Stream Online
- **Detection Trigger:** WebSocket receives first valid video frame and telemetry socket opens.
- **Visual Display:** Smooth transition to Live Device Viewer canvas. Telemetry HUD activates (`30 FPS · 38ms`).

### 2.8 State 8: Connection Failure (Pipeline Error)
- **Detection Trigger:** Subprocess error or socket timeout during pipeline startup.
- **Visual Display:** Error card with crimson dot (`#EF4444`).
- **Copy:** "Failed to negotiate stream pipeline with device 8TCABAIFWOZTDICI. Port 8098 socket rejected or ADB buffer exhausted."
- **Action:** Primary button "Retry Connection" | Secondary button "View Diagnostics Log".

### 2.9 State 9: Unexpected Disconnection (Cable Pulled)
- **Detection Trigger:** Heartbeat timeout or ADB `device disconnected` event during active session.
- **Visual Display:** Viewer canvas freezes last valid frame with 60% dark charcoal wash.
- **Copy:** "USB connection lost for POCO X6 Pro 5G. Background stream halted safely."
- **Automatic Recovery:** If cable is reconnected within 30 seconds, session automatically re-establishes the stream.

### 2.10 State 10: Reconnection In Progress
- **Detection Trigger:** Cable re-inserted after disconnection.
- **Visual Display:** Amber status indicator: "Reconnecting to device 8TCABAIFWOZTDICI (Attempt 1/3)...".

### 2.11 State 11: Unsupported Platform Capability
- **Detection Trigger:** Attempting an operation unsupported on target platform (e.g. running Android APK install on iOS device, or interactive touch on iOS connected to Windows host).
- **Visual Display:** Neutral informational badge (`#8A867E`).
- **Copy:** "Interactive touch injection for Apple iOS requires a macOS host workstation. Syslog capture and device telemetry remain active."

### 2.12 State 12: Missing Required Host Runtime
- **Detection Trigger:** Host system does not have `adb.exe` on PATH or specified in settings.
- **Visual Display:** Blocking setup card with amber warning dot (`#F59E0B`).
- **Heading:** "Android SDK Platform-Tools Missing" (Lora 19px).
- **Description:** "Device Lab requires `adb.exe` to discover and communicate with Android devices. It was not found in your system PATH."
- **Actionable Steps:**
  - Install Android Studio or standalone Platform-Tools.
  - Or configure the exact path in `Device Lab Settings` (`/settings`).
  - Action button: "Open Settings".

---

## 3. Multi-Device Conflict Prevention

When multiple Android devices are connected simultaneously:
- Every ADB command is strictly isolated using `-s <serial>`.
- The UI displays explicit device selector dropdowns so users and agents never execute a command or install an APK onto the wrong target device.
- Device identity chips always pair the human-readable model name with the hardware serial (e.g. `POCO X6 Pro 5G (8TCABAIFWOZTDICI)`).
