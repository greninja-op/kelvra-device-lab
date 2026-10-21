# KELVRA Bench Design Reference for Device Lab (`docs/BENCH_DESIGN_REFERENCE.md`)

## 1. Product Context & Aesthetic Direction

KELVRA Bench is the Swarm Control Room and orchestration dashboard of the KELVRA ecosystem.
Device Lab must eventually integrate or dock into KELVRA Bench. To ensure seamless visual and architectural continuity, Device Lab adopts the exact design language defined in:
- `Kelvra/kelvra-bench/DESIGN.md`
- `Kelvra/design-reference/SKILL.md`
- `Kelvra/design-reference/reference.html`

**Aesthetic Direction:** Warm editorial with utilitarian developer precision (Claude.ai-inspired warm dark charcoal, terracotta accents, hairline geometry, serif + sans + mono typography, flat status dots, zero glassmorphism, and zero neon glow).

---

## 2. Canonical Color Tokens (Verified)

Copy directly from CSS custom properties:

### Surface Layers
- `--bg-canvas`: `#262624` (Warm dark charcoal window and page background)
- `--bg-sidebar`: `#1E1E1C` (Deep matte background for rails, topbars, and cards)
- `--bg-panel`: `#1A1918` (Darkest inset container surface for drill-down views)
- `--bg-elevated`: `#2E2D2A` (Elevated card, modal, or raised row fill)
- `--bg-hover`: `#33312D` (Interactive hover fill)
- `--bg-active`: `#3A3834` (Active selection fill)

### Hairlines & Borders
- `--border-hairline`: `rgba(255, 255, 255, 0.08)` (Delicate, thin dividers; never boxy outlines)
- `--border-subtle`: `#333230` (Container edges)
- `--border-strong`: `#45433F` (Active card or input outlines)
- `--border-focus`: `#D97757` (Focus ring)

### Text Tiers
- `--text-primary`: `#F5F1EA` (Warm cream off-white, high contrast; never pure `#FFFFFF`)
- `--text-secondary`: `#A39E93` (Muted warm gray-beige)
- `--text-tertiary`: `#736F66` (Subdued timestamps, labels, and secondary metadata)
- `--text-disabled`: `#54514B`

### Brand Accent
- `--accent-coral`: `#D97757` (Authentic Kelvra terracotta brand accent)
- `--accent-coral-hover`: `#E08567`
- `--accent-coral-subtle`: `rgba(217, 119, 87, 0.14)` (14% wash for badges, pills, and active highlights)

### Semantic Status Taxonomy (Flat Dots, Never Glowing Boxes)
Status indicators must always be flat dots with accompanying text:
- `idle`: `#8A867E`
- `working` / `busy`: `#60A5FA`
- `blocked` / `warning`: `#F59E0B`
- `awaiting review`: `#A78BFA`
- `complete` / `online`: `#10B981`
- `error` / `unauthorized`: `#EF4444`

---

## 3. Typography Scale & Fonts (Verified)

- **Display & Section Titles:** `Lora`, 'Source Serif 4', Georgia, serif (weight 500, editorial character).
- **Body & Interface Labels:** `Inter`, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif (crisp legibility at 12–14px).
- **Code, Data, Telemetry, and Logcat:** `JetBrains Mono`, Consolas, monospace with `font-variant-numeric: tabular-nums` (prevents jitter during real-time updates).

### Type Hierarchy
- `text-xs` (11–12px): Timestamps, rate limits, micro badges, chip labels.
- `text-sm` (13px): Device card metadata, secondary labels, battery readings.
- `text-base` (14px): Body copy, log entries, status explanations.
- `text-md` (16px): Panel headers, device model names.
- `text-lg` (19px): Section titles.
- `text-xl` (22px): Main application heading.

---

## 4. Spacing, Geometry & Radii (Verified)

- **4px Spacing Scale:** 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px. Arbitrary non-scale values are forbidden.
- **Corner Radii:**
  - `xs`: 3px
  - `sm`: 6px (inputs, small buttons)
  - `md`: 8px (cards, action panels)
  - `lg`: 12px (screen canvas viewport, modal containers)
  - `pill`: 9999px (badges, status pills, toggles)

---

## 5. Icon Conventions & Absolute Zero-Emoji Prohibition (MANDATORY)

- **Zero Unicode Emojis:** Strictly prohibited without exception. Never insert raw Unicode emoji glyphs in code, logs, tooltips, UI, or commit messages.
- **Authentic Vector Outlines Only:** Use Lucide-style thin-stroke vector SVGs (`stroke-width: 1.8`, `currentColor`, round caps/joins).
- **Icon Sourcing:** Sourced from `ICONS-ASSETS/apps-and-dashboards/` or standard geometric Lucide vectors. Never use improvised cartoons or colored emoji symbols.

---

## 6. Motion & Canvas Interaction (Verified)

- **State-Change-Only Motion:** Elements never move or animate on their own. Transitions trigger strictly on genuine state changes (device selection, button press, panel open/close).
- **Easing Curve:** `--duration-fast: 150ms`, `--duration-normal: 260ms`, `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`.
- **Accessibility:** Must include `@media (prefers-reduced-motion: reduce)` rules freezing transitions and rendering instantaneous frames.

---

## 7. Verified vs Uncertain Design Details

| Aspect | Status | Notes |
|---|---|---|
| Palette & Token Names | VERIFIED | Directly sourced from `reference.html` and `DESIGN.md`. |
| Font Families & Weights | VERIFIED | Lora (500), Inter (400/500/600), JetBrains Mono (400/500). |
| Radius Scale | VERIFIED | 3px / 6px / 8px / 12px / 9999px. |
| Status Colors & Dots | VERIFIED | Flat dots, no box outlines or glowing neon. |
| Bench Docking Component Shape | UNCERTAIN | Bench is currently web + Tauri desktop. Eventual docking may be an embedded iframe, a native sub-view, or a proxied route (`/devices`). Kept decoupled. |
| Multi-Device Concurrency Cap | UNCERTAIN | Bench allocates agent slots (`agent_slot=2`); Device Lab concurrent streaming cap should be tuned empirically based on USB host bandwidth. |
