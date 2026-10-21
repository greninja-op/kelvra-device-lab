# KELVRA Device Lab — Known Limitations & Host Constraints

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/KNOWN_LIMITATIONS.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Apple iOS / iPadOS on Windows Host

### 1.1 Screen Streaming & Mirroring
- **Limitation:** Live screen streaming and video capture for iOS devices are unsupported on Windows host environments.
- **Root Cause:** iOS does not expose an unauthenticated video frame server over USB on Windows. Native streaming requires macOS host frameworks (AVFoundation / QuickTime screen capture protocol) or a jailbroken on-device daemon.
- **Handling in v1.0.0:** Handled honestly via "Inspection Mode". REST/WebSocket requests for iOS streaming return HTTP 400 Bad Request with an explanation. Hardware metadata, battery health, and pairing state remain fully functional.

### 1.2 Touch & Gesture Injection
- **Limitation:** Remote touch injection and physical keyboard typing into iOS devices are unsupported on Windows hosts.
- **Root Cause:** Apple requires WebDriverAgent / XCTest runner signing via Xcode on macOS to inject synthetic touch events into UIKit/SwiftUI window hierarchies.
- **Handling in v1.0.0:** Rejects touch injection with HTTP 400 without simulated or fake touch indications.

---

## 2. Android Virtual Devices (AVD)

### 2.1 Host Virtualization Requirement
- **Limitation:** AVD emulation requires hardware virtualization support (Intel VT-x / AMD-V / Windows Hypervisor Platform / KVM on Linux).
- **Behavior:** In environments without hardware virtualization (e.g., nested cloud VMs), emulators will fail to boot or experience severe latency.
- **Remediation:** Physical Android devices or headless cloud device farms should be used when hardware virtualization is unavailable.

### 2.2 System Image Installation
- **Limitation:** KELVRA Device Lab automates the execution and configuration of AVDs, but does not bundle multi-gigabyte Android system images.
- **Prerequisite:** Users must install desired system images via `sdkmanager "system-images;android-XX;google_apis;x86_64"` prior to creating new AVDs.

---

## 3. Physical Android Device Constraints

### 3.1 Screen Recording Duration
- **Limitation:** Android's internal `screenrecord` binary enforces a hard 3-minute (180s) maximum capture duration per invocation.
- **Handling in v1.0.0:** The `RecordingManager` enforces timeouts and cleanly finalizes the MP4 container upon reaching the limit. Longer captures require sequential segments.

### 3.2 DRM-Protected Media Playback
- **Limitation:** DRM-protected screens (e.g., Widevine L1 content in protected apps) produce black frames during screen streaming.
- **Root Cause:** Native Android hardware security policy suppresses framebuffer reads on secure surfaces.
- **Handling in v1.0.0:** Standard Android security behavior; device returns blank frames for protected windows while non-protected interfaces stream normally.
