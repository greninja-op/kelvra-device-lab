# KELVRA Device Lab — Device Inventory UI Implementation Specification

## 1. Overview

The Device Inventory subsystem provides the operator interface for managing mobile devices in KELVRA Device Lab. It adheres strictly to the KELVRA Bench design contract and tokens:
- **Font Stack:** Inter (UI), JetBrains Mono (code/metrics), Lora (headings).
- **Color Palette:** Warm dark obsidian background (`#121210`), elevated panels (`#181816`, `#1E1E1C`), coral accents (`#D97757`), flat status dots (`#788C5D` complete, `#6A9B9B` working, `#C9944D` blocked, `#C46550` error).
- **Zero Emoji Prohibition:** 100% vector SVG icons and flat dots only.

---

## 2. Inventory UI Components

### 2.1 Fleet Statistics Strip
Displays aggregate metrics computed dynamically by `GET /api/registry/stats`:
- Total Fleet Count
- Available / Online Devices
- Connected Active Sessions
- Unauthorized Devices

### 2.2 Inventory Toolbar
- **Search Bar:** Real-time client-side substring matching across serial, model, and manufacturer.
- **Platform Filter:** Dropdown filtering by `android_physical`, `android_virtual`, or `apple_physical`.
- **State Filter:** Dropdown filtering by lifecycle state (`available`, `connected`, `unauthorized`, `unavailable`).
- **Layout Switcher:** Grid card view vs dense data table view.
- **Rescan Trigger:** Re-polls host ADB daemon and refreshes fleet inventory.

### 2.3 Card Grid View
Each device card presents:
- Device Model and Manufacturer title lockup.
- Flat status dot with uppercase lifecycle state label.
- Platform, Transport, and Battery badges.
- Hardware specifications table (Serial, OS version, SDK level, ABI architecture).
- Quick-copy button for hardware serial.
- Prominent amber alert box for unauthorized devices with physical guidance instructions.
- Connect / Disconnect action buttons wired directly to `/api/devices/{id}/connect` and `/api/devices/{id}/disconnect`.

### 2.4 Table View
Dense tabular layout displaying Status, Model, Serial, Platform/Transport, OS/ABI, and Action buttons.

### 2.5 Honest Empty State
When 0 devices are attached or when filters match no devices, an authentic empty state is rendered with an invitation to plug in hardware or boot an emulator. Simulated or fake devices are strictly prohibited.
