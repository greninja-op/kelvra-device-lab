# Design System — KELVRA Device Lab

## Product Context
- **What this is**: KELVRA Device Lab Control Room & Fleet Management Console.
- **Who it's for**: Autonomous AI engineers, test orchestrators, and developers managing physical and virtual companion devices.
- **Space/industry**: Mobile hardware automation, ADB teleoperation, remote test labs, device health observability.
- **Integration Destination**: Docks directly into KELVRA Bench (`kelvra-bench`).

## Aesthetic Direction
- **Direction**: Warm editorial with utilitarian developer precision, adhering strictly to KELVRA Bench's design contract.
- **Decoration level**: Intentional, minimal, zero-slop. Hairline geometry, matte panels, quiet status dots.
- **Mood**: Calm, highly legible, professional device control room.
- **Zero-Emoji Prohibition**: Strictly enforced. Never use raw unicode emojis anywhere. Authentic SVG icons only.

## Typography
- **Display/Headings**: `Lora`, 'Source Serif 4', Georgia, serif (editorial warmth).
- **Body / UI Labels**: `Inter`, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif.
- **Mono / Data / Specs / Logcat**: `JetBrains Mono`, Consolas, monospace with `font-variant-numeric: tabular-nums`.
- **Type Scale**:
  - `text-xs`: 0.75rem (12px) - timestamps, chip labels, micro badges.
  - `text-sm`: 0.8125rem (13px) - device specs, secondary labels, battery levels.
  - `text-base`: 0.875rem (14px) - body text, log lines, status descriptions.
  - `text-md`: 1.0rem (16px) - panel subheadings, device names.
  - `text-lg`: 1.1875rem (19px) - section titles.
  - `text-xl`: 1.375rem (22px) - primary header.

## Color Palette
- **Canvas & Backgrounds**:
  - `--bg-canvas`: `#262624` (warm dark charcoal base).
  - `--bg-sidebar`: `#1E1E1C` (deep matte background for sidebar & cards).
  - `--bg-panel`: `#1A1918` (dark container surface).
  - `--bg-elevated`: `#2E2D2A` (card hover state, elevated rows).
  - `--bg-active`: `#3A3834` (active selection fill).
- **Borders & Dividers**:
  - `--border-hairline`: `rgba(255, 255, 255, 0.08)` (delicate, never boxy).
  - `--border-subtle`: `#333230`.
  - `--border-strong`: `#45433F`.
- **Text Tiers**:
  - `--text-primary`: `#F5F1EA` (warm cream off-white, high contrast).
  - `--text-secondary`: `#A39E93` (muted warm gray-beige).
  - `--text-tertiary`: `#736F66` (subdued labels).
- **Brand Accent**:
  - `--accent-coral`: `#D97757` (authentic Kelvra terracotta / coral brand accent).
  - `--accent-coral-hover`: `#E08567`.
  - `--accent-coral-subtle`: `rgba(217, 119, 87, 0.14)`.
- **Semantic Status Indicators**:
  - Online / Connected: `#10B981` (quiet emerald dot).
  - Idle / Standby: `#A39E93` (muted neutral dot).
  - Busy / Running Test: `#F59E0B` (amber dot).
  - Offline / Unauthorized: `#EF4444` (crimson dot).

## Spacing & Component Layout
- 4px Base unit: `space-1` (4px), `space-2` (8px), `space-3` (12px), `space-4` (16px), `space-5` (20px), `space-6` (24px).
- **Layout Architecture**:
  1. Top Navigation Bar: Brand mark (`KELVRA DEVICE LAB`), connected device counter, global status, Bench bridge link.
  2. Left Device Fleet Rail: Auto-scanned device list with status pills, battery meter, Android version, and architecture.
  3. Center Interactive Teleoperation Stage: Live high-DPI canvas mirror of device screen with click-to-tap, drag-to-swipe, and virtual hardware key rail (Back, Home, Recents, Power, Volume).
  4. Right Diagnostics & Telemetry Panel: Real-time CPU, RAM, battery temperature, storage, network mode, and APK test runner controls.
  5. Bottom Live Logcat Console: Virtualized log stream with level filters (Verbose, Debug, Info, Warn, Error), live search, and auto-scroll freeze.
