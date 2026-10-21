# KELVRA Device Lab — Product Vision

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PRODUCT_VISION.md`
- **Subsystem:** KELVRA Device Lab
- **Parent Product:** KELVRA Bench (`Kelvra/kelvra-bench/`)
- **Development Model:** Standalone-first repository and application; planned integration into KELVRA Bench
- **Status:** Phase 2 Product Requirements & Feature Definition
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. What KELVRA Device Lab Is

KELVRA Device Lab is a dedicated mobile device management, interactive teleoperation, screen streaming, telemetry inspection, and automated testing laboratory. It is engineered to bridge the physical divide between autonomous AI engineering agents (and human developers) and live mobile hardware.

Developed initially as an independent application with its own repository, local service, and control console on port `:8098`, Device Lab is designed from first principles to dock natively into KELVRA Bench as a first-class control room workspace.

---

## 2. The Problem It Solves

Multi-agent development benches and AI engineers building mobile companion applications (such as `Kelvra Mobile`) face severe operational friction:

1. **The Mobile Blind Spot:** While autonomous agents can generate Kotlin Multiplatform / Compose code, compile Gradle tasks, and produce APKs, they cannot visually inspect the running UI on physical screens, verify touch gesture responsiveness, observe hardware thermals, or validate air-gapped on-device AI models without fragmented external tools.
2. **Tool Fragmentation & Workspace Sprawl:** Human developers must manually juggle disjointed single-purpose tools: an ADB command-line terminal, a standalone floating scrcpy window, Android Studio Device Manager consuming massive host RAM, and separate raw logcat buffers.
3. **Lack of Programmatic Agent Hooks:** Commercial or open-source GUI viewers are designed for human eyes, not autonomous agent swarms. They lack structured REST/WebSocket APIs for programmatic coordinate-based touch injection, assertion-gated screenshot capture, and event publication into an agent orchestration event bus.
4. **Deceptive Emulation vs Physical Hardware Reality:** Companion features—such as hardware Keystore P-256 secure enclave keys, on-device offline SODA speech recognition, Bluetooth Low Energy peripherals, and microphone audio capture—behave fundamentally differently on emulators than on real hardware. Without physical hardware inspection, false positives easily pass unnoticed.

---

## 3. Target Users

1. **Autonomous Coding Agents (Primary Operator):** Swarm agents (Scout, Frontend, Backend, QA, Reviewer) operating in Bench worktrees that need to deploy test builds, verify UI components, and capture regression screenshots autonomously.
2. **AI Engineers & Swarm Supervisors:** Human developers overseeing multi-agent workflows who need to visually monitor test executions, inspect live device telemetry, or take over manual teleoperation when an agent requests clarification.
3. **Mobile Companion Developers:** Engineers building and testing `Kelvra Mobile` across real Android devices and emulators.

---

## 4. Why Device Lab Belongs Inside KELVRA Bench

Device Lab is not an isolated utility; it is a core operational capability of the KELVRA Bench Swarm Control Room:
- **Unified Event Bus Integration:** Test runs, device discovery events, and assertion failures seamlessly publish to the Bench EventBus (`/api/events`), enabling Bench Kanban cards to update automatically based on physical device verification.
- **Shared Design Continuity:** Adheres strictly to the KELVRA Bench Design Contract (warm dark charcoal `#262624`, `#1E1E1C`, terracotta `#D97757`, Lora, Inter, JetBrains Mono, zero emojis), ensuring visual and ergonomic continuity.
- **Tool Gateway & MCP Exposure:** Device Lab exposes device automation primitives as Model Context Protocol (MCP) tools, allowing LLM agents inside Bench to inspect, tap, swipe, and verify mobile interfaces programmatically.

---

## 5. What Makes Its Workflow Different

| Traditional Manual Workflow | KELVRA Device Lab Workflow |
|---|---|
| Run `adb devices` in terminal | Automatic real-time fleet discovery and status polling |
| Launch standalone floating `scrcpy` window | Aspect-ratio-locked viewport integrated into a unified 3-column control console |
| Open separate terminal for `adb logcat` | Real-time virtualized logcat feed with instant tag, regex, and severity filters |
| Inspect device battery via `dumpsys battery` | Live telemetry graphs showing CPU, RAM, battery, thermals, and frame rate |
| Manually tap screen or use `adb shell input` | Low-latency click-to-tap, drag-to-swipe, and physical keyboard text injection |
| Manual screenshots saved to device disk | Single-click screenshot capture and programmatic assertion check-points |
| No agent access | Structured REST/WebSocket APIs designed for autonomous agent execution |

---

## 6. What the Product Must NOT Attempt To Do (Non-Goals)

To prevent bloat and maintain architectural discipline, Device Lab explicitly declines to:
- **Replace Android Studio or Xcode as a Full IDE:** It will not provide code editing, project refactoring, or compiler toolchains.
- **Provide Universal Hardware Compatibility:** It will not promise support for obsolete OS versions (Android < API 26 or iOS < 15), jailbroken devices, or unverified custom ROMs.
- **Compete with Commercial Multi-Tenant Cloud Device Farms:** It will not attempt to manage thousands of remote cloud devices or multi-tenant billing infrastructure in MVP.
- **Bypass Operating System Security:** It will never bypass hardware Keystore isolation, biometric security, or system permission dialogs without explicit authorization.
- **Simulate iOS on Non-macOS Hosts:** It will not attempt to run iOS Simulators on Windows or Linux.

---

## 7. Graceful Degradation Principles

When certain platforms or hardware features are unavailable, Device Lab remains useful:
- **No Physical Device Attached:** Immediately highlights the option to launch or connect a headless/GUI virtual device (AVD), or inspect mock fixtures for pipeline verification.
- **Unauthorized ADB State:** Surfaces clear, actionable guidance on the device viewport instructing the developer to accept the RSA host fingerprint on the physical phone screen.
- **High Latency or Low Bandwidth:** Dynamically adapts screen streaming frame rate (throttling from 60 FPS down to 10 FPS or on-demand JPEG captures) while maintaining touch injection fidelity.
- **Restricted Platforms (iOS on Windows Host):** Honestly discloses platform boundaries. Supports usbmuxd discovery, battery telemetry, and syslog streaming where possible, while cleanly marking interactive touch injection as requiring a macOS host or deferred.

---

## 8. The Core User Journey

```
[Connect USB Cable / Launch Virtual Device]
                     │
                     ▼
[Automatic Discovery in Fleet Rail (< 2s)]
                     │
                     ▼
[Device Card Selected: Telemetry & Status Verified]
                     │
                     ▼
[Open Stage Viewport: Aspect-Ratio Screen Streamed]
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
[Manual Teleoperation]     [Autonomous Test Run]
- Click to tap             - Install APK
- Drag to swipe            - Launch package
- Type to text             - Evaluate assertions
- Live logcat stream       - Capture evidence
        │                         │
        └────────────┬────────────┘
                     ▼
[Review Execution Report & Checkpoint Screenshots]
```

1. **Connect & Discover:** The developer plugs in a physical Android phone or launches an emulator. The Fleet Rail detects the device in under 2 seconds and displays its hardware specs and status dot.
2. **Select & Inspect:** The user clicks the device. The Stage Viewport activates, rendering the screen stream with correct aspect ratio and zero distortion.
3. **Interact & Monitor:** The user clicks and drags in the viewport to control the phone, types text via keyboard, and monitors live logcat and CPU/RAM/thermal telemetry in the contextual panels.
4. **Automate & Verify:** The developer or an autonomous Bench agent dispatches a test suite (e.g. install build, launch activity, assert button visibility). Device Lab captures screenshots at each step and reports results.
