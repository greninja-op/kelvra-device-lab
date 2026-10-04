# KELVRA Device Lab — Responsive Behavior & Layout Adaptation

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/RESPONSIVE_DESIGN.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract
- **Status:** Verified Responsive Design Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Desktop-First Philosophy

KELVRA Device Lab is primarily an engineering studio and swarm command console. While responsive across screen sizes, it is **desktop-first**—optimized for developer workstations, high-DPI laptop screens, and 4K multi-window monitors rather than consumer mobile browsers.

The layout gracefully adapts without breaking the continuous teleoperation canvas or causing layout thrashing.

---

## 2. Breakpoint Matrix & Layout Tiers

| Breakpoint Tier | Viewport Width | Studio Layout Strategy | Left Rail (Fleet) | Center Stage (Viewer) | Right Rail (Context) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1: 4K / Ultrawide** | `>= 1920px` | 3-Column Studio (Expanded) | 340px fixed | Flex 1 (Wide canvas) | 440px fixed (Dual tab panes) |
| **Tier 2: Standard Desktop** | `1440px - 1919px` | 3-Column Studio (Standard) | 300px fixed | Flex 1 | 380px fixed |
| **Tier 3: Small Laptop** | `1200px - 1439px` | 3-Column Studio (Compact) | 260px fixed | Flex 1 | 340px fixed |
| **Tier 4: Narrow / Split View** | `1024px - 1199px` | 2-Column Studio (Drawer) | Collapsed (64px icon rail) | Flex 1 | 340px (or bottom drawer) |
| **Tier 5: Minimum Usable** | `768px - 1023px` | Single-Column Stack | Collapsed into top menu | Flex 1 (Full width) | Bottom slide-over drawer |
| **Tier 6: Unsupported** | `< 768px` | Minimal Fallback Banner | N/A | Informational notice | "Device Lab requires at least 768px width" |

---

## 3. Detailed Component Adaptations

### 3.1 Left Fleet Navigation Rail
- **Expanded (>= 1200px):** Full card list showing device model name, serial, connection type, and status dot.
- **Collapsed (1024px - 1199px):** Auto-collapses to a 64px icon rail. Shows platform icon with status dot overlay; hovering an item reveals a tooltip with full model name and serial.
- **Drawer (< 1024px):** Fully hidden behind a "Fleet" toggle button in the topbar; slides out as a modal drawer from the left.

### 3.2 Center Stage Device Viewport
- **Continuous Scaling:** The viewing canvas never wraps or scrolls horizontally. The letterboxing/pillarboxing algorithm continuously recomputes available container width and height.
- **Orientation Responsiveness:** In landscape phone testing, the center stage claims horizontal flex space while preserving the phone's 16:9 or 20:9 ratio.
- **Hardware Navigation Bar:** At narrow widths (< 1024px), button padding compacts from 16px to 10px while maintaining the 44px min-touch hit box.

### 3.3 Right Contextual Rail (Inspection & Diagnostics)
- **Standard (>= 1200px):** Fixed right sidebar with tab selector at the top.
- **Narrow (1024px - 1199px):** Can be toggled open/closed via a topbar "Inspect" icon button. When closed, center stage expands to fill the entire remaining width.
- **Mobile / Split View (< 1024px):** Transforms into a bottom drawer with drag handle. Dragging upwards expands the logcat or telemetry pane over the lower half of the device screen.

### 3.4 Device Inventory Grid Adaptation
- **>= 1600px:** 4 cards per row.
- **1200px - 1599px:** 3 cards per row.
- **900px - 1199px:** 2 cards per row.
- **< 900px:** 1 card per row (full-width stacked list).

---

## 4. Modal Dialogs & Overflow Handling

- **Modal Sizing:** Modals (`max-width: 600px`, `width: 90%`) are centered with `position: fixed`.
- **Vertical Overflow:** Modal body containers enforce `max-height: 80vh; overflow-y: auto;` with custom thin dark scrollbars.
- **Body Scroll Lock:** Opening any modal or mobile drawer sets `document.body.style.overflow = 'hidden'` to prevent background document scrolling.
- **Minimum Window Constraint:** Device Lab specifies a hard CSS constraint:
  ```css
  body {
    min-width: 768px;
    min-height: 600px;
  }
  ```
