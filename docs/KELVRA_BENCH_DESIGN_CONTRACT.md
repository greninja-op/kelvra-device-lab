# KELVRA Bench Design Contract for KELVRA Device Lab

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/KELVRA_BENCH_DESIGN_CONTRACT.md`
- **Target Subsystem:** KELVRA Device Lab
- **Host Integration Destination:** KELVRA Bench (`Kelvra/kelvra-bench/`)
- **Authority Sources:**
  - `Kelvra/kelvra-bench/DESIGN.md`
  - `Kelvra/design-reference/SKILL.md`
  - `Kelvra/design-reference/reference.html` (Canonical visual truth)
  - `DesignSoul/SKILL.md`
- **Status:** Verified Design Contract & Standalone Isolation Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Verified Design Tokens

All visual surfaces in KELVRA Device Lab must use the frozen design tokens established by KELVRA Bench. Below are the verified ground-truth values extracted from `Kelvra/design-reference/reference.html` and `Kelvra/kelvra-bench/DESIGN.md`.

### 1.1 Surfaces and Backgrounds
- `--bg-canvas`: `#262624` (Warm dark charcoal base; window background, root canvas)
- `--bg-sidebar`: `#1E1E1C` (Deep matte surface for navigation rails, topbars, device list column, card headers)
- `--bg-panel`: `#1A1918` (Darkest inset container surface for drill-down panes, logcat viewers, telemetry graphs)
- `--bg-elevated`: `#2E2D2A` (Elevated card, modal backdrop, hover card state, raised rows)
- `--bg-hover`: `#33312D` (Interactive button and row hover fill)
- `--bg-active`: `#3A3834` (Active selection fill, selected device list item)

### 1.2 Borders and Dividers
- `--border-hairline`: `rgba(255, 255, 255, 0.08)` (Delicate hairline divider between sections; never a heavy box outline)
- `--border-subtle`: `#333230` (Container borders, structural framing)
- `--border-strong`: `#45433F` (Active card framing, input field borders)
- `--border-focus`: `#D97757` (Keyboard focus ring, active interactive element halo)

### 1.3 Text Tiers
- `--text-primary`: `#F5F1EA` (Warm cream off-white, high contrast; never `#FFFFFF`)
- `--text-secondary`: `#A39E93` (Muted warm gray-beige; subtitles, labels, metadata)
- `--text-tertiary`: `#736F66` (Subdued metadata, timestamps, non-interactive tags)
- `--text-disabled`: `#54514B` (Disabled controls, unavailable states)

### 1.4 Brand Accent (Terracotta / Coral)
- `--accent-coral`: `#D97757` (Authentic KELVRA terracotta brand accent)
- `--accent-coral-hover`: `#E08567` (Hover state on primary actions)
- `--accent-coral-subtle`: `rgba(217, 119, 87, 0.14)` (14% opacity wash for active chips, pills, selected tabs)

### 1.5 Semantic Status Taxonomy
Status indicators must always use flat dots paired with text labels. They must never use raw Unicode emojis, glowing neon effects, or colored box outlines.
- `idle`: `#8A867E` (Device connected, idle)
- `working` / `busy`: `#60A5FA` (Screen streaming active, test suite executing)
- `blocked` / `warning`: `#F59E0B` (ADB unauthorized, battery low, temperature high)
- `awaiting review`: `#A78BFA` (Automation paused, manual verification requested)
- `complete` / `online`: `#10B981` (Device online, test passed)
- `error` / `offline`: `#EF4444` (Device disconnected, process crash, test failed)

### 1.6 Radii and Geometry
- `radius-xs`: `3px` (Micro chips, inline tags)
- `radius-sm`: `6px` (Input boxes, compact icon buttons)
- `radius-md`: `8px` (Standard cards, modal containers, action toolbars)
- `radius-lg`: `12px` (Device viewport container, modal dialogs)
- `radius-pill`: `9999px` (Status badges, toggle pills, mode chips)

---

## 2. Typography

The typography follows KELVRA Bench's editorial-developer hybrid hierarchy:

- **Display & Section Titles:** `Lora`, 'Source Serif 4', Georgia, serif (weight 500, editorial character). Used for workspace headings, device model names in primary headers, and modal titles.
- **Interface Labels & Body:** `Inter`, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif (crisp legibility). Used for navigation, button labels, settings, and descriptions.
- **Code, Stream Telemetry, and Logcat:** `JetBrains Mono`, Consolas, monospace with `font-variant-numeric: tabular-nums` (prevents jitter during live frame rate, latency, and log streaming updates).

### Type Scale
- `text-xs`: 0.75rem (12px) - Timestamps, FPS counter, stream latency, bitrate badges.
- `text-sm`: 0.8125rem (13px) - Device list metadata, secondary attributes, session tags.
- `text-base`: 0.875rem (14px) - Body copy, standard UI controls, log text.
- `text-md`: 1.0rem (16px) - Section headers, card titles.
- `text-lg`: 1.1875rem (19px) - Subsystem header, device modal titles.
- `text-xl`: 1.375rem (22px) - Primary workspace heading.

---

## 3. Layout Conventions

### 3.1 Three-Column Studio Workspace
Device Lab adopts KELVRA Bench's structured multi-column workspace pattern:
1. **Left Rail / Fleet Column (Width: 280px - 320px):**
   - Fleet summary counter (Total, Online, Busy, Offline).
   - Device inventory list with model name, serial, platform badge (Android/iOS, Physical/Virtual), and connection status dot.
   - Quick action triggers: Refresh fleet, Launch emulator, Pair wireless device.
2. **Center Stage / Device Viewport (Flex: 1, Min-width: 480px):**
   - Device header bar: Selected device identity, live resolution, orientation toggle, zoom/scale selector, stream quality indicator.
   - Interactive viewport: Aspect-ratio locked canvas/video container framed with `--bg-panel` and `--border-hairline`.
   - Interaction overlay: Remote touch input mapping, gesture indicators, hardware button bar (Back, Home, App Switcher, Power, Volume).
3. **Right Contextual Rail / Diagnostic & Control Hub (Width: 340px - 400px):**
   - Tabbed panels:
     - *Telemetry:* Live CPU, RAM, battery, thermal metrics, frame rate, latency.
     - *Logcat / Console:* Real-time searchable log stream with log-level filters (V/D/I/W/E/F).
     - *Automation / Test Runner:* Multi-step assertion scripts, screenshot capture, APK/IPA install drop-zone.
     - *Device Settings:* ADB shell commands, proxy settings, language/locale, display density.

### 3.2 Spacing Grid
Strictly follows the 4px base scale: 4px (`space-1`), 8px (`space-2`), 12px (`space-3`), 16px (`space-4`), 20px (`space-5`), 24px (`space-6`), 32px (`space-8`), 40px (`space-10`). Non-scale arbitrary pixel margins are prohibited.

---

## 4. Component Behavior

### 4.1 Device Inventory Card
- **Resting State:** Surface `--bg-sidebar`, hairline border, neutral text `--text-secondary`.
- **Hover State:** Surface `--bg-elevated`, smooth transition (150ms), no scale transform.
- **Selected / Active State:** Background `--bg-active`, left border accent 2px `--accent-coral`, text `--text-primary`.
- **Status Dot:** 8px solid circular dot with pulse animation only when actively streaming or running tests.

### 4.2 Stream Viewport
- **Black Bar Prevention:** Viewport dynamically computes letterbox/pillarbox margins inside the container to preserve exact device display aspect ratio without stretching.
- **Interaction Feedback:** Touch gestures render subtle terracotta ripple circles (`rgba(217, 119, 87, 0.4)`) fading out in 200ms.
- **Offline / Disconnected Overlay:** When the device is offline or disconnected, render an honest empty state with `--text-secondary` and a reconnect trigger, never simulated or stale frozen screen frames.

### 4.3 Logcat & Diagnostics Feed
- **Virtual Scrolling:** High-frequency log streams use virtualized row rendering to prevent DOM bloat during high-velocity logging (1,000+ lines/sec).
- **Auto-Scroll Behavior:** Follows stream bottom by default; user upward scroll automatically suspends auto-scroll with a visible "Scroll to bottom" pill.
- **Log Level Color Coding:**
  - Verbose: `--text-tertiary` (`#736F66`)
  - Debug: `--text-secondary` (`#A39E93`)
  - Info: `--text-primary` (`#F5F1EA`)
  - Warning: `#F59E0B`
  - Error: `#EF4444`

---

## 5. Interaction Patterns

### 5.1 Mouse & Keyboard Mapping
- **Left Click:** Injected as touch down, move, and up at normalized coordinates `(x / width, y / height)`.
- **Click and Drag:** Injected as smooth touch swipe sequence.
- **Right Click:** Injected as Android system BACK button.
- **Middle Click:** Injected as Android system HOME button.
- **Typing:** Text focus in viewport transmits character sequences or raw key events via ADB `input text` or IME protocol.

### 5.2 Motion Rules
- All transitions use `--duration-fast: 150ms` or `--duration-normal: 260ms` with `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`.
- Animations trigger strictly upon state changes; decorative looping idle animations are forbidden.
- Honors `@media (prefers-reduced-motion: reduce)` by immediately rendering final states without transitions.

---

## 6. Relevant Existing UI References

The design contract is directly referenced from:
1. `Kelvra/kelvra-bench/DESIGN.md`: Primary design guidelines, color system, and typography.
2. `Kelvra/design-reference/reference.html`: Executable token layer rendering every swatch, typography sample, and component style.
3. `Kelvra/design-reference/SKILL.md`: Mandatory operational rules governing Kelvra UI surfaces.
4. `Kelvra/kelvra-space/static/`: Concrete production implementations of telemetry cards, status grids, and command bars.

---

## 7. Components That May Eventually Be Reused

When Device Lab is integrated into KELVRA Bench (Phase H), the following components can be unified:
1. **Bench Topbar & Header:** Navigation breadcrumb and ecosystem status pills.
2. **Bench EventBus Bridge:** Event publishing to `/api/events` for swarm task coordination.
3. **Bench Modal Framework:** Unified modal dialogs for settings, device details, and pairing wizards.
4. **Bench Notification / Toast Component:** Unified non-intrusive status alerts.
5. **Bench Tool Gateway Integration:** Exposing device automation primitives as MCP tools to Bench agents.

---

## 8. Components That Must Remain Independent for Standalone Development

During standalone development (Phases A through G), the following components must remain fully self-contained inside `Kelvra/KELVRA Device Lab/`:
1. **Standalone Application Shell:** Dedicated HTML/CSS/JS shell running on port `:8098`.
2. **WebSocket Screen Streamer:** Direct binary WebSocket stream between browser canvas and ADB/scrcpy backend.
3. **Independent Device Session Manager:** State management tracking active device sessions, input locks, and telemetry buffers.
4. **Local REST API Server:** FastAPI backend on `:8098` hosting device endpoints independently from Bench (:8099).
5. **Standalone Test Runner UI:** Interactive runner for automated mobile verification suites.

---

## 9. Unresolved Design Decisions

The following design decisions are documented as unresolved pending further empirical testing and user feedback:

1. **Streaming Transport in Bench Context:**
   - *Standalone Implementation:* Binary WebSocket frame streaming (JPEG/H.264).
   - *Future Bench Question:* When embedded in Bench, should Device Lab stream directly via its own WebSocket port or proxy through Bench's ASGI server?
   - *Resolution Plan:* Keep direct WebSocket communication isolated on `:8098` during standalone development; assess Bench proxy overhead during Phase G.
2. **Multi-Device Concurrency Cap:**
   - USB host controller bandwidth on developer workstations limits simultaneous high-framerate video feeds.
   - *Standalone Baseline:* Default to 1 active high-FPS stream with multiple low-rate thumbnail previews.
3. **Touch Latency Optimization:**
   - Evaluating ADB shell `input tap` (~120ms latency) versus persistent scrcpy control socket (~15ms latency).
   - *Resolution Plan:* Implement adapter pattern supporting both mechanisms.
