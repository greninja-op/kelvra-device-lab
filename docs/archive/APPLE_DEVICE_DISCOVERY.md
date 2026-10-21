# Apple Physical Device Discovery Architecture
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Discovery Pipeline Overview

Device discovery for physical Apple devices operates through a resilient, multi-tiered pipeline that gracefully degrades across diverse host environments.

```
                         [ Discovery Trigger ]
                                  |
                                  v
                    Is usbmuxd port active? (27015)
                                  |
                 +----------------+----------------+
                 | Yes                             | No
                 v                                 v
      Is CLI toolchain present?           Return empty list
                 |                        (Report usbmux offline)
        +--------+--------+
        |                 |
     Yes                  No
        v                 v
   Invoke CLI      Inspect Lockdown Store
  (idevice_id /    (%ProgramData%\Apple\Lockdown)
 pymobiledevice3)         |
        |          Scan <UDID>.plist files
        |                 |
        +--------+--------+
                 |
                 v
        Parse Device Records
                 |
                 v
        Resolve Product Type
      (AppleDeviceModelMapper)
                 |
                 v
     Evaluate Trust & Pairing
                 |
                 v
  Construct Domain `Device` Models
                 |
                 v
     Register in DeviceRegistry
```

---

## 2. Multi-Tiered Discovery Strategies

### Strategy A: CLI Toolchain Invocation (Primary When Installed)
When `libimobiledevice` or `pymobiledevice3` is discovered on the host system:
1. `idevice_id -l` is executed via subprocess with a strict 2.0-second timeout.
2. The command outputs the UDIDs of all currently attached physical devices.
3. For each discovered UDID, `ideviceinfo -u <UDID> -s` is invoked to retrieve atomic device metadata:
   - `DeviceName`
   - `ProductType` (e.g. `iPhone15,2`)
   - `ProductVersion` (e.g. `17.4.1`)
   - `CPUArchitecture` (e.g. `arm64`)
   - `BatteryCurrentCapacity`

### Strategy B: Lockdown Pairing Record Inspection (Resilient Fallback)
If no third-party CLI binaries are installed, but the native Apple Mobile Device Service is running:
1. `AppleDeviceProvider` directly inspects the system lockdown storage directory:
   `C:\ProgramData\Apple\Lockdown`
2. All `.plist` files matching UDID format (`^[a-fA-F0-9\-]{25,40}\.plist$`) are parsed using Python's native `plistlib`.
3. The pairing record yields:
   - `DeviceName` (stored friendly host label)
   - `UDID` (extracted from record filename)
   - `SystemBUID` / `HostID`
4. The provider verifies socket connectivity to the target device through usbmuxd to validate whether the paired device is physically attached.

---

## 3. UDID Format & Normalization

Apple devices utilize two primary UDID representations:

1. **Legacy 40-character Hexadecimal** (iPhone 4 through iPhone X):
   - Example: `40a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9`
   - Format: Pure 40-byte lowercase hex string without hyphens.
2. **Modern 25-character Hyphenated Hexadecimal** (iPhone XS, iPhone 11 through iPhone 16+):
   - Example: `00008030-001144A83653C02E`
   - Format: 8 hex digits, hyphen, 16 hex digits (total 25 characters).

`AppleDeviceProvider` normalizes all identifiers to uppercase with preserved hyphens for consistency across the registry.

---

## 4. Discovery Performance & Error Handling

- **Non-Blocking Operation**: Discovery routines run asynchronously via thread executors to ensure the FastAPI server loop remains fully responsive at 120 FPS UI render speeds.
- **Strict Timeouts**: Subprocess commands have a hard cutoff of 2.0 to 3.0 seconds to prevent lingering hangs if a device enters a non-responsive sleep state.
- **Clean Failure Boundaries**: If `usbmuxd` is unreachable, `discover_devices()` immediately returns an empty list without raising unhandled exceptions or corrupting the global `DeviceRegistry`.
