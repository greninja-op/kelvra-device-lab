# Apple Platform Research & Tooling Investigation
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Executive Summary

This document captures the technical investigation, protocol analysis, and tooling evaluation conducted for integrating Apple iOS and iPadOS physical devices into KELVRA Device Lab on Windows workstations and cross-platform developer environments.

Unlike Android, which provides an open, bidirectional debugging and streaming protocol through standard `adb` daemon sockets, Apple's mobile operating system architecture is strictly sandboxed, cryptographically locked, and heavily optimized for macOS-first developer workflows.

This investigation establishes:
- The foundational communication mechanisms for iOS/iPadOS over USB (`usbmuxd`).
- The role and structure of Apple Mobile Device Service (AMDS) on Windows.
- The state, licensing, and reliability of third-party libraries (`libimobiledevice`, `pymobiledevice3`).
- The limitations of automation frameworks (WebDriverAgent, XCUITest) on non-macOS hosts.
- Concrete architectural boundaries between supported telemetry/diagnostics and unsupported interactive screen streaming.

---

## 2. Low-Level Protocol Architecture: The usbmux Layer

All physical USB communication between a host computer and an iOS/iPadOS device flows through a multiplexing protocol known as **usbmux** (USB Multiplexor).

### 2.1 Protocol Topology

```
+-------------------------------------------------------------+
|                     Host Workstation                        |
|                                                             |
|  +-------------------------------------------------------+  |
|  |             KELVRA Device Lab (Port 8098)             |  |
|  +-------------------------------------------------------+  |
|                            |                                |
|                            v (TCP Socket 127.0.0.1:27015)   |
|  +-------------------------------------------------------+  |
|  |           usbmuxd / AppleMobileDeviceService          |  |
|  +-------------------------------------------------------+  |
+----------------------------|--------------------------------+
                             | USB Bulk Transfer Endpoints
                             v
+-------------------------------------------------------------+
|               Target iOS / iPadOS Device                    |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                    lockdownd                          |  |
|  |   (Authentication, Pairing, Service Demultiplexing)   |  |
|  +-------------------------------------------------------+  |
|           |                   |                  |          |
|           v                   v                  v          |
|      syslog_relay      installation_proxy     diagnostics   |
+-------------------------------------------------------------+
```

### 2.2 Wire Protocol Mechanics
- **Transport**: Encapsulated within USB Bulk endpoints across standard Lightning or USB-C cables.
- **Multiplexer Daemon**: A background service (`usbmuxd` on Linux/macOS, `AppleMobileDeviceService.exe` on Windows) binds to loopback interface `127.0.0.1` on TCP port `27015` (or `/var/run/usbmuxd` UNIX domain socket).
- **Packet Structure**: 16-byte header consisting of:
  - `Length` (uint32, little-endian): Total packet length including header.
  - `Version` (uint32): Version 1 (XML plist) or Version 0 (binary payload).
  - `Request` (uint32): Message type identifier (`Listen`, `Connect`, `Result`).
  - `Tag` (uint32): Correlation sequence number.
- **Service Handshake**:
  1. Client sends `Listen` packet to `usbmuxd`.
  2. `usbmuxd` broadcasts `Attached` / `Detached` events with device ID, serial (UDID), and connection speed.
  3. Client sends `Connect` request specifying device ID and port number (e.g., port 62078 for `lockdownd`).
  4. `usbmuxd` bridges socket to target device daemon.

---

## 3. Host Tooling Landscape

### 3.1 Apple Mobile Device Support (AMDS) on Windows
- **Distribution**: Bundled with iTunes for Windows or standalone Apple Devices app from Microsoft Store.
- **Components**:
  - `AppleMobileDeviceService.exe` (AMDS daemon listening on TCP `127.0.0.1:27015`).
  - `AppleMobileDeviceSupport64.msi` (Kernel drivers `usbaapl64.sys`).
  - Lockdown directory: `%ProgramData%\Apple\Lockdown` storing cryptographic host/device trust pairings (`<UDID>.plist`).
- **Suitability**: Highly stable for physical USB link layer and driver binding, but provides zero CLI utilities or public programmatic C/Python APIs for third-party tools.

### 3.2 libimobiledevice Suite
- **Origins**: Reverse-engineered open-source implementation of Apple device protocols.
- **Core CLI Tools**:
  - `idevice_id`: List connected device UDIDs.
  - `ideviceinfo`: Query lockdown properties (model, OS version, serial, battery, build).
  - `idevicepair`: Validate or trigger host-device pairing.
  - `idevicesyslog`: Stream unified system logs in real-time.
  - `idevicedebug` / `idevicecrashreport`: Collect diagnostic crash logs.
- **Licensing Consideration**:
  - `libimobiledevice` core library is licensed under **LGPLv2.1+**.
  - CLI utilities are licensed under **GPLv2+**.
  - Invoking CLI binaries out-of-process via standard subprocess boundaries preserves commercial licensing neutrality without copyleft contamination.

### 3.3 pymobiledevice3
- **Overview**: Pure Python implementation of Apple lockdown and debug services.
- **Capabilities**: Full support for iOS 10 through iOS 17+, Developer Disk Image mounting, syslog streaming, screenshot capture, and Tunneld (coredevice remote tunnel).
- **Licensing Constraint**: Licensed under **GPLv3**.
  - Direct runtime `import pymobiledevice3` inside KELVRA's Python backend would impose GPLv3 obligations onto KELVRA Device Lab.
  - Architectural Mandate: If `pymobiledevice3` is used as an optional CLI provider, it must strictly be executed through isolated subprocesses or container boundaries.

---

## 4. Automation Frameworks: WebDriverAgent & XCUITest

To evaluate automation capabilities on iOS/iPadOS, the investigation reviewed Apple's UI automation architecture:

1. **XCUITest Framework**:
   - Apple's proprietary UI test framework built into Xcode.
   - Requires an active macOS host with a registered Apple Developer Team certificate to sign and execute test runner bundles on target devices.
2. **WebDriverAgent (WDA)**:
   - Developed by Facebook / Appium.
   - An iOS application running XCUITest that exposes an HTTP REST server on the device.
   - Limitations on Windows:
     - WDA cannot be built, compiled, or code-signed directly on Windows without pre-signed binaries and developer provisioning profiles.
     - On iOS 17+, Apple transitioned device communication to `CoreDevice` with local IPv6 tunnels and strict Developer Mode constraints, heavily penalizing non-macOS hosts.

---

## 5. Architectural Conclusions & Strategic Decisions

1. **Host-Native Windows Support**:
   KELVRA Device Lab targets Windows workstations as first-class hosts. Physical iOS/iPadOS device support must therefore rely on:
   - AMDS driver detection and usbmux loopback connectivity (`127.0.0.1:27015`).
   - Lockdown pairing record verification in `%ProgramData%\Apple\Lockdown`.
   - Optional CLI toolchain integration (`libimobiledevice` or `pymobiledevice3`).
2. **Truthful Capability Reporting**:
   Device Lab must clearly differentiate between supported capabilities (inventory discovery, hardware specification inspection, trust verification, telemetry) and unsupported capabilities (live screen streaming, touch injection) on Windows.
3. **No Deceptive Emulation**:
   Device Lab will not attempt to render a simulated or fake screen streaming canvas for iOS devices when the host lacks the technical infrastructure to capture it.
