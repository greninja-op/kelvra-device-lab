# Apple Live Screen Streaming Feasibility Analysis
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Executive Feasibility Verdict

**Status on Windows Host: UNAVAILABLE**  
**Status on macOS Host: EXPERIMENTAL / RESTRICTED**

Unlike Android, where the Android Open Source Project provides native display buffers accessible via unprivileged developer tools (`scrcpy` utilizing `app_process` / `MediaProjection` APIs), Apple iOS and iPadOS enforce absolute sandboxing around the display pipeline (`SpringBoard` / `QuartzCore` / `Metal`).

There is no native `scrcpy` equivalent for Apple devices on Windows workstations.

---

## 2. Technical Evaluation of Screen Capture Techniques

### 2.1 QuickTime USB Video Class (UVC) Protocol
- **Mechanism**: On macOS, Apple devices can register as native CoreMedia / AVFoundation video capture inputs when connected via Lightning/USB-C (the protocol behind QuickTime Screen Recording).
- **Feasibility on Windows**:
  - The QuickTime screen capture protocol requires proprietary USB descriptor handshakes and Apple-signed digital certificates not exposed by Windows generic UVC drivers.
  - Open-source implementations such as `quicktime-video-hack` or `scrcpy-ios` are unmaintained, prone to severe kernel panics, and do not compile reliably on Windows.

### 2.2 WebDriverAgent (WDA) Screenshot Polling Loop
- **Mechanism**: WebDriverAgent captures the active framebuffer using private XCUITest APIs (`XCUIScreen.main.screenshot()`) and encodes frames to JPEG over an HTTP loop.
- **Feasibility on Windows**:
  - WDA requires a running macOS host to compile, code-sign, and provision the test bundle onto the physical iOS device.
  - Performance is bottlenecked at 3 to 8 FPS with 400ms+ latency, rendering interactive 60/120 FPS teleoperation impossible.
  - Heavy CPU and thermal throttling on the device causes thermal crashes during sustained sessions.

### 2.3 Apple Developer Disk Image (DDI) Screenshot Service
- **Mechanism**: Mounting the Developer Disk Image exposes the lockdown service `com.apple.screenshotr`.
- **Feasibility on Windows**:
  - Allows capturing single static PNG/TIFF frames.
  - Capturing a single frame takes between 800ms and 2.5s per frame.
  - Unusable for real-time continuous video streaming.
  - Beginning with iOS 17, Apple replaced standard DDI mounting with `CoreDevice` / `RemotePairing`, requiring secure IPv6 tunnels and macOS Xcode 15+ pairing services.

### 2.4 AirPlay Mirroring Emulation
- **Mechanism**: Running a local AirPlay server (e.g. `UxPlay`, `AirServer`) and instructing the user to initiate screen mirroring from iOS Control Center.
- **Feasibility on Windows**:
  - Requires Bonjour / mDNS network discovery and unmanaged Wi-Fi network routing.
  - Requires continuous user intervention on the physical device to re-initiate mirroring.
  - AirPlay streams incorporate HDCP encryption for protected media, causing blackouts.
  - Does not provide any mechanism for reverse touch input or keystroke control.

---

## 3. Product & Design Contract

In accordance with KELVRA Device Lab's core design principles:
1. **Zero Deceptive UI**: Device Lab will NEVER fabricate a mock video player, static simulated canvas, or faux streaming feed for an Apple device on Windows.
2. **Transparent Inspection Mode**: When an operator opens an Apple device in Device Studio:
   - The stream toggle is explicitly disabled.
   - The canvas displays a crisp, architectural diagnostic banner:
     *"Apple Device Inspection Mode: Live screen streaming and remote touch injection are not supported on Windows host environments. Hardware metadata and lockdown trust verification are active."*
   - Real-time hardware specifications, UDID, and trust state are displayed truthfully.
