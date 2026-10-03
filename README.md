# KELVRA Device Lab

Autonomous device testing, teleoperation, and mobile fleet orchestration laboratory for KELVRA Companion devices.

Part of the **KELVRA** (Kinetic Execution Layer, Verified Routing for Agents) ecosystem.
Eventual integration destination: **KELVRA Bench** (`kelvra-bench`).

---

## Capabilities

1. **Fleet Discovery & Status Engine:**
   - Real-time ADB device discovery (physical USB, Wi-Fi ADB, emulators).
   - Rich hardware introspection: model, manufacturer, SoC, ABI, Android OS version, SDK API level, display resolution, pixel density, battery status, thermals, and network state.

2. **Low-Latency Teleoperation & Input Injection:**
   - Real-time screen capture and streaming via WebSockets.
   - Interactive remote input: click-to-tap, drag-to-swipe, virtual hardware navigation keys (Back, Home, Recents, Power, Volume).
   - Direct text typing injection via ADB keyboard emulation.

3. **Live Logcat Streaming:**
   - Real-time log streaming over WebSockets.
   - Dynamic tag, severity (Verbose, Debug, Info, Warning, Error), and regex filtering.
   - Circular buffer history for instant inspection upon connection.

4. **Hardware Telemetry & Health Monitoring:**
   - Real-time tracking of CPU utilization, RAM usage, internal storage capacity, and battery temperature.
   - Fail-safe thermal and battery alert triggers.

5. **Companion Test Runner:**
   - Automated APK installation and verification.
   - Package launch, foreground monitoring, and clean termination.
   - Screenshot capture with assertion verification.

6. **KELVRA Bench Bridge:**
   - Bi-directional event synchronization with KELVRA Bench.
   - Automatic registration and pairing status validation against `data/paired_devices.json`.

---

## Design System

Adheres strictly to the **KELVRA Bench Design Contract**:
- Warm editorial dark charcoal canvas (`#262624`) with deep matte cards (`#1E1E1C`).
- Authentic terracotta accent (`#D97757`).
- Typography: Lora (headings), Inter (interface), JetBrains Mono (metrics and logs).
- Strict Zero-Emoji Rule: 100% authentic vector SVG icons; zero raw unicode emojis.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Android SDK Platform Tools (`adb` on PATH)

### Installation
```bash
pip install -r requirements.txt
```

### Running the Server
```bash
python -m uvicorn src.server:app --port 8098 --host 127.0.0.1
```

The Web Control Console will be available at `http://127.0.0.1:8098/`.

### Running Tests
```bash
pytest -q
```
