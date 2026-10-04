# KELVRA Device Lab — Screen-by-Screen UX Specifications

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SCREEN_SPECIFICATIONS.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract (`#262624`, `#1E1E1C`, `#D97757`, Lora, Inter, JetBrains Mono)
- **Status:** Verified Screen-by-Screen Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Screen 1: Device Lab Overview (`/`)

### 1.1 Purpose
The executive landing dashboard providing fleet health at a glance, quick connection actions, and direct entry points to active devices and tests.

### 1.2 Layout & Information Hierarchy
- **Header:** Lora 22px title: "Fleet Overview", subtitle: "Autonomous mobile testing laboratory on port :8098".
- **Hero Metric Tiles (4-Column Grid, minmax(220px, 1fr)):**
  1. *Total Connected Devices:* Large tabular numeral (`text-2xl`), subline: `1 physical, 0 virtual`.
  2. *Active Teleoperation Sessions:* Numeral, subline: `1 exclusive lease active`.
  3. *Fleet Health Status:* `● All systems operational` (quiet green dot), subline: `ADB 1.0.41 running`.
  4. *Automated Test Pass Rate:* `100%` (green), subline: `Last run: 14 mins ago (Run #104)`.
- **Primary Section (2-Column Split: 65% / 35%):**
  - *Left (65%):* Active Device Inventory Preview. Top 3 connected devices with live thumbnail/status, platform icon, model name, and a primary CTA "Launch Studio".
  - *Right (35%):* Recent Activity Ledger. Last 10 events (device attached, test executed, lease expired) with mono timestamps.
- **Actions:**
  - Primary button: "Scan for Devices" (`.btn.primary`, terracotta `#D97757`).
  - Secondary button: "Launch Virtual Device" (`.btn`).

### 1.3 States
- **Loading:** Skeleton pulses using `--bg-elevated` on tiles (no spinner).
- **Empty State:** When no devices are attached, renders honest empty tile: "No mobile devices detected. Plug in an Android phone with USB Debugging enabled or start an emulator." Actions: "Scan Devices" and "Troubleshooting Guide".
- **Error State:** If ADB daemon is stopped, renders amber warning banner: "ADB server unreachable on 127.0.0.1:5037. Click 'Restart ADB Daemon' to reconnect."

---

## 2. Screen 2: Device Inventory (`/devices`)

### 2.1 Purpose
Comprehensive fleet management interface supporting multi-attribute filtering, search, sorting, and batch actions across physical and virtual devices.

### 2.2 Layout & Controls
- **Toolbar:**
  - Search Input: Real-time search across model name, manufacturer, and serial (`--bg-panel`, hairline border).
  - Platform Filter Pill Group: `All`, `Android Physical`, `Android Virtual`, `iOS Physical`.
  - Status Filter: `All`, `Online`, `Busy`, `Unauthorized`, `Offline`.
  - View Toggle: Grid view (card tiles) vs Table view (dense tabular rows).
- **Inventory Grid / Table:**
  - *Card View:* Device cards displaying platform outline icon, model name (Lora 16px), serial (JetBrains Mono 12px), OS badge (`Android 14 / API 34`), connection transport (`USB 3.0`), status dot, and action button.
  - *Table View:* Columns for Select, Device Name, Serial, Platform, OS Version, Battery %, Thermal °C, Status, Lease Holder, and Actions.
- **Batch Actions Bar (Appears on row selection):**
  - "Install APK on Selected", "Reboot Selected", "Run Smoke Test Suite".

---

## 3. Screen 3: Device Details (`/devices/{serial}/details`)

### 3.1 Purpose
In-depth technical specification and hardware telemetry inspection for a specific device.

### 3.2 Layout & Data Sections
- **Device Identity Header:**
  - Model Name: Lora 22px (e.g. "POCO X6 Pro 5G").
  - Hardware Badges: `xiaomi`, `MediaTek Dimensity 8300-Ultra`, `arm64-v8a`, `SDK 34 (Android 14)`.
- **Telemetry & Hardware Grid (2x2 Cards):**
  1. *Display Subsystem:* Resolution (`1220 x 2712 px`), Density (`480 dpi`), Refresh Rate (`120 Hz`), Current Orientation (`Portrait`).
  2. *Power & Thermals:* Battery Level (`82% charging`), Battery Health (`Good`), Battery Temp (`32.4°C`), Thermal Throttling (`None`).
  3. *Storage & Memory:* Internal Storage (`214 GB / 512 GB free`), RAM (`7.4 GB / 12 GB in use`).
  4. *Network & Radio:* WiFi SSID (`Office_5G`), IP Address (`192.168.1.144`), Cellular State (`LTE / SIM Active`).
- **Installed Packages Drilldown:** Searchable list of installed third-party and companion packages with package name, version code, and launch/uninstall triggers.

---

## 4. Screen 4: Connection & Pairing (`/devices/connect`)

### 4.1 Purpose
Interactive onboarding and pairing wizard guiding developers through physical USB attachment, wireless ADB pairing, and iOS developer mode trust.

### 4.2 Layout & Wizard Flows
- **3-Step Tab Bar:** `1. Physical USB`, `2. Wireless ADB (Wi-Fi)`, `3. Virtual Emulator`.
- **Step 1: Physical USB Flow:**
  - Illustrated instructions (SVG line diagrams, no emojis):
    1. Connect device via USB cable to host workstation.
    2. Open *Settings > About Phone* and tap *Build Number* 7 times to enable Developer Options.
    3. Enable *USB Debugging* and *Install via USB*.
    4. When prompt appears on phone, check *Always allow from this computer* and tap *Allow*.
  - Live Connection Detector: Polling indicator showing connection status (`Waiting for device...` -> `Device Detected: Unauthorized` -> `Authorized & Online`).
- **Step 2: Wireless Pairing Flow:**
  - Fields: `Device IP Address`, `Port` (e.g. `37015`), `Pairing Code` (6 digits).
  - Submit button: "Pair Wireless Device".

---

## 5. Screen 5: Live Device Viewer (`/devices/{serial}/view`)

### 5.1 Purpose
Central teleoperation studio. Provides real-time aspect-ratio locked screen streaming, precision touch/keyboard injection, live logcat streaming, and test execution.

### 5.2 3-Column Studio Layout
- **Left Column (300px) — Quick Device Rail:** Collapsible list of connected devices for instant switching.
- **Center Stage (Flex 1, min 500px) — Live Viewport:**
  - *Viewer Header:* Device title, resolution badge, orientation flip button, zoom selector (Fit, 50%, 75%, 100%), and live FPS/latency chip.
  - *Stream Canvas:* Aspect-ratio locked canvas surrounded by dark container panel (`#1A1918`). Touch ripple animation (`rgba(217, 119, 87, 0.40)`) rendered on click/drag.
  - *Hardware Navigation Bar (Bottom):* Outlined vector icons for `Back` (Android triangle), `Home` (circle), `Recents` (square), `Power`, `Volume Down`, `Volume Up`.
- **Right Column (380px) — Contextual Hub:**
  - Tabs: `Telemetry`, `Logcat`, `Automation`, `Settings`.
  - Full details specified in [`docs/DEVICE_VIEWER_UX.md`](file:///C:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_VIEWER_UX.md).

---

## 6. Screen 6: Virtual Device Management (`/virtual`)

### 6.1 Purpose
Local Android Virtual Device (AVD) orchestration hub for launching, stopping, and managing headless emulator instances.

### 6.2 Layout & Controls
- **AVD Cards Grid:**
  - Card attributes: AVD Name (e.g. `Pixel_7_API_34`), Target SDK (`Android 14.0 Google APIs`), System ABI (`x86_64`), Disk Size (`6.2 GB`), Current State (`Stopped` / `Booting` / `Online`).
  - Actions: "Start Headless", "Start GUI Window", "Cold Boot (Wipe Data)", "Delete AVD".
- **Creation Dialog:**
  - Select device profile (e.g. Phone, Tablet, Wear).
  - Select system image (checks local Android SDK availability).
  - Configure RAM, internal storage, and headless toggle.

---

## 7. Screen 7: Session Management (`/sessions`)

### 7.1 Purpose
Governance and audit interface tracking active single-writer operator leases, multi-viewer streaming sessions, and lock revocation.

### 7.2 Layout & Tables
- **Active Leases Table:**
  - Columns: Target Device, Lease Holder (Agent ID or User), Role (`Operator` / `Developer`), Acquired At, Inactivity Timeout Countdown (`tabular-nums`), Action (`Revoke Lease`).
- **Concurrent Stream Viewers Table:**
  - Columns: Device, Client Remote IP, Protocol (`WebSocket / Binary`), Stream Type (`Baseline JPEG` / `H.264 WebCodecs`), Frame Rate, Connection Uptime.
- **Revocation Safety Gate:**
  - Clicking "Revoke Lease" opens confirmation modal: "Revoking the lease will immediately terminate active input injection for Agent 'agent-qa-builder'. Confirm revocation?"

---

## 8. Screen 8: Automation & Test Runner (`/automation`)

### 8.1 Purpose
Automated test suite orchestrator for executing mobile smoke tests, companion verification scripts, APK installations, and screenshot comparison assertions.

### 8.2 Layout & Sections
- **Test Suite Selection:**
  - Available test suites: `Companion Cold Launch & Heartbeat`, `Deep Link Audio Routing`, `Bluetooth Audio Bridge Verification`.
- **Target Device Selector:** Dropdown of available online devices with single-writer lock acquisition check.
- **Live Execution Ledger:**
  - Real-time step progress list: Step 1 (Install APK) -> Step 2 (Launch Activity) -> Step 3 (Assert Foreground) -> Step 4 (Capture Screenshot).
  - Status indicators: `working` (blue pulse) -> `complete` (green dot) or `error` (crimson dot).
- **Screenshot Comparison Pane:** Side-by-side golden reference vs live captured frame with difference overlay.

---

## 9. Screen 9: Logs & Diagnostics (`/diagnostics`)

### 9.1 Purpose
Centralized operational diagnostics, ADB transport health, WebSocket pipe bandwidth, and security audit log viewer.

### 9.2 Layout & Tools
- **Subsystem Health Strip:**
  - ADB Daemon: `Running on 127.0.0.1:5037` (Green).
  - WebSocket Port: `Listening on :8098` (Green).
  - SQLite Audit Store: `WAL Mode / 1.2 MB` (Green).
  - Sibling Isolation: `Voice (:8090) & Bench (:8099) Protected` (Green).
- **Audit Log Ledger:**
  - High-density tabular event log: Timestamp, Event Type (`DEVICE_ATTACHED`, `LEASE_ACQUIRED`, `APK_INSTALLED`, `SHELL_EXECUTED`), Actor, Target Device, Result (`SUCCESS` / `DENIED`).
  - Search and export triggers (`Export JSON`, `Export CSV`).

---

## 10. Screen 10: Device Lab Settings (`/settings`)

### 10.1 Purpose
Host configuration, platform tooling paths, video encoding preferences, and retention controls.

### 10.2 Configuration Categories
- **Platform Tools Configuration:**
  - `ADB Binary Path`: e.g. `C:\Users\Athira Aswin\AppData\Local\Android\Sdk\platform-tools\adb.exe` (validated on save).
  - `Android SDK Root`: Auto-detected environment path.
- **Video & Streaming Preferences:**
  - Default Streaming Tier: Radio selector (`Baseline JPEG WebSocket (Low Overhead)` vs `scrcpy H.264 WebCodecs (60 FPS)`).
  - Max Bitrate: Dropdown (`2 Mbps`, `4 Mbps`, `8 Mbps`).
  - Default Resolution Cap: `1080p`, `720p`, `Native`.
- **Security & Leases:**
  - Inactivity Lease Timeout: Input (`300 seconds`).
  - Logcat Buffer Retention: Input (`1,000 lines`).
  - Audit Log Retention: Input (`30 days`).
- **Save Trigger:** Terracotta primary button "Save Configuration" with instant feedback notification.
