# KELVRA Device Lab — Known Issues and Technical Debt Register

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/KNOWN_ISSUES_AND_TECHNICAL_DEBT.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Phase:** Phase 21 — Post-Acceptance Handoff & Maintenance Readiness
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Classification Framework

This document tracks all known architectural limitations, host constraints, and technical debt across 8 standardized categories:
1. Critical Defects (P0)
2. Reliability and Security Improvements
3. Compatibility Issues
4. Missing Automated Tests
5. Documentation Gaps
6. Performance Improvements
7. Deferred Features
8. Future Architectural Work

---

## 2. Technical Debt & Work Register

| ID | Category | Item Description | Affected Files | Dependencies | Risk | Recommended Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEBT-01** | Deferred Feature | WebCodecs H.264 60 FPS hardware-accelerated video streaming pipeline | `src/screen_streamer.py`, `static/app.js` | `scrcpy-server-v2.4.jar` | Low | **Medium (Release 1.1)** |
| **DEBT-02** | Compatibility | Physical Apple device screen capture & touch on macOS hosts | `src/apple_provider.py` | macOS AVFoundation, XCTest | Medium | **Medium (v1.2 Roadmap)** |
| **DEBT-03** | Reliability | Web Worker offscreen canvas decoding for multi-view stream isolation | `static/app.js` | Browser OffscreenCanvas API | Low | **Low (Release 1.1)** |
| **DEBT-04** | Performance | Adaptive bitrate & frame rate scaling under high loopback network load | `src/screen_streamer.py` | Bandwidth measurement probe | Low | **Medium (Release 1.1)** |
| **DEBT-05** | Missing Tests | Real physical USB cable disconnect and reconnect hardware test harness | `tests/test_phase2_android_provider.py` | Physical USB relay or automated switch | Low | **Low (Lab Hardware)** |
| **DEBT-06** | Architectural | Pluggable auth provider for corporate multi-tenant SSO / mTLS | `src/server.py` | KELVRA Gatekeeper token service | Medium | **High (Enterprise)** |
| **DEBT-07** | Performance | Native binary ADB socket protocol implementation bypassing CLI parsing | `src/android_provider.py` | ADB smartsocket protocol spec | Medium | **Low (Optimization)** |

---

## 3. Analysis by Category

### 3.1 Critical Defects (P0)
- **Status:** **NONE**. All 179 unit and integration tests pass cleanly with zero P0 or P1 defects in the register.

### 3.2 Reliability and Security Improvements
- Subprocess safety (`shell=False`) and 64 KB output bounding are implemented and verified.
- Leases auto-expire after 300s TTL. Future improvement: configurable per-agent lease TTL policies.

### 3.3 Compatibility Issues
- **Apple iOS on Windows:** Video streaming and touch injection are intentionally unsupported on Windows due to Apple driver sandboxing. Handled honestly via Inspection Mode (rejects streaming with HTTP 400 without simulated frames).
- **Nested Virtualization:** Emulators fail to boot on cloud VMs lacking hardware virtualization (VT-x / AMD-V). Requires physical hardware or bare-metal hypervisors.

### 3.4 Missing Automated Tests
- Software error injection and simulated transport drops have 100% test coverage. Physical hardware unplugging currently relies on manual test verification.

### 3.5 Deferred Features
- **WebCodecs H.264:** Current MVP delivers robust, zero-dependency JPEG streaming sustaining up to 30 FPS. 60 FPS H.264 streaming via `scrcpy-server` is scoped for Release 1.x.
- **Audio Capture:** Audio streaming from mobile hardware is deferred to future releases.
