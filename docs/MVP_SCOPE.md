# KELVRA Device Lab — MVP Scope & Phased Release Plan

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/MVP_SCOPE.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Authority:** KELVRA Product Scope & Roadmap
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Release Philosophy & Tier Definitions

To ensure rapid standalone validation, zero regression risks to concurrent KELVRA projects, and architectural reliability, Device Lab follows a phased release cadence:
- **`MVP` (Minimum Viable Product):** The smallest self-contained, fully functional, and useful standalone laboratory. Focuses strictly on physical and virtual Android devices over USB with zero external binary dependencies.
- **`Release 1.x`:** High-performance optimizations, declarative test runners, virtual device lifecycle managers, and initial iOS inspection.
- **`Future`:** Cross-device multi-view grids, wireless teleoperation, and macOS-hosted iOS interactive automation.
- **`Deferred`:** Monolithic distributed cloud farms and third-party SaaS integrations out of scope for local-first developer benches.

---

## 2. Minimum Viable Product (MVP) Scope

### 2.1 Included Capabilities
1. **Automated Fleet Discovery:**
   - Detects all USB-connected Android physical devices and running virtual emulators via local ADB socket (`127.0.0.1:5037`).
   - Surfaces model name, manufacturer, Android OS version, SDK API level, display resolution, and online/unauthorized status.
2. **Aspect-Ratio-Preserving Screen Viewer:**
   - Live stream rendered on HTML5 Canvas via WebSocket binary frame streaming (JPEG compression, 15–30 FPS).
   - Dynamic pillarbox/letterbox centering preventing image stretching.
3. **Interactive Mouse Teleoperation:**
   - Click-to-tap, drag-to-swipe, and scroll-wheel drag mapping with visual feedback.
4. **Hardware Navigation Controls & Text Injection:**
   - Dedicated toolbar controls for Back, Home, App Switcher, Power, Volume Up, and Volume Down.
   - Browser physical keyboard typing forwarded directly into focused Android text fields.
5. **Real-Time Virtualized Logcat Streamer:**
   - Streams Android logcat over WebSocket with ring buffer caching, tag filtering, and instant regex search.
   - Built-in secret redaction for API keys and tokens.
6. **Hardware Health & Telemetry Monitor:**
   - Live polling of CPU utilization, RAM usage, storage capacity, battery percentage, charging state, and temperature.
   - Alerts on high thermal conditions (> 42°C) or critical battery levels (< 15%).
7. **Single-Click & Programmatic Screenshot Engine:**
   - High-resolution uncompressed PNG screenshot capture with timestamped metadata.
8. **Smoke Test Runner & APK Installer:**
   - Installs APK builds, launches main activity, checks for immediate process crashes, captures proof screenshots, and logs exit status.
9. **Bench-Aligned Standalone Control Console:**
   - Complete 3-column UI built with the KELVRA Bench design contract (`#262624`, `#1E1E1C`, `#D97757`, Lora, Inter, JetBrains Mono, zero emojis).

### 2.2 Excluded from MVP (Explicit Non-Goals for Initial Release)
- No `scrcpy-server` binary injection (deferred to Release 1.x to keep MVP 100% zero-dependency).
- No headless AVD provisioning or automated emulator creation.
- No Apple iOS interactive screen control.
- No wireless ADB pairing.
- No multi-device simultaneous grid streaming.

---

## 3. Release 1.x Scope (Post-MVP Enhancements)

Following stable MVP validation:
1. **Hardware-Accelerated MediaCodec Streaming (scrcpy Adapter):**
   - High-FPS video streaming (60 FPS baseline, provisional 120 FPS target on supported hardware) with sub-45ms latency via WebCodecs H.264.
2. **Android Virtual Device (AVD) CLI Lifecycle Manager:**
   - Headless boot, snapshot restore, and clean shutdown of emulators without Android Studio GUI.
3. **Wireless ADB Discovery:**
   - mDNS pairing and wireless network connection for Android 11+ devices.
4. **Declarative UI Test Execution:**
   - Integration with Maestro YAML flows and UIAutomator element selectors.
5. **Apple iOS Hardware Discovery & Telemetry (Windows Host):**
   - USB discovery of iPhone/iPad, battery metrics, and syslog streaming via `pymobiledevice3`.

---

## 4. Future Release Scope

1. **Cross-Platform iOS Teleoperation (macOS Host):**
   - Full interactive streaming and touch injection for physical iOS devices and Simulators via WebDriverAgent.
2. **Multi-Device Studio Grid:**
   - Synchronized side-by-side teleoperation across phone, tablet, and foldable form factors.
3. **KELVRA Bench Native Docking (Phase H):**
   - Direct integration into KELVRA Bench Swarm Control Room as a native workspace pane.

---

## 5. Deferred Capabilities

1. **Commercial Multi-Tenant Cloud Device Farms:**
   - Cloud device booking, multi-tenant billing, and remote data scrubbing are out of scope.
2. **AI Vision Self-Healing Automation:**
   - Autonomous vision reasoning belongs in the KELVRA Agent runtime (`kelvra-agent`), which consumes Device Lab's REST/WebSocket APIs rather than embedding vision models inside Device Lab core.
