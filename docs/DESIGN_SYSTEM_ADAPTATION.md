# KELVRA Bench Design System Adaptation for Device Lab

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DESIGN_SYSTEM_ADAPTATION.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Parent Ecosystem:** KELVRA Bench (`kelvra-bench`, `:8099`)
- **Canonical Design Source:** `Kelvra/design-reference/reference.html` & `Kelvra/kelvra-bench/DESIGN.md`
- **Status:** Verified Design System Adaptation Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary & Design Vision

KELVRA Device Lab is not a generic mobile device dashboard or third-party device cloud clone (such as AWS Device Farm, BrowserStack, or Sauce Labs). It is an integral, purpose-built subsystem of the KELVRA ecosystem that provides real-time hardware telemetry, live screen teleoperation, and mobile test orchestration for autonomous AI engineers and swarm agents.

When a developer or autonomous agent opens Device Lab, it must immediately feel like an organic extension of KELVRA Bench. The aesthetic philosophy marries warm editorial elegance with utilitarian developer precision:
- **Warm Editorial Atmosphere:** Built on a foundation of warm dark charcoal canvas (`#262624`), deep matte surfaces (`#1E1E1C`), and delicate hairline dividers (`rgba(255, 255, 255, 0.08)`).
- **Singular Terracotta Accent:** The authentic KELVRA terracotta coral accent (`#D97757`) is reserved exclusively for primary interactive intent and focused states. It is never used gratuitously for glowing borders or neon backlights.
- **Typographic Hybridity:** Editorial serif titles (`Lora`) establish dignified hierarchy, crisp sans-serif interface text (`Inter`) ensures immediate legibility, and tabular monospace strings (`JetBrains Mono`) anchor live metrics, frame rates, and logcat output.
- **Honest Telemetry:** Every metric, FPS counter, and battery level reflects real, live ADB/Syslog feeds. Fabricated numbers, simulated percentages, and decorative idle animations are strictly prohibited.
- **Zero-Emoji Rule:** Status and identity are communicated via flat semantic dots (`●`) and authentic vector SVG outlines (1.8px stroke width). No raw Unicode emojis or cartoonish caricatures are permitted anywhere in the interface.

---

## 2. Adaptation Challenges & Subsystem Specialization

While KELVRA Bench primarily deals with agent swarms, terminal transcripts, and token quota gauges, Device Lab introduces several specialized interaction patterns unique to hardware teleoperation:

### 2.1 Viewport Aspect-Ratio Preservation
Mobile screens have diverse physical aspect ratios:
- Standard tall smartphones: 19.5:9 or 20:9 (e.g. 1080x2400, 1220x2712).
- Foldables and tablets: 4:3, 16:10, or 1:1.
- Landscape testing modes: 9:19.5 or 10:16.

**Adaptation Strategy:** The live viewer container utilizes an intelligent pillarbox/letterbox algorithm framed by deep matte container panels (`--bg-panel: #1A1918`). The active canvas strictly preserves device aspect ratio without stretching, pixel distortion, or window overflow.

### 2.2 High-Frequency Stream & Log Rendering
Unlike standard dashboards that update on REST intervals, Device Lab receives:
- Live video frames at 30 to 60 FPS over WebSockets.
- Logcat log feeds delivering 500 to 2,000 lines per second during app launches.

**Adaptation Strategy:** 
- The live viewer renders on HTML5 Canvas using double-buffering and `requestAnimationFrame` synchronization.
- The logcat viewer implements virtualized row recycling (DOM virtualization) maintaining a fixed pool of 50 DOM rows, preventing UI lag or garbage collection spikes.

### 2.3 Single-Writer Input Teleoperation
Physical devices are stateful single-writer targets. Multiple developers or agents can observe a stream, but only one operator may inject touch and key commands at any time.

**Adaptation Strategy:**
- The interface prominently displays lease ownership state via a compact session pill.
- When an operator holds the lease, touch ripples (`rgba(217, 119, 87, 0.40)`) provide immediate 200ms visual confirmation on click/drag.
- When in read-only observation mode, the viewport displays an unobtrusive "Observer Mode" badge, and input pointer events are safely intercepted.

---

## 3. Design Principles Checklist

Before declaring any UI layout or component ready for implementation, verify alignment against the 7 KELVRA Design Principles:

1. **Editorial Calm:** Does the interface remain quiet and legible even when a device is streaming high-velocity logs?
2. **True Hierarchy:** Is structure communicated via type scale and whitespace rather than heavy nested boxes and borders?
3. **One Primary Action:** Does each view highlight at most one terracotta (`#D97757`) action button?
4. **Honest States:** Does an unauthorized device display the exact ADB RSA prompt instruction rather than a generic "Loading..." spinner?
5. **Tabular Precision:** Are all live numbers, timestamps, and memory counters styled with `font-variant-numeric: tabular-nums` to eliminate jitter?
6. **Outlined Vector Assets:** Are all icons thin-stroke (1.8px) SVGs matching the canonical KELVRA iconography?
7. **Accessibility & Reduced Motion:** Does the layout support complete keyboard navigation, focus rings (`outline: 2px solid #D97757`), and honor `@media (prefers-reduced-motion: reduce)`?
