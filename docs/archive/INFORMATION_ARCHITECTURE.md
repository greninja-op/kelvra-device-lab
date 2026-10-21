# KELVRA Device Lab — Information Architecture & Navigation Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/INFORMATION_ARCHITECTURE.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Status:** Verified Information Architecture Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Structure & Navigation Philosophy

Device Lab functions both as an autonomous standalone control console (`http://127.0.0.1:8098/`) and as an eventual docked tool within KELVRA Bench. The information architecture prioritizes:
- **Instant Operational Readiness:** One click from initial arrival to live device streaming.
- **Context Preservation:** Navigating between live streaming, diagnostics, and test execution preserves the active device session and socket pipeline.
- **Deep-Linkable Entities:** Direct URLs allow linking straight to a device inspection view, active session, or test execution report.
- **Zero Empty Traps:** Sections that do not have active backend capabilities (e.g. cloud emulators, iOS teleoperation on Windows) are explicitly classified as deferred rather than displaying non-functional dummy navigation items.

---

## 2. Navigation Taxonomy & Section Matrix

| Section / Route | Scope | Primary Purpose | MVP Status |
| :--- | :--- | :--- | :--- |
| **Overview** (`/`) | Global Fleet | Global fleet health, connected device summary, quick connection actions. | **MVP Core** |
| **Device Inventory** (`/devices`) | Fleet View | Full searchable, filterable grid and table of physical & virtual devices. | **MVP Core** |
| **Live Device Viewer** (`/devices/{id}/view`) | Device Studio | Interactive 3-column teleoperation studio, aspect-locked stream, input injector, logcat. | **MVP Core** |
| **Device Details** (`/devices/{id}/details`) | Hardware Spec | Comprehensive hardware telemetry, display metrics, OS build, ABI, battery health. | **MVP Core** |
| **Virtual Devices** (`/virtual`) | Emulator Hub | Local Android AVD management, headless emulator booting, cold-boot controls. | **MVP Core** |
| **Session Management** (`/sessions`) | Leases & Locks | Active operator leases, multi-viewer streaming sessions, lock revocation. | **MVP Core** |
| **Automation** (`/automation`) | Test Runner | APK installation, test suite execution, screenshot assertions, pass/fail ledger. | **MVP Core** |
| **Logs & Diagnostics** (`/diagnostics`) | System Health | Real-time system logs, ADB server diagnostics, WebSocket pipe metrics, audit ledger. | **MVP Core** |
| **Settings** (`/settings`) | Configuration | Port allocations, ADB binary path, video encoding defaults, log retention. | **MVP Core** |
| *Cloud Fleet Federation* | Multi-Host | Distributed device farm spanning multiple developer workstations. | *Deferred (Phase 8+)* |
| *iOS WebInspector Bridge* | Apple Safari | Live Safari DOM debugger for iOS devices. | *Deferred (Release 1.x)* |

---

## 3. Global Navigation Layout

### 3.1 Primary Navigation Topbar
The global topbar provides continuous ecosystem awareness:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ KELVRA Device Lab   /devices/8TCABAIFWOZTDICI/view   ● 1 Device Online  | Lease: Admin (04:12)   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Brand Lockup (Left):**
   - Wordmark: "KELVRA" (Inter 13px bold, `--text-secondary`) + "Device Lab" (Lora 16px medium, `--text-primary`).
   - Clicking returns to `/` (Overview) with active confirmation if a test is executing.
2. **Contextual Breadcrumb (Center):**
   - e.g. `Devices` > `POCO X6 Pro 5G (8TCABAIFWOZTDICI)` > `Live Studio`.
   - Each segment is clickable and displays an accessible focus ring on keyboard tab.
3. **Ecosystem & Session Status (Right):**
   - Fleet Status: `● 1 Online` (green dot) | `● 0 Blocked` | `Port :8098`.
   - Active Lease Pill: `Exclusive Lease: You` (terracotta wash) with countdown timer (`tabular-nums`).
   - Bench Coordination Link: Direct status indicator verifying KELVRA Bench EventBus connectivity.

### 3.2 Studio Workspace Layout (3-Column Context)
When navigating inside a device workspace (`/devices/{id}/view`), the global navigation gracefully recedes to maximize screen real estate:
- **Left Column (300px):** Fast device switcher list. Clicking another device seamlessly switches the viewport without losing diagnostic tab context.
- **Center Stage (Flex 1):** Dedicated to the interactive mobile canvas and hardware navigation bar.
- **Right Column (380px):** Tabbed hub switching between Telemetry, Logcat, Automation, and Shell.

---

## 4. Breadcrumbs & Deep Linking Specification

### 4.1 URL Route Patterns
- `/`: Overview & Fleet Summary.
- `/devices`: Complete device inventory.
- `/devices?platform=android&status=online`: Filtered inventory query.
- `/devices/{serial}/view`: Live teleoperation studio for device `{serial}`.
- `/devices/{serial}/details`: Deep hardware telemetry and system properties.
- `/devices/{serial}/logs`: Direct full-screen logcat inspection.
- `/automation`: Test suite runner overview.
- `/automation/runs/{run_id}`: Granular assertion output and screenshot comparisons for run `{run_id}`.
- `/sessions`: Active single-writer lease table.
- `/diagnostics`: Host ADB health and WebSocket pipe bandwidth.
- `/settings`: Host and streaming configuration.

### 4.2 Browser History & Session Recovery
- Deep links restore full device context immediately upon browser refresh.
- If a user navigates to `/devices/{serial}/view` for an offline device, the interface renders an informative "Device Offline" screen with a direct "View Last Known Details" action rather than a 404 error.
- State preservation: Query parameters (`?filter=error&tag=KelvraCompanion`) persist in the URL so developers can share direct links to specific debugging scenarios.
