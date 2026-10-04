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

## 3. Architecture, Research, Security, UX & Implementation Documentation Inventory

Comprehensive engineering blueprints, research audits, security specifications, complete UX designs, and implementation records are maintained inside [`docs/`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/):
- [`docs/SCREENSHOT_CAPTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SCREENSHOT_CAPTURE.md) — Visual inspection, LANCZOS downsampling, and JPEG/PNG artifact generation pipeline.
- [`docs/RECORDING_SESSIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/RECORDING_SESSIONS.md) — Screen recording lifecycle, Android screenrecord SIGINT MOOV finalization, and disconnect recovery.
- [`docs/DEVICE_LOGGING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LOGGING.md) — Circular 2,000-entry log buffer, inline credential regex scrubbing, and TXT/JSON artifact export.
- [`docs/DEVICE_DIAGNOSTICS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_DIAGNOSTICS.md) — Unified non-fabricated telemetry aggregation: provider, stream stats, leases, battery, and error ledger.
- [`docs/AUTOMATION_ENGINE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AUTOMATION_ENGINE.md) — Sequential step runner, coordinate bounds checking, and single-runner per-device concurrency locking.
- [`docs/AUTOMATION_WORKFLOW_SCHEMA.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AUTOMATION_WORKFLOW_SCHEMA.md) — Complete declarative JSON schema and action catalogue (WAIT, TAP, SWIPE, KEY, TEXT, APP, SCREEN, ASSERT).
- [`docs/AUTOMATION_EXECUTION_SECURITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AUTOMATION_EXECUTION_SECURITY.md) — Subprocess sandboxing, shell injection escaping, package regex validation, and timeouts.
- [`docs/ARTIFACT_MANAGEMENT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ARTIFACT_MANAGEMENT.md) — Partitioned storage, catalog.json metadata index, path traversal defense, and confirmed deletion.
- [`docs/ARTIFACT_RETENTION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ARTIFACT_RETENTION.md) — 500 MB workstation storage quota with automated LRU eviction of oldest assets.
- [`docs/OBSERVABILITY_TESTING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/OBSERVABILITY_TESTING.md) — 20-test verification matrix and full 140-test project suite execution report.
- [`docs/APPLE_PLATFORM_RESEARCH.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_PLATFORM_RESEARCH.md) — Low-level usbmux protocol mechanics, AMDS, libimobiledevice, and pymobiledevice3 research.
- [`docs/IOS_IPADOS_CAPABILITY_MATRIX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/IOS_IPADOS_CAPABILITY_MATRIX.md) — 12-item capability classification matrix: Windows host vs macOS host.
- [`docs/APPLE_PROVIDER_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_PROVIDER_IMPLEMENTATION.md) — Architecture of AppleDeviceProvider, model mapper, and subprocess isolation boundary.
- [`docs/APPLE_HOST_REQUIREMENTS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_HOST_REQUIREMENTS.md) — Workstation host prerequisites, AMDS daemon setup, and diagnostics verification.
- [`docs/APPLE_DEVICE_DISCOVERY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_DEVICE_DISCOVERY.md) — Multi-tier discovery pipeline, lockdown record parsing, and UDID normalization.
- [`docs/APPLE_PAIRING_AND_TRUST.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_PAIRING_AND_TRUST.md) — Apple trust model, lockdown records, pairing challenges, and FSM mapping.
- [`docs/APPLE_STREAMING_FEASIBILITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_STREAMING_FEASIBILITY.md) — Live screen streaming feasibility audit on Windows hosts and non-deceptive inspection posture.
- [`docs/APPLE_AUTOMATION_FEASIBILITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_AUTOMATION_FEASIBILITY.md) — Automation landscape evaluation (WDA, XCUITest, Appium) and supported telemetry workflows.
- [`docs/APPLE_SECURITY_CONSIDERATIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_SECURITY_CONSIDERATIONS.md) — Apple integration threat model, lockdown key ACLs, session privacy, and GPL compliance.
- [`docs/APPLE_TESTING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/APPLE_TESTING.md) — Test architecture, mock isolation, and 17-test coverage report (120 total).
- [`docs/ANDROID_SDK_ENVIRONMENT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_SDK_ENVIRONMENT.md) — Host SDK discovery, binary resolution, missing tool guidance.
- [`docs/AVD_INVENTORY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AVD_INVENTORY.md) — Local AVD discovery, headerless INI parser, hardware config extraction.
- [`docs/AVD_CONFIGURATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AVD_CONFIGURATION.md) — Hardware profiles, CPU ABI matrix, GPU acceleration tiers.
- [`docs/AVD_CREATION_WORKFLOW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AVD_CREATION_WORKFLOW.md) — Safe creation pipeline, path traversal defense, non-interactive CLI answering.
- [`docs/EMULATOR_LIFECYCLE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/EMULATOR_LIFECYCLE.md) — Emulator lifecycle FSM, port allocation, boot tracking, and shutdown.
- [`docs/EMULATOR_RESOURCE_MANAGEMENT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/EMULATOR_RESOURCE_MANAGEMENT.md) — Workstation concurrency caps, memory limits, and disk containment.
- [`docs/EMULATOR_PROCESS_SECURITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/EMULATOR_PROCESS_SECURITY.md) — Process execution security, no shell=True, input validation, and cleanup.
- [`docs/AVD_TESTING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AVD_TESTING.md) — Test architecture, mock isolation, and 18-test coverage report (103 total).
- [`docs/ANDROID_STREAMING_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_STREAMING_IMPLEMENTATION.md) — Screen streaming pipeline, capture worker, and WebSocket delivery.
- [`docs/STREAM_SESSION_LIFECYCLE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAM_SESSION_LIFECYCLE.md) — 9-state stream lifecycle FSM, transitions, and detachment handling.
- [`docs/ANDROID_INPUT_CONTROL.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_INPUT_CONTROL.md) — Remote touch, swipe, key injection, bounds checking, and shell escaping.
- [`docs/STREAMING_PERFORMANCE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAMING_PERFORMANCE.md) — Resolution tiers (480p, 720p, 1080p), latency budgets, and backpressure.
- [`docs/STREAMING_DIAGNOSTICS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAMING_DIAGNOSTICS.md) — Real-time telemetry, zero-fabrication metrics, and HUD specs.
- [`docs/SESSION_ISOLATION_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SESSION_ISOLATION_IMPLEMENTATION.md) — Single-writer lease exclusivity, collision 409, and expiration.
- [`docs/STREAMING_TESTING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAMING_TESTING.md) — Test architecture, mock strategies, and 85-test coverage report.
- [`docs/DEVICE_DOMAIN_MODEL.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_DOMAIN_MODEL.md) — Typed device domain model and composite identifier specification.
- [`docs/DEVICE_REGISTRY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_REGISTRY.md) — Central thread-safe registry, reconciliation, and event dispatcher.
- [`docs/DEVICE_LIFECYCLE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LIFECYCLE.md) — 10-state connection lifecycle FSM and valid transitions.
- [`docs/PROVIDER_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PROVIDER_IMPLEMENTATION.md) — Abstract provider contract, health diagnostics, and mock provider.
- [`docs/ANDROID_DISCOVERY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_DISCOVERY.md) — Android ADB discovery, getprop introspection, and recovery hints.
- [`docs/DEVICE_INVENTORY_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_INVENTORY_IMPLEMENTATION.md) — Device inventory UI, filter toolbar, card/table views.
- [`docs/ANDROID_PROVIDER_IMPLEMENTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_PROVIDER_IMPLEMENTATION.md) — Architecture of AndroidDeviceProvider, properties, and lifecycle.
- [`docs/ADB_RUNTIME_MANAGEMENT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ADB_RUNTIME_MANAGEMENT.md) — Resolution priority, bounded execution, timeout cleanup, and process safety.
- [`docs/ANDROID_DEVICE_METADATA.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_DEVICE_METADATA.md) — Introspection, display geometry, property caching with TTL, and zero personal data extraction.
- [`docs/ANDROID_CONNECTION_WORKFLOW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_CONNECTION_WORKFLOW.md) — Discovery to authorization, physical RSA guidance, and disconnection cleanup.
- [`docs/ANDROID_PROVIDER_ERRORS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_PROVIDER_ERRORS.md) — Error taxonomy (ADB_UNAUTHORIZED, DEVICE_OFFLINE, timeouts) and recovery.
- [`docs/ANDROID_PROVIDER_TESTING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANDROID_PROVIDER_TESTING.md) — Test architecture, mock strategies, and 71-test coverage report.
- [`docs/TESTING_GUIDE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/TESTING_GUIDE.md) — Comprehensive test architecture and verification guide.
- [`docs/PROJECT_STATE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PROJECT_STATE.md) — Live project state, roadmap, and safety invariants.
- [`docs/IMPLEMENTATION_LOG.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/IMPLEMENTATION_LOG.md) — Detailed implementation records for Phases 7 through 12.
- [`docs/COMPONENT_IMPLEMENTATION_STATUS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/COMPONENT_IMPLEMENTATION_STATUS.md) — Catalog implementation audit mapping completed vs deferred components.
- [`docs/VALIDATION_REPORT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/VALIDATION_REPORT.md) — Phase 12 test execution report (120/120 passing) and verification findings.
- [`docs/DESIGN_SYSTEM_ADAPTATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DESIGN_SYSTEM_ADAPTATION.md) — Design system adaptation guide and Bench parity rules.
- [`docs/DESIGN_TOKENS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DESIGN_TOKENS.md) — Ground-truth tokens (surfaces, borders, text tiers, semantic dots, radii).
- [`docs/INFORMATION_ARCHITECTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INFORMATION_ARCHITECTURE.md) — Navigation structure, routing, and section hierarchy.
- [`docs/SCREEN_SPECIFICATIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SCREEN_SPECIFICATIONS.md) — Granular screen specifications for all 10 core screens.
- [`docs/DEVICE_VIEWER_UX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_VIEWER_UX.md) — Live device viewer layout, controls, input injection, and aspect locking.
- [`docs/DEVICE_INVENTORY_UX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_INVENTORY_UX.md) — Device inventory cards, dense table, filtering, and batch operations.
- [`docs/CONNECTION_WORKFLOW_UX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/CONNECTION_WORKFLOW_UX.md) — 12 connection and trust states with actionable recovery steps.
- [`docs/COMPONENT_CATALOG.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/COMPONENT_CATALOG.md) — 16 reusable Device Lab UI components and Bench reuse mapping.
- [`docs/INTERACTION_AND_ACCESSIBILITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTERACTION_AND_ACCESSIBILITY.md) — Keyboard navigation, focus rings, ARIA landmarks, and WCAG contrast.
- [`docs/RESPONSIVE_DESIGN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/RESPONSIVE_DESIGN.md) — 5 breakpoint tiers and responsive layout adaptations.
- [`docs/ANIMATION_AND_PERFORMANCE_UX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ANIMATION_AND_PERFORMANCE_UX.md) — Functional motion rules, DOM virtualization, and canvas budgets.
- [`docs/DESIGN_ACCEPTANCE_CRITERIA.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DESIGN_ACCEPTANCE_CRITERIA.md) — 15 verifiable design acceptance criteria (DS-AC-01 through DS-AC-15).
- [`docs/TRUST_BOUNDARIES.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/TRUST_BOUNDARIES.md) — 4 trust enclaves, 12 trust boundaries, and network isolation topology.
- [`docs/AUTHORIZATION_POLICY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AUTHORIZATION_POLICY.md) — Granular operation scopes, role definitions, and confirmation gates.
- [`docs/DEVICE_TRUST_AND_PAIRING.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_TRUST_AND_PAIRING.md) — Android RSA keypair pairing, iOS lockdown, and unauthorized device handling.
- [`docs/PROCESS_EXECUTION_SECURITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PROCESS_EXECUTION_SECURITY.md) — Subprocess execution rules, shell prohibition (`shell=False`), and working directory jails.
- [`docs/FILE_AND_PACKAGE_SECURITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/FILE_AND_PACKAGE_SECURITY.md) — File uploads, APK validation, path traversal defense, and automatic cleanup.
- [`docs/SESSION_ISOLATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SESSION_ISOLATION.md) — Single-writer lease exclusivity, multi-viewer streaming, and session timeouts.
- [`docs/STREAMING_SECURITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAMING_SECURITY.md) — Loopback interface binding, WebSocket origin checks, and frame isolation.
- [`docs/SECRETS_AND_CONFIGURATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECRETS_AND_CONFIGURATION.md) — Secret classification, `.env` isolation, git-ignore enforcement, and zero logging.
- [`docs/AUDIT_AND_LOGGING_POLICY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/AUDIT_AND_LOGGING_POLICY.md) — Structured audit event schema, SQLite storage, and 30-day retention policies.
- [`docs/SECURITY_THREAT_MODEL.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_THREAT_MODEL.md) — 15 STRIDE threat scenarios, mitigation specifications, and residual risks.
- [`docs/SECURITY_TEST_PLAN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_TEST_PLAN.md) — 16 automated security verification test suites.
- [`docs/SECURITY_ACCEPTANCE_CRITERIA.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_ACCEPTANCE_CRITERIA.md) — 10 verifiable MVP security gates (SEC-AC-01 through SEC-AC-10).
- [`docs/UPSTREAM_REPOSITORY_RESEARCH.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/UPSTREAM_REPOSITORY_RESEARCH.md) — Technical audit of scrcpy, STF, Appium, ADB, and pymobiledevice3.
- [`docs/UPSTREAM_COMPARISON.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/UPSTREAM_COMPARISON.md) — 11-dimension trade-off analysis matrix.
- [`docs/COMPONENT_ADOPTION_DECISIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/COMPONENT_ADOPTION_DECISIONS.md) — Component-by-component adoption recommendations.
- [`docs/LICENSING_AND_ATTRIBUTION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/LICENSING_AND_ATTRIBUTION.md) — License review, GPLv3 process boundary, and attribution requirements.
- [`docs/DEPENDENCY_POLICY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEPENDENCY_POLICY.md) — Supply chain security, version pinning, and checksum verification.
- [`docs/UPSTREAM_INTEGRATION_ROADMAP.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/UPSTREAM_INTEGRATION_ROADMAP.md) — Phased upstream component integration sequence.
- [`docs/ARCHITECTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ARCHITECTURE.md) — 8-layer system architecture and context diagram.
- [`docs/TECH_STACK_DECISIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/TECH_STACK_DECISIONS.md) — Technology evaluation, rationale, and trade-offs.
- [`docs/COMPONENT_BOUNDARIES.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/COMPONENT_BOUNDARIES.md) — Component responsibilities, inputs, outputs, and isolation.
- [`docs/RUNTIME_TOPOLOGY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/RUNTIME_TOPOLOGY.md) — Process model, Windows flags, orphan prevention, and shutdown.
- [`docs/COMMUNICATION_PROTOCOLS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/COMMUNICATION_PROTOCOLS.md) — REST endpoints, WebSocket schemas, and error envelopes.
- [`docs/DEVICE_PROVIDER_CONTRACT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_PROVIDER_CONTRACT.md) — `BaseDeviceProvider` interface and 10-state FSM.
- [`docs/STREAMING_ARCHITECTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STREAMING_ARCHITECTURE.md) — Streaming pipeline, scrcpy boundary, and 60/120 FPS targets.
- [`docs/SECURITY_ARCHITECTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_ARCHITECTURE.md) — Threat model, command allowlist, path jails, and secret redaction.
- [`docs/PERFORMANCE_ARCHITECTURE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PERFORMANCE_ARCHITECTURE.md) — Latency budgets, GPU decoding, and adaptive throttling.
- [`docs/FAILURE_AND_RECOVERY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/FAILURE_AND_RECOVERY.md) — 10 failure models, detection, cleanup, and retry policies.
- [`docs/BENCH_INTEGRATION_CONTRACT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/BENCH_INTEGRATION_CONTRACT.md) — EventBus publishing, MCP tool definitions, and workspace docking.
- [`docs/ARCHITECTURE_DECISIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ARCHITECTURE_DECISIONS.md) — ADR index (ADR-01 through ADR-12).
- [`docs/OPEN_DECISIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/OPEN_DECISIONS.md) — Trade-offs and open decision log.
- [`docs/PRODUCT_VISION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PRODUCT_VISION.md) — Executive vision, target users, and non-goals.
- [`docs/PRODUCT_REQUIREMENTS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PRODUCT_REQUIREMENTS.md) — Product specifications for Modules A through J.
- [`docs/FEATURE_CATALOG.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/FEATURE_CATALOG.md) — Granular catalog with release classifications.
- [`docs/PLATFORM_CAPABILITY_MATRIX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PLATFORM_CAPABILITY_MATRIX.md) — Rigorous matrix across Android and Apple platforms.
- [`docs/USER_ROLES_AND_PERMISSIONS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/USER_ROLES_AND_PERMISSIONS.md) — Governance, roles, and confirmation gates.
- [`docs/USER_EXPERIENCE_SPEC.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/USER_EXPERIENCE_SPEC.md) — 3-column layout, responsive behavior, and state designs.
- [`docs/MVP_SCOPE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/MVP_SCOPE.md) — Phased release boundaries (MVP, 1.x, Future, Deferred).
- [`docs/ACCEPTANCE_CRITERIA.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ACCEPTANCE_CRITERIA.md) — Objective functional, performance, and security criteria.
- [`docs/PERFORMANCE_BASELINE.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PERFORMANCE_BASELINE.md) — Measured performance baseline across startup, discovery, streaming, and I/O.
- [`docs/PERFORMANCE_OPTIMIZATION.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PERFORMANCE_OPTIMIZATION.md) — Streamer idle loop throttling, JPEG compression, and backpressure protection.
- [`docs/RELIABILITY_REVIEW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/RELIABILITY_REVIEW.md) — Failure recovery models, hardware disconnect handling, and deadlock prevention.
- [`docs/RESOURCE_LIFECYCLE_AUDIT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/RESOURCE_LIFECYCLE_AUDIT.md) — Comprehensive audit of processes, tasks, sockets, and cleanup hooks.
- [`docs/MEMORY_AND_CPU_STABILITY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/MEMORY_AND_CPU_STABILITY.md) — RSS memory stability profiles, circular bounding, and CPU benchmarks.
- [`docs/PLATFORM_COMPATIBILITY_MATRIX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PLATFORM_COMPATIBILITY_MATRIX.md) — Hardening matrix across Windows, Linux, macOS, Android, and iOS.
- [`docs/SECURITY_REGRESSION_REVIEW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_REGRESSION_REVIEW.md) — Threat audit, input validation, path traversal defense, and lease isolation.
- [`docs/ACCESSIBILITY_REVIEW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ACCESSIBILITY_REVIEW.md) — WCAG 2.1 AA compliance, keyboard navigation, and zero-emoji verification.
- [`docs/DEPENDENCY_HEALTH.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEPENDENCY_HEALTH.md) — Dependency licensing compliance, GPLv3 subprocess isolation, and CVE posture.
- [`docs/REGRESSION_TEST_PLAN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/REGRESSION_TEST_PLAN.md) — Automated regression test suite strategy covering all 155 test cases.
- [`docs/SYSTEM_ACCEPTANCE_REPORT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SYSTEM_ACCEPTANCE_REPORT.md) — Formal pass/fail audit across 34 acceptance criteria.
- [`docs/SYSTEM_VERIFICATION_MATRIX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SYSTEM_VERIFICATION_MATRIX.md) — Full requirements traceability matrix across Modules A through J.
- [`docs/END_TO_END_WORKFLOWS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/END_TO_END_WORKFLOWS.md) — Architectural specifications for the 5 core user workflows.
- [`docs/OPERATIONAL_READINESS_REVIEW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/OPERATIONAL_READINESS_REVIEW.md) — Production readiness, runbooks, and failure recovery.
- [`docs/STANDALONE_RELEASE_NOTES.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/STANDALONE_RELEASE_NOTES.md) — Official v0.1.0-standalone release notes and quick start guide.
- [`docs/INTEGRATION_READINESS_ASSESSMENT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_READINESS_ASSESSMENT.md) — Comprehensive readiness audit, acceptance criteria confirmation, and preconditions.
- [`docs/REPOSITORY_COMPATIBILITY_MATRIX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/REPOSITORY_COMPATIBILITY_MATRIX.md) — Cross-repository compatibility analysis (runtime, framework, async, ports, design tokens).
- [`docs/INTEGRATION_STRATEGY.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_STRATEGY.md) — Evaluation of 4 architectural options and rationale for Approach 4 (Hybrid Adapter).
- [`docs/INTEGRATION_CONTRACT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_CONTRACT.md) — Immutable v1.0 REST API, WebSocket streaming, and EventBus contract.
- [`docs/MODULE_OWNERSHIP_AND_BOUNDARIES.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/MODULE_OWNERSHIP_AND_BOUNDARIES.md) — Exact ownership domains and 5 cardinal boundary enforcement rules.
- [`docs/SYNCHRONIZATION_FILE_PLAN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SYNCHRONIZATION_FILE_PLAN.md) — Granular file-by-file categorization (Categories A, B, C, D) and pre-sync gates.
- [`docs/DEPENDENCY_COMPATIBILITY_REPORT.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEPENDENCY_COMPATIBILITY_REPORT.md) — Python package audit, permissive licensing, and GPLv3 boundary verification.
- [`docs/INTEGRATION_SECURITY_REVIEW.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_SECURITY_REVIEW.md) — Token translation, multi-tenant RBAC, process sandboxing, and log scrubbing.
- [`docs/FEATURE_FLAG_AND_ROLLBACK_PLAN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/FEATURE_FLAG_AND_ROLLBACK_PLAN.md) — Feature flag configuration, offline degradation, and instant rollback runbook.
- [`docs/INTEGRATION_TEST_PLAN.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_TEST_PLAN.md) — 5-tier integration verification test plan across connectivity, events, and control.
- [`docs/INTEGRATION_RISK_REGISTER.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_RISK_REGISTER.md) — Comprehensive 8-risk register, mitigation strategies, and contingencies.
- [`docs/INTEGRATION_EXECUTION_CHECKLIST.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_EXECUTION_CHECKLIST.md) — Authoritative 6-gate sequential checklist governing synchronization execution.
- [`docs/INTEGRATION_IMPLEMENTATION_STATUS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_IMPLEMENTATION_STATUS.md) — Implementation matrix and component registration report.
- [`docs/CONFIGURATION_AND_DEPENDENCY_CHANGES.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/CONFIGURATION_AND_DEPENDENCY_CHANGES.md) — Configuration variable additions and dependency verification.
- [`docs/INTEGRATION_TEST_RESULTS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/INTEGRATION_TEST_RESULTS.md) — 12/12 automated integration tests execution outcomes.
- [`docs/REGRESSION_TEST_RESULTS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/REGRESSION_TEST_RESULTS.md) — Full regression audit across Device Lab (155/155 passed) and Bench (54/54 passed).
- [`docs/SECURITY_VALIDATION_RESULTS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/SECURITY_VALIDATION_RESULTS.md) — Security boundary verification, threat mitigations, and secret redaction audit.
- [`docs/ROLLBACK_STATUS.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/ROLLBACK_STATUS.md) — Tested rollback triggers, recovery procedures, and emergency runbook.

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
