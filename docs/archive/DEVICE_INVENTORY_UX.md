# KELVRA Device Lab — Device Inventory UX Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVICE_INVENTORY_UX.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract
- **Status:** Verified Device Inventory Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Inventory Role

The Device Inventory (`/devices`) is the primary fleet management cockpit for KELVRA Device Lab. It catalogs all physical phones, tablets, local emulators (AVDs), and potential future remote agents connected to the host workstation.

The interface prioritizes:
1. **High Information Density Without Clutter:** Fast visual scanning across 10 to 50 devices.
2. **Clear Separation of Identity vs Transient State:** Hardware model and serial remain persistent; connection status, battery, and stream leases update dynamically.
3. **Dual View Architecture:** Grid view (spacious cards for visual identification) and Table view (dense rows for bulk management and swarm operations).

---

## 2. Card View vs Table View

### 2.1 View Toggle Control
Positioned on the inventory toolbar:
- Segmented pill toggle: `[Card Grid] | [Dense Table]`.
- Choice is persisted in `localStorage` under `kelvra_device_inventory_view`.

### 2.2 Card View Specification (Grid)
Grid definition: `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;`.

Each device card is rendered on `--bg-sidebar` (`#1E1E1C`) with a hairline border:
```
┌────────────────────────────────────────────────────────────┐
│ [Android Icon] POCO X6 Pro 5G              ● Online        │
│ 8TCABAIFWOZTDICI                           USB 3.0         │
├────────────────────────────────────────────────────────────┤
│ Platform: Android 14 (API 34)    Battery: 82% (Charging)   │
│ Display:  1220x2712 @ 120Hz      Thermals: 32.4°C (Normal) │
├────────────────────────────────────────────────────────────┤
│ Lease: Available                 Last Seen: Active Now     │
├────────────────────────────────────────────────────────────┤
│ [Launch Studio]                            [Details] [...] │
└────────────────────────────────────────────────────────────┘
```

**Card Hierarchy:**
1. **Card Header:** Platform outline vector icon (Android robot / Apple glyph), Device Model (Lora 16px, `--text-primary`), and Status dot (`● online` in quiet green).
2. **Sub-Header:** Serial number in `JetBrains Mono` 12px (`--text-secondary`) and Connection Transport (`USB 3.0`, `Wi-Fi 5GHz`, or `AVD Pipe`).
3. **Telemetry Matrix (2x2 Inset):**
   - OS & SDK level badge.
   - Live battery level with charging state.
   - Display resolution and native refresh rate.
   - Device thermal state.
4. **Card Footer:**
   - Lease indicator: `Lease: Available` (neutral) or `Lease: Agent-Frontend` (amber).
   - Primary Action Button: "Launch Studio" (`.btn.primary` terracotta) opens Live Device Viewer.
   - Context Menu trigger `[...]`: "Reboot Device", "Capture Bugreport", "Wipe Cache".

### 2.3 Table View Specification (Tabular Density)
For developers managing larger fleets or autonomous swarms:
- Column Headers: `[Select]` | `Device Model` | `Serial` | `Platform` | `OS / SDK` | `Transport` | `Battery` | `Thermals` | `Status` | `Lease Holder` | `Actions`.
- Row height: 44px (touch accessible).
- Hover state: Row background changes to `--bg-hover` (`#33312D`) in 150ms.
- Zebra striping: Subtly alternating between `--bg-sidebar` and `--bg-canvas` with hairline bottom borders.

---

## 3. Search, Filtering, Sorting & Grouping

### 3.1 Live Search Filter
- Input field with search icon (`stroke-width: 1.8px`).
- Matches instantaneously across:
  - Model Name (e.g. `POCO`, `Pixel`, `Galaxy`).
  - Manufacturer (e.g. `Xiaomi`, `Google`, `Samsung`).
  - Serial Number (e.g. `8TCABAIFWOZTDICI`, `emulator-5554`).
  - Target ABI (e.g. `arm64-v8a`, `x86_64`).

### 3.2 Granular Filter Chips
- **Platform:** `All`, `Android Physical`, `Android Emulator (AVD)`, `iOS Physical`.
- **Status:** `All`, `Online (Ready)`, `Busy (Streaming)`, `Unauthorized (RSA)`, `Offline`.
- **Lease State:** `All`, `Available`, `Reserved / Leased`.

### 3.3 Sorting Options
- Sort dropdown:
  - *Status (Online first)* [Default].
  - *Device Model (A-Z)*.
  - *Last Seen (Most recent first)*.
  - *Battery Level (High to Low)*.

### 3.4 Logical Grouping
Toggle to group devices by:
1. **Platform:** Physical Android, Virtual Android (AVD), Physical Apple iOS.
2. **Availability:** Ready for Use, In Active Session, Blocked / Unauthorized.

---

## 4. Multi-Device Batch Operations

When one or more checkboxes are selected in table view (or cards are multi-selected with Shift+Click):
- A sticky **Batch Action Bar** slides in at the bottom center of the screen (`--duration-normal: 260ms`):
  - Badge: `3 devices selected`.
  - Action 1: "Install APK on Fleet..." (Opens file picker / drag-and-drop modal).
  - Action 2: "Run Smoke Test Suite".
  - Action 3: "Reboot Devices" (Opens confirmation modal).
  - Dismiss: "Deselect All".

---

## 5. Responsive Behavior

- **4K / Ultrawide Displays (> 1920px):** Card grid expands to 4 or 5 columns.
- **Standard Desktop (1440px - 1920px):** 3-column card grid.
- **Laptop (1024px - 1440px):** 2-column card grid.
- **Narrow Tablet / Split View (< 1024px):** Automatically collapses to single-column card grid or scrollable table.
