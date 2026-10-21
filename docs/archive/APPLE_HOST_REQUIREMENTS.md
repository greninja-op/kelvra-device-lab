# Apple Host Requirements & Environment Setup
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Workstation Host Prerequisites

KELVRA Device Lab is designed to run seamlessly on Windows 10/11 x64 developer workstations. To interface with physical Apple iOS and iPadOS hardware, the host machine must satisfy the following baseline requirements:

### 1.1 Mandatory Components
1. **Operating System**: Windows 10 Build 19041+ or Windows 11 (64-bit).
2. **Apple Mobile Device Service (AMDS)**:
   - Provides kernel-level USB drivers (`usbaapl64.sys`) and background multiplexer daemon.
   - Binds loopback TCP socket `127.0.0.1:27015`.
   - Installation sources:
     - Standalone **Apple Devices** application from Microsoft Store (Recommended).
     - Standard **iTunes for Windows** x64 installer.
3. **USB Hardware Interface**:
   - Physical USB 3.0 / USB-C port with MFi-certified Lightning or USB-C high-speed data cable.
   - Direct connection to workstation motherboard ports (avoid unpowered passive USB hubs to prevent bus resets during large payload transfers).

---

## 2. Optional Toolchain Components

To unlock telemetry and diagnostic capabilities (e.g. system logs, battery health queries, and crash reports), one of the following optional toolchains may be installed on the host machine:

### 2.1 libimobiledevice Windows Binaries (Recommended for Lightweight Deployments)
- **Installation**: Place precompiled 64-bit binaries in a folder added to system `PATH` (or `C:\Program Files\libimobiledevice`):
  - `idevice_id.exe`
  - `ideviceinfo.exe`
  - `idevicepair.exe`
  - `idevicesyslog.exe`
- **Verification**: Run `idevice_id -l` in terminal to list connected UDIDs.

### 2.2 pymobiledevice3 CLI (Recommended for Modern iOS 17+ Support)
- **Installation**: Install via isolated Python virtual environment or pipx:
  ```bash
  pipx install pymobiledevice3
  ```
- **CLI Commands Utilized**:
  - `pymobiledevice3 usbmux list-devices`
  - `pymobiledevice3 lockdown info`
- **Isolation Requirement**: Must run out-of-process via CLI execution; direct in-process Python import is forbidden due to GPLv3 licensing.

---

## 3. Storage & Permissions Layout

Device Lab interacts with standard Apple lockdown directories:

| Platform | Lockdown Storage Directory | Access Permissions | Contents |
|---|---|---|---|
| **Windows** | `%ProgramData%\Apple\Lockdown` (`C:\ProgramData\Apple\Lockdown`) | SYSTEM & Administrators (Read/Write) | Host private keys (`HostPrivateKey.pem`), SystemBUID, `<UDID>.plist` pairing certificates |
| **macOS** | `/var/db/lockdown` | `root:wheel` / `_usbmuxd` (Read/Write) | SystemBUID, `<UDID>.plist` |
| **Linux** | `/var/lib/lockdown` | `usbmux:usbmux` (Read/Write) | SystemBUID, `<UDID>.plist` |

---

## 4. Diagnostics & Health Verification

KELVRA Device Lab includes automated environment detection via `AppleEnvironmentDetector`. To verify workstation health:

1. Open KELVRA Device Lab at `http://localhost:8098/#diagnostics`.
2. Locate the **Apple Mobile Services (`usbmuxd`)** diagnostics card.
3. Confirm indicators:
   - **Host Platform**: Windows (`AMD64`).
   - **usbmuxd Port (127.0.0.1:27015)**: `Listening` (Green status dot).
   - **Lockdown Directory**: `Accessible` (Path verified).
   - **Paired Records**: Count of paired devices displayed.
   - **Detected Toolchain**: `libimobiledevice` / `pymobiledevice3` / `Native AMDS`.
