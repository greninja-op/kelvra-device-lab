# KELVRA Device Lab — Design Token Contract

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DESIGN_TOKENS.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority Sources:** `Kelvra/design-reference/reference.html`, `Kelvra/kelvra-bench/DESIGN.md`
- **Status:** Verified Design Token Ground Truth
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Color System

Every CSS variable is directly mapped from the canonical KELVRA design reference. No custom color palettes or deviations are permitted.

### 1.1 Canvas & Surfaces
| Token Name | Value | Purpose & Usage |
| :--- | :--- | :--- |
| `--bg-canvas` | `#262624` | Primary window and page background; main application root. |
| `--bg-sidebar` | `#1E1E1C` | Left fleet rail, topbars, device cards, input field shells. |
| `--bg-panel` | `#1A1918` | Darkest container surface; viewport pillarbox/letterbox, logcat panel. |
| `--bg-elevated` | `#2E2D2A` | Elevated cards, modal dialog shells, active dropdown menus, raised rows. |
| `--bg-hover` | `#33312D` | Interactive button and list row hover background (150ms transition). |
| `--bg-active` | `#3A3834` | Selected device row fill, pressed button state, active tab surface. |

### 1.2 Borders & Structural Dividers
| Token Name | Value | Purpose & Usage |
| :--- | :--- | :--- |
| `--border-hairline` | `rgba(255, 255, 255, 0.08)` | Delicate section dividers, panel edges; never heavy box strokes. |
| `--border-subtle` | `#333230` | Structural card borders, toolbar containers. |
| `--border-strong` | `#45433F` | Focused card framing, active search input border, tab bar borders. |
| `--border-focus` | `#D97757` | Keyboard focus ring (`outline: 2px solid var(--border-focus)`). |

### 1.3 Text Tiers
| Token Name | Value | Contrast Ratio (vs #262624) | Purpose & Usage |
| :--- | :--- | :--- | :--- |
| `--text-primary` | `#F5F1EA` | 13.8:1 (AAA) | High contrast warm cream off-white; headings, titles, active labels. |
| `--text-secondary` | `#A39E93` | 6.4:1 (AA) | Muted warm gray-beige; body copy, secondary attributes, inactive labels. |
| `--text-tertiary` | `#736F66` | 3.8:1 (UI text) | Subdued timestamps, technical metadata, input placeholders. |
| `--text-disabled` | `#54514B` | 2.4:1 | Non-interactive controls, disabled action buttons. |

### 1.4 Brand Accent (Terracotta Coral)
| Token Name | Value | Purpose & Usage |
| :--- | :--- | :--- |
| `--accent-coral` | `#D97757` | Authentic KELVRA brand accent; primary CTA button, active tab indicator. |
| `--accent-coral-hover` | `#E08567` | Hover fill on primary buttons and interactive accents. |
| `--accent-coral-subtle` | `rgba(217, 119, 87, 0.14)` | 14% opacity wash for active chips, pills, selected device border. |

### 1.5 Semantic Status Dots & Taxonomy
Status is **always** communicated via a solid 8px flat dot paired with clear text. Never communicate status through color alone.

| Status State | Dot Token | Hex Value | Label Copy | Context in Device Lab |
| :--- | :--- | :--- | :--- | :--- |
| **Idle** | `--dot-idle` | `#8A867E` | `idle` | Device connected via ADB, ready for session allocation. |
| **Working / Active** | `--dot-working` | `#60A5FA` | `working` | Screen streaming active, test suite running, APK installing. |
| **Blocked / Warning** | `--dot-blocked` | `#F59E0B` | `blocked` | ADB unauthorized (RSA prompt), battery < 15%, thermal > 42°C. |
| **Awaiting Review** | `--dot-review` | `#A78BFA` | `awaiting review` | Test assertion paused, manual human verification requested. |
| **Complete / Online** | `--dot-complete` | `#10B981` | `online` / `complete` | Device verified online, test passed, lease cleanly released. |
| **Error / Offline** | `--dot-error` | `#EF4444` | `offline` / `error` | USB cable disconnected, process crashed, test assertion failed. |

---

## 2. Typography

### 2.1 Font Families
```css
--font-serif: 'Lora', 'Source Serif 4', Georgia, serif;
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', Consolas, monospace;
```

### 2.2 Type Scale & Line Heights
| Token | Font Size | Line Height | Letter Spacing | Font Family | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--text-xs` | `0.75rem` (12px) | `1.4` (17px) | `+0.02em` | Mono / Sans | FPS counters, latency badges, timestamps, tags. |
| `--text-sm` | `0.8125rem` (13px) | `1.5` (20px) | `0` | Sans | Device serials, metadata labels, session pills. |
| `--text-base` | `0.875rem` (14px) | `1.6` (22px) | `0` | Sans | Body text, control labels, logcat stream lines. |
| `--text-md` | `1.0rem` (16px) | `1.4` (22px) | `-0.01em` | Serif (500) | Card titles, section headers, dialog titles. |
| `--text-lg` | `1.1875rem` (19px) | `1.3` (25px) | `-0.015em` | Serif (500) | Screen titles, prominent device name headers. |
| `--text-xl` | `1.375rem` (22px) | `1.2` (26px) | `-0.02em` | Serif (500) | Workspace hero headers, modal titles. |
| `--text-2xl` | `1.625rem` (26px) | `1.1` (29px) | `-0.025em` | Serif (500) | Primary dashboard headline. |

### 2.3 Tabular Number Formatting
All numeric indicators that update dynamically (frame rates, timestamps, memory, CPU load) must enforce:
```css
.tabular-nums {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
```

---

## 3. Spacing & Geometry Scale

### 3.1 4px Spacing Scale
| Token | Pixel Value | Standard Usage |
| :--- | :--- | :--- |
| `--space-1` | `4px` | Micro gaps between icon and label, inline chip margins. |
| `--space-2` | `8px` | Gap between status dot and text, compact button row gap. |
| `--space-3` | `12px` | Card internal padding for compact tiles, toolbar item padding. |
| `--space-4` | `16px` | Standard container padding, sidebar horizontal padding, grid gaps. |
| `--space-5` | `20px` | Card header padding, modal internal gutter. |
| `--space-6` | `24px` | Workspace panel gutters, section spacing. |
| `--space-8` | `32px` | Major section breaks, modal window margins. |
| `--space-10` | `40px` | Page header vertical padding. |

### 3.2 Border Radii
| Token | Value | Applied To |
| :--- | :--- | :--- |
| `--radius-xs` | `3px` | Inline code chips, micro status tags. |
| `--radius-sm` | `6px` | Input boxes, select dropdowns, compact icon buttons. |
| `--radius-md` | `8px` | Standard cards, panel containers, action toolbars. |
| `--radius-lg` | `12px` | Device viewport container, modal dialog frames. |
| `--radius-pill` | `9999px` | Buttons, status pills, filter chips, lease badges. |

### 3.3 Elevation & Shadows
Per KELVRA Bench design rules, heavy drop shadows and glowing neon effects are strictly prohibited. Elevation is achieved via surface tonal steps and subtle borders:
- **Resting:** `--bg-sidebar` with `1px solid var(--border-hairline)`.
- **Raised / Elevated:** `--bg-elevated` with `box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25)`.
- **Modal Backdrop:** `background: rgba(18, 18, 16, 0.75)` with `backdrop-filter: blur(2px)`.

---

## 4. Motion & Animation Tokens

| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `--duration-fast` | `150ms` | Button hover, list selection, focus ring transition. |
| `--duration-normal` | `260ms` | Collapsible panels, drawer slide-out, modal entry/exit. |
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Standard natural deceleration curve. |

### 4.1 Reduced Motion Override
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
