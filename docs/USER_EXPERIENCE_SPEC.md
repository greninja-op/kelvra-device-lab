# KELVRA Device Lab — User Experience & Interface Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/USER_EXPERIENCE_SPEC.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Design Authority:** `Kelvra/design-reference/reference.html` & `Kelvra/kelvra-bench/DESIGN.md`
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Information Architecture & Navigation Structure

The Device Lab interface is organized into a cohesive, high-density 3-column studio layout optimized for 1080p and 4K developer displays:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ KELVRA Device Lab Topbar (Host: 127.0.0.1:8098 | Active: 1 Device | Bench Status: Ready)    │
├───────────────────┬─────────────────────────────────────────┬───────────────────────────────┤
│ Left Rail         │ Center Stage: Live Device Viewport      │ Right Contextual Hub          │
│ (Width: 300px)    │ (Flex: 1, Min: 500px)                   │ (Width: 380px)                │
│                   │                                         │                               │
│ - Fleet Overview  │ [Selected Device Header Bar]            │ Tabbed Inspection Panels:     │
│ - Physical List   │ ┌─────────────────────────────────────┐ │ 1. Live Telemetry             │
│ - Virtual List    │ │ Aspect-Ratio Locked Viewport        │ │    (CPU, RAM, Battery, Temp)  │
│ - Refresh / AVD   │ │ (Touch Ripple Feedback Overlay)     │ │ 2. Virtualized Logcat Feed    │
│   Launch Triggers │ │                                     │ │    (Filter, Severity, Tag)  │
│                   │ └─────────────────────────────────────┘ │ 3. Automated Test Runner      │
│                   │ [Hardware Navigation Control Bar]       │    (APK Install, Assertions)  │
│                   │ (Back, Home, Recents, Power, Vol-, Vol+)│ 4. Device Settings & Shell    │
└───────────────────┴─────────────────────────────────────────┴───────────────────────────────┘
```

### 1.1 Column Specifications
1. **Left Navigation Rail (Fleet Hub):**
   - Fleet summary chip: Total devices, Online count, Offline/Busy count.
   - Filterable device cards listing physical phones and emulators.
   - Quick launch action: "Start Headless Emulator" or "Scan Wireless Devices".
2. **Center Stage (Live Teleoperation Viewport):**
   - Header bar displaying device model name (in Lora serif), serial, resolution, live FPS, and latency.
   - Aspect-ratio locked canvas/video viewer preserving exact physical device geometry with subtle dark charcoal pillarbox/letterbox padding (`--bg-panel`).
   - Touch interaction feedback: Semi-transparent terracotta ripple animation (`rgba(217, 119, 87, 0.4)`) on click/tap.
   - Bottom hardware control bar with authentic thin-stroke outlined vector icons.
3. **Right Contextual Rail (Inspection & Diagnostics):**
   - Tab switcher (`Telemetry`, `Logcat`, `Automation`, `Settings`) using pill active styles (`--accent-coral-subtle`).
   - High-density telemetry metrics with `JetBrains Mono` tabular numbers preventing layout jitter.
   - Virtualized logcat feed with auto-scroll lock toggle and instant regex filtering.

---

## 2. State Design & Interaction Flow

Every operational state in Device Lab is intentionally designed to be truthful, informative, and calm:

### 2.1 State: No Device Connected (Fleet Empty State)
- **Visuals:** Canvas remains dark charcoal (`--bg-canvas`). Fleet rail renders an honest, non-cluttered empty panel.
- **Copy:**
  - *Title:* "No mobile devices connected" (Lora 16px, `--text-primary`).
  - *Body:* "Connect a physical Android phone via USB with USB Debugging enabled, or boot a virtual emulator." (`--text-secondary`).
- **Action:** Primary terracotta button: "Refresh Fleet" / Secondary button: "Launch Virtual Device".

### 2.2 State: Device Unauthorized (RSA Key Prompt)
- **Visuals:** Center stage renders a prominent, non-modal status card over the dark viewport with an amber status dot (`#F59E0B`).
- **Copy:**
  - *Title:* "Device authorization required" (Lora 19px, `--text-primary`).
  - *Body:* "Device [Model / Serial] is attached but unauthorized. Please check your physical phone screen and accept the 'Allow USB debugging' prompt."
- **Behavior:** Background poller automatically detects when authorization is granted and seamlessly transitions to the live stream without requiring a manual page reload.

### 2.3 State: Device Booting / Connecting
- **Visuals:** Centered status indicator with a quiet emerald pulsing dot (`#10B981`) and subtle progress message.
- **Copy:** "Initializing stream pipeline for [Device Model]... Negotiating resolution."
- **Rule:** Never display artificial loading spinners or fake percentage bars.

### 2.4 State: Active Streaming Session
- **Visuals:** Real-time frames rendered smoothly on HTML5 Canvas.
- **Telemetry HUD:** Discrete chip in top-right corner of viewport showing live frame rate (e.g. `30.2 FPS`) and stream latency (e.g. `42ms`) in JetBrains Mono.
- **Interactivity:** Cursor dynamically shifts to precision pointer inside canvas; click events inject touch coordinates.

### 2.5 State: Device Disconnected During Active Session
- **Visuals:** Screen canvas cleanly freezes on the last valid frame with an overlay wash (`rgba(26, 25, 24, 0.75)`).
- **Copy:**
  - *Title:* "Device disconnected" (Lora 16px, `--text-primary`).
  - *Body:* "USB connection lost for [Device Serial]. Reconnect the cable to resume teleoperation."
- **Cleanup:** Background streams and sockets are immediately terminated within 500ms; telemetry counters cleanly halt.

### 2.6 State: Permission Denied / Action Blocked
- **Visuals:** Non-blocking inline banner with muted crimson border (`#EF4444`).
- **Copy:** Plain, actionable verbs explaining the limitation: e.g. "Uninstall blocked. System packages cannot be uninstalled via Device Lab."

### 2.7 State: Unsupported Platform Capability
- **Visuals:** Informational pill with neutral dot (`#8A867E`).
- **Copy:** Truthful boundary explanation: e.g. "Interactive touch teleoperation for iOS requires a macOS host. Syslog and device telemetry remain available."

---

## 3. Responsive Behavior & Visual Rhythm

- **Aspect-Ratio Resilience:** Whether streaming a tall 20:9 phone (e.g. POCO X6 Pro 1220x2712), a 4:3 tablet, or a landscape foldable, the viewport container dynamically centers the canvas with balanced gutters.
- **Compact View (Narrow Screens < 1200px):**
  - Left navigation rail collapses into a compact icon rail (64px).
  - Right contextual hub converts into a toggleable bottom drawer.
- **Reduced Motion Compliance:**
  - Honors `@media (prefers-reduced-motion: reduce)`.
  - Disables touch ripple animations and tab sliding transitions; renders state updates instantaneously.
