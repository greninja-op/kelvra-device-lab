# KELVRA Device Lab

Autonomous device testing, teleoperation, screen streaming, and mobile fleet orchestration laboratory for KELVRA Companion devices.

Part of the **KELVRA** (Kinetic Execution Layer, Verified Routing for Agents) ecosystem.
Eventual integration destination: **KELVRA Bench** (`kelvra-bench`).

Current Development Phase: **Phase 18 — Integration Verification, Regression & Stabilization (Complete — Stable & Ready for Release Preparation)**.

---

## 1. Product Capabilities

1. **Fleet Discovery & Status Engine:**
   - Real-time ADB device discovery for physical Android hardware, virtual emulators, and Wi-Fi endpoints via local socket polling (`127.0.0.1:5037`).
   - Strongly typed domain model (`Device`) enforcing composite identifiers (`<platform>:<serial>`).
   - Hardware introspection: model, manufacturer, SoC, ABI, Android OS version, SDK API level, display resolution, pixel density, battery status, thermals, and network state.
   - Deterministic 10-state lifecycle FSM (`DISCOVERED`, `UNAUTHORIZED`, `AVAILABLE`, `CONNECTING`, `CONNECTED`, `BUSY`, `UNAVAILABLE`, `DISCONNECTING`, `DISCONNECTED`, `ERROR`).
   - Safe Android ADB provider with `shell=False`, 3-5s timeouts, and read-only `getprop` caching.
   - Thread-safe `DeviceRegistry` with auto-reconciliation, disappearance detection, and real-time state change events.

2. **Android Virtual Device (AVD) Management (Phase 11):**
   - Host SDK toolchain discovery: automated resolution of `sdk_root`, `emulator`, `avdmanager`, `sdkmanager`, `adb`, and `system-images/`.
   - AVD inventory scanning: specialized headerless INI parser extracting hardware specifications, ABI, API levels, RAM, and SD card profiles.
   - Emulator lifecycle FSM (`STOPPED`, `LAUNCHING`, `BOOTING`, `RUNNING`, `STOPPING`, `ERROR`) with process supervision and crash detection.
   - Dynamic console port allocation stepping by 2 (`5554`, `5556`, etc.) with local port collision prevention.
   - Non-blocking background boot tracking loop polling `sys.boot_completed=1` and `dev.bootcomplete=1`.
   - Direct integration into `DeviceRegistry` as `DevicePlatform.ANDROID_VIRTUAL` in `AVAILABLE` state for immediate streaming in Phase 10 Studio.
   - Safe creation workflow with path traversal defense and non-interactive CLI answering.
   - Safe deletion requiring explicit confirmation query parameters and active session locking.
   - Interactive AVD Hub Web UI with environment status strip, missing tool remediation banner, card grid, and Create AVD modal.

3. **iOS & iPadOS Physical Device Integration (Phase 12):**
   - Host environment detection (`AppleEnvironmentDetector`) probing host OS, loopback TCP port 27015 (`usbmuxd`), lockdown pairing store (`%ProgramData%\Apple\Lockdown` on Windows), and detected toolchains.
   - Hardware identifier mapping (`AppleDeviceModelMapper`) mapping internal product types (`iPhone16,1` -> iPhone 15 Pro, `iPad13,16` -> iPad Air 5th gen) across 30+ hardware generations.
   - Resilient multi-tier discovery combining high-level CLI toolchains (`libimobiledevice` / `pymobiledevice3`) with native lockdown pairing record scanning.
   - Strict GPLv3 subprocess isolation ensuring external tools run out-of-process without in-process Python licensing contamination.
   - Comprehensive trust workflow mapping: passcode-locked and unconfirmed trust states map directly to `DeviceLifecycleState.UNAUTHORIZED` with actionable user recovery guidance.
   - 12-item capability classification catalog distinguishing supported, prerequisite-gated, experimental, and unavailable capabilities across Windows and macOS hosts.
   - Dedicated REST API endpoints: `/api/providers/apple/health`, `/api/providers/apple/capabilities`, `/api/devices/{id}/apple/trust`, `/api/devices/{id}/apple/pair`.
   - Truthful web interface integration: Apple Physical badges, UDIDs, "Inspect Device" trigger, and non-deceptive Device Studio Inspection Mode.

4. **Low-Latency Teleoperation & Input Injection (Phase 10):**
   - Real-time aspect-ratio-locked screen streaming via WebSockets with explicit 9-state stream lifecycle (`StreamState`).
   - Non-blocking viewer backpressure dropping stale frames $O(1)$ under network congestion.
   - Rolling 1.0-second sliding-window FPS computation without simulated or fabricated rates.
   - Single-Writer Operator Lease exclusivity (`SessionManager`) with HTTP 409 collision rejection and heartbeat renewals.
   - Remote input controls: pointer tap, swipe, long-press, hardware navigation buttons (`BACK`, `HOME`, `APP_SWITCH`, `POWER`, `VOLUME_UP`, `VOLUME_DOWN`).
   - Direct text typing injection with space-to-`%s` conversion and shell metacharacter escaping.
   - Out-of-bounds display coordinate validation against native device screen dimensions.

5. **Device Automation & Observability Subsystem (Phase 13):**
   - Declarative workflow execution engine coordinating sequential typed actions (`WAIT`, `DELAY`, `TAP`, `SWIPE`, `KEY`, `TYPE_TEXT`, `SCREENSHOT`, `LAUNCH_APP`, `STOP_APP`, `ASSERT_STATE`).
   - Single-runner per-device execution concurrency locking, step timeouts, and graceful cancellation.
   - Centralized `ArtifactManager` with directory partitioning (`screenshots/`, `recordings/`, `logs/`, `reports/`), path traversal defense, 500 MB quota with automated LRU pruning, and explicit deletion confirmation.
   - Screen recording lifecycle manager on Android Physical and AVD devices with clean `SIGINT` container finalization, and truthful rejection of iOS recording on Windows host.
   - Live logcat streaming with circular memory bounding (2,000 entries), inline Bearer/credential/token regex sanitization, level/tag/search filtering, and plaintext/JSON exports.
   - Structured `DiagnosticsService` aggregating non-fabricated multi-tier telemetry across providers, stream pipes, operator leases, and hardware sensors.
   - Complete Web UI integration: Studio screenshot & recording controls, Route 5 Automation Console, and Route 6 Live Logcat & Deep Diagnostics panels.

6. **Hardware Telemetry & Health Monitoring:**
   - Real-time tracking of CPU utilization, RAM usage, internal storage capacity, and battery temperature.
   - Fail-safe thermal (> 42°C) and critical battery (< 15%) alerts.

7. **Performance, Reliability & Engineering Hardening (Phase 14):**
   - Streamer idle loop optimization reducing background CPU from 6% to <0.5% when 0 clients are viewing.
   - Bounded memory architecture across all subsystems (`collections.deque(maxlen=2000)` logcat buffer, 500 MB disk storage quota with automatic LRU pruning).
   - Strict Windows host subprocess safety (`shell=False`, argument list passing, CRLF/LF line normalization, dynamic `.exe` resolution, process termination timeout with kill fallback).
   - Security regression defense: strict Pydantic model validation, touch coordinate bounds checks, package name regex, path traversal defense, and single-writer lease isolation.
   - 100% WCAG 2.1 AA accessibility compliance with full keyboard navigation, ARIA landmarks, visible focus rings, and reduced motion support.
   - 149-test automated regression suite passing with 100% success rate in ~65 seconds.

8. **KELVRA Bench Bridge:**
   - Bi-directional event synchronization with KELVRA Bench EventBus (`/api/events`).
   - Registration and status validation against paired device records.

---

## 2. Design System Alignment

Adheres strictly to the **KELVRA Bench Design Contract**:
- Warm editorial dark charcoal canvas (`#121210`) with deep matte cards (`#181816`, `#1E1E1C`).
- Authentic coral brand accent (`#D97757`).
- Typography: Lora (headings), Inter (interface), JetBrains Mono (metrics and logs).
- Strict Zero-Emoji Rule: 100% authentic vector SVG icons; zero raw Unicode emojis.

---

## 3. Authoritative Canonical Documentation System

All project planning, architectural specifications, verified current status, historical phase records, and forward roadmap are consolidated into the **four canonical documents** inside [`docs/`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/):

1. **[`docs/DEVICE_LAB_KNOWLEDGE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_KNOWLEDGE.md)**: The authoritative long-term technical reference. Contains the complete product vision, architectural boundaries, domain models, state machines, design system tokens, communication protocols, Apple & Android platform capabilities, security architecture, and permanent documentation governance rules.
2. **[`docs/DEVICE_LAB_STATUS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_STATUS.md)**: The verified current project baseline. Covers all 14 implemented subsystems, the 185-test passing test suite, zero-defect ledger, multi-platform launcher suite, pre-flight environment checks, and production wheel packaging.
3. **[`docs/DEVICE_LAB_CHANGELOG.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_CHANGELOG.md)**: The comprehensive development history spanning Phases 1 through 24, including historical phase objectives, test progressions, all 31 confirmed architectural decisions, and historical defect resolutions.
4. **[`docs/DEVICE_LAB_ROADMAP.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_ROADMAP.md)**: The unified forward trajectory. Maps the 3-horizon development schedule (Horizon 1 completed, Horizon 2 WebCodecs H.264 60 FPS, Horizon 3 native macOS & enterprise RBAC), open decisions ledger (DEC-01 to DEC-05), platform blockers, and the Phase 25 implementation contract.

> **Permanent Documentation Governance Rule:** In accordance with Section 14 of `DEVICE_LAB_KNOWLEDGE.md`, future implementation prompts must update these four canonical files directly. Creating ad-hoc phase or report Markdown files is strictly prohibited.
---

## 4. Getting Started

### Prerequisites
- Python 3.10+ (Verified on Python 3.13.7)
- Android SDK Platform Tools (`adb` on PATH, verified on ADB 1.0.41)
- Apple Mobile Device Support (AMDS service active on TCP `127.0.0.1:27015` or iTunes for Windows)

### Running the Server
```bash
python -m uvicorn src.server:app --port 8098 --host 127.0.0.1
```

The Web Control Console is available at `http://127.0.0.1:8098/`.

### Running Tests
```bash
pytest -q
```
