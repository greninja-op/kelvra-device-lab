# KELVRA Device Lab — Reusable Component Catalog

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/COMPONENT_CATALOG.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract & `reference.html`
- **Status:** Verified Component Catalog Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Catalog Overview & Reuse Philosophy

To maintain absolute aesthetic parity with KELVRA Bench while delivering specialized mobile teleoperation features, the component library balances **direct Bench reuse** with **purpose-built Device Lab components**.

Every component strictly enforces:
- Warm editorial styling (`#262624`, `#1E1E1C`, `#D97757`).
- Zero Unicode emojis (authentically rendered vector SVGs only).
- WCAG 2.1 AA/AAA contrast ratios and full keyboard accessibility.

---

## 2. Component Specifications

### 2.1 `DeviceCard`
- **Purpose:** Primary grid tile representing a single physical or virtual device in the inventory.
- **Classification:** Proposed New Component (specialized for hardware telemetry).
- **Bench Reuse:** Reuses Bench card base framing (`--bg-sidebar`, `--border-hairline`, `--radius-lg`).
- **Properties:**
  - `device`: `{ serial: string, model: string, platform: 'android'|'ios', is_virtual: bool, os_version: string, battery: number, is_charging: bool, thermal_c: number, status: 'online'|'idle'|'busy'|'blocked'|'offline', lease_holder?: string }`
  - `onLaunchStudio`: `(serial: string) => void`
  - `onViewDetails`: `(serial: string) => void`
- **States:** Default, Hover (`--bg-elevated`, 150ms transition), Selected (2px terracotta left accent border), Disabled (offline device, 40% opacity).
- **Accessibility:** Full keyboard focus ring (`--border-focus`), Enter key triggers `onLaunchStudio`.

### 2.2 `DeviceStatusDot`
- **Purpose:** Semantic 8px flat status indicator paired with text label.
- **Classification:** Direct Bench Pattern Reuse (`.taxonomy .tax`).
- **Properties:**
  - `state`: `'idle' | 'working' | 'blocked' | 'review' | 'complete' | 'error'`
  - `label`: `string` (e.g. "online", "busy", "unauthorized")
  - `pulse`: `boolean` (true only during active streaming or test execution)
- **Visuals:** Flat circular 8px dot using canonical color token (`--dot-idle`, `--dot-working`, `--dot-blocked`, `--dot-complete`, `--dot-error`). No glowing shadows.

### 2.3 `DevicePlatformIcon`
- **Purpose:** Authentic thin-stroke vector icon indicating device operating system and form factor.
- **Classification:** Authentic Vector Icon (from `ICONS-ASSETS/`).
- **Variants:** `android-phone`, `android-tablet`, `android-emulator`, `apple-iphone`, `apple-ipad`.
- **Properties:** `width: 20`, `height: 20`, `stroke-width: 1.8`, `color: 'currentColor'`.

### 2.4 `ConnectionBanner`
- **Purpose:** Non-blocking informational or warning banner across top of view.
- **Classification:** Direct Bench Component Reuse.
- **Properties:**
  - `variant`: `'info' | 'warning' | 'error' | 'success'`
  - `title`: `string`
  - `message`: `string`
  - `actionLabel?`: `string`
  - `onAction?`: `() => void`
- **States:** Default, Action Focused, Dismissed.

### 2.5 `DeviceViewerCanvas`
- **Purpose:** High-performance HTML5 2D canvas rendering aspect-ratio locked video stream and capturing touch inputs.
- **Classification:** Purpose-Built Device Lab Core Component.
- **Properties:**
  - `serial`: `string`
  - `streamSocketUrl`: `string`
  - `scaleMode`: `'fit' | '50%' | '75%' | '100%'`
  - `isLeaseHolder`: `boolean`
  - `onInputEvent`: `(event: InputPayload) => void`
- **States:** Loading (negotiating pipeline), Streaming (active frames), Reconnecting (overlay wash), Disconnected (empty state).
- **Accessibility:** `aria-label="Live screen stream for [device model]"`, `tabindex="0"`, keyboard event listener forwards keys when focused.

### 2.6 `ViewerToolbar`
- **Purpose:** Top action strip controlling live stream parameters and device capture.
- **Classification:** Proposed New Component.
- **Controls:** Scale selector dropdown, Orientation toggle button, Screenshot trigger, Screen record trigger, Fullscreen toggle, End Session button.
- **Height:** 44px (touch accessible).

### 2.7 `HardwareNavBar`
- **Purpose:** Emulated physical/virtual navigation buttons for Android.
- **Classification:** Proposed New Component.
- **Controls:** Back (`KEYCODE_BACK`), Home (`KEYCODE_HOME`), Recents (`KEYCODE_APP_SWITCH`), Power (`KEYCODE_POWER`), Volume Down, Volume Up.
- **Icons:** Outlined vector glyphs (1.8px stroke width). Min-touch target: 44px x 44px.

### 2.8 `SessionIndicatorPill`
- **Purpose:** Compact status badge displaying active lease ownership and countdown timer.
- **Classification:** Bench Pill Pattern Reuse (`.badge`).
- **Properties:**
  - `role`: `'Viewer' | 'Operator' | 'Developer' | 'Admin'`
  - `holder`: `string` (e.g. "You", "Agent-QA")
  - `expiresInSeconds`: `number`
  - `isExclusive`: `boolean`
- **Formatting:** Terracotta wash (`--accent-coral-subtle`) when holding exclusive lease; tabular numerals for countdown.

### 2.9 `StreamTelemetryHUD`
- **Purpose:** Discrete floating or docked chip displaying live frame rate, latency, and bitrate.
- **Classification:** Proposed New Component.
- **Formatting:** `JetBrains Mono` 12px tabular numbers (`30.0 FPS · 38ms`). Unobtrusive semi-transparent container (`rgba(30, 30, 28, 0.85)`).

### 2.10 `VirtualizedLogcatFeed`
- **Purpose:** High-velocity logcat feed with DOM row recycling, regex filtering, and severity highlighting.
- **Classification:** Adapted from Bench Terminal / Transcript Component.
- **Properties:**
  - `lines`: `LogEntry[]`
  - `severityFilter`: `'all' | 'verbose' | 'debug' | 'info' | 'warn' | 'error'`
  - `searchQuery`: `string`
  - `autoScroll`: `boolean`
- **Performance:** Renders exactly 50 physical DOM nodes; recycled on scroll.

### 2.11 `DiagnosticHealthTile`
- **Purpose:** Compact metric card showing subsystem health (ADB, WebSockets, SQLite).
- **Classification:** Direct Bench Tile Reuse (`.tile-demo`).
- **Hierarchy:** Title (Lora 16px), Value with flat status dot, secondary explanation.

### 2.12 `DeviceEmptyState`
- **Purpose:** Honest, helpful empty panel when no devices are connected or search yields zero results.
- **Classification:** Direct Bench Pattern Reuse (`.copy-block`).
- **Elements:** Headline (Lora 16px), Actionable explanation, Primary terracotta button.

---

## 3. Component Hierarchy & Composition Tree

```
DeviceLabShell
├── GlobalTopbar
│   ├── Wordmark & Breadcrumbs
│   ├── FleetStatusIndicator
│   └── SessionIndicatorPill
├── WorkspaceRouter
│   ├── OverviewView
│   │   ├── MetricTilesGrid (DiagnosticHealthTile x 4)
│   │   └── DeviceInventoryPreview
│   ├── DeviceInventoryView
│   │   ├── InventoryToolbar (Search, Filter, ViewToggle)
│   │   ├── DeviceInventoryGrid (DeviceCard x N)
│   │   └── DeviceInventoryTable
│   └── LiveDeviceViewerView
│       ├── QuickDeviceRail (DeviceListItem x N)
│       ├── CenterStage
│       │   ├── ViewerToolbar
│       │   ├── DeviceViewerCanvas (with TouchRippleOverlay & TelemetryHUD)
│       │   └── HardwareNavBar
│       └── RightContextualRail
│           ├── TabBar (Telemetry | Logcat | Automation | Settings)
│           ├── TelemetryPanel
│           ├── VirtualizedLogcatFeed
│           └── AutomationRunnerPanel
```
