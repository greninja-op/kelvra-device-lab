# KELVRA Device Lab — Live Device Viewer UX Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEVICE_VIEWER_UX.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract
- **Status:** Verified Device Viewer Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Viewer Role

The Live Device Viewer is the central operational environment of KELVRA Device Lab. It provides:
1. Low-latency, aspect-ratio-locked screen streaming over binary WebSockets.
2. Direct interactive teleoperation (touch injection, drags, swipes, hardware keys).
3. Real-time logcat streaming with virtualized row rendering and tag filtering.
4. Concurrent inspection of hardware telemetry (CPU, RAM, thermals, battery).
5. Integrated test automation triggers.

---

## 2. 3-Column Studio Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Topbar: POCO X6 Pro 5G  | 1220x2712 px  | 30.2 FPS (42ms) | Lease: Admin (Active) | [End Session]│
├───────────────────┬──────────────────────────────────────────────┬───────────────────────────────┤
│ Left Rail (300px) │ Center Stage: Live Viewport (Flex: 1)        │ Right Rail (380px)            │
│                   │                                              │                               │
│ Fleet Switcher    │ ┌──────────────────────────────────────────┐ │ Tabbed Hub:                   │
│ - POCO X6 Pro     │ │ [Viewer Toolbar: Scale, Rotate, Capture] │ │ 1. Telemetry                  │
│   (Active ●)      │ ├──────────────────────────────────────────┤ │ 2. Logcat Feed               │
│ - Pixel 7 (AVD)   │ │                                          │ │ 3. Automated Test Runner      │
│   (Idle ●)        │ │  Aspect-Ratio Locked Screen Canvas       │ │ 4. Device Settings            │
│                   │ │  (Touch Ripple Feedback Overlay)         │ │                               │
│ [Add Device]      │ │                                          │ │ [Log Filter: KelvraCompanion] │
│                   │ ├──────────────────────────────────────────┤ │ [Severity: Info/Warn/Error]   │
│                   │ │ [Hardware Nav: Back, Home, Apps, Pwr, Vol│ │                               │
│                   │ └──────────────────────────────────────────┘ │                               │
└───────────────────┴──────────────────────────────────────────────┴───────────────────────────────┘
```

---

## 3. Main Viewing Region & Canvas Engine

### 3.1 Aspect-Ratio Preservation Algorithm
Physical devices come in diverse display aspect ratios (e.g. 20:9, 19.5:9, 16:9, 4:3). The viewport container dynamically computes pillarbox (horizontal gutters) or letterbox (vertical gutters) inside `--bg-panel` (`#1A1918`):

```javascript
function computeFitDimensions(containerW, containerH, deviceW, deviceH) {
  const containerAspect = containerW / containerH;
  const deviceAspect = deviceW / deviceH;
  let renderW, renderH;

  if (deviceAspect > containerAspect) {
    // Width constrained -> letterbox (top/bottom gutters)
    renderW = containerW;
    renderH = Math.round(containerW / deviceAspect);
  } else {
    // Height constrained -> pillarbox (left/right gutters)
    renderH = containerH;
    renderW = Math.round(containerH * deviceAspect);
  }
  return { width: renderW, height: renderH };
}
```

### 3.2 Zoom & Scaling Modes
The viewer toolbar provides a scale selector:
- **Fit to Window (Default):** Canvas scales dynamically to maximize usable area without scrollbars.
- **50% Scale:** High-density downscaled view for multi-window workflows.
- **75% Scale:** Balanced developer preview.
- **100% Native 1:1:** Pixel-perfect inspection mode; enables viewport pan/scroll bars if display exceeds container size.

### 3.3 Dynamic Orientation Transitions
When the device rotates from Portrait to Landscape (or vice-versa):
1. The backend ADB window-manager watcher detects the orientation change.
2. The frontend triggers a smooth 260ms transition (`--duration-normal: 260ms var(--ease-out)`).
3. The canvas dimensions smoothly interpolate to the new aspect ratio without frame flicker or black tears.

### 3.4 Fullscreen Mode
- Standard Fullscreen Button (`F11` or toolbar icon) expands the viewing canvas to occupy the full monitor.
- In fullscreen mode, the hardware navigation bar floats unobtrusively at the bottom edge and fades to 20% opacity after 3 seconds of cursor inactivity.

---

## 4. Operational States of the Viewer

### 4.1 Viewer Loading State (Connecting)
- **Visuals:** Center stage renders the device frame with an inset charcoal canvas (`#1A1918`).
- A subtle emerald pulsing dot (`#10B981`) appears with the text: "Negotiating stream pipeline with device 8TCABAIFWOZTDICI...".
- **Rule:** Never display spinning circles or synthetic percentage bars.

### 4.2 Active Streaming State
- High-performance 2D Canvas rendering incoming JPEG binary blobs or WebCodecs VideoFrames.
- Discrete telemetry HUD badge in the top-right corner showing: `30.0 FPS · 38ms latency` in `JetBrains Mono` tabular nums.
- Precision crosshair or pointer cursor indicating remote touch readiness.

### 4.3 Stream Failure / Network Hiccup State
- If the WebSocket disconnects unexpectedly:
  - The canvas displays the last known good frame overlaid with a 50% dark charcoal wash (`rgba(26, 25, 24, 0.70)`).
  - An amber status pill appears: `● Reconnecting stream (Attempt 1/5)...`.
  - Polling attempts reconnection every 2 seconds with exponential backoff up to 10 seconds.

### 4.4 Disconnected State (USB Cable Unplugged)
- If the physical device is unplugged:
  - The stream cleanly stops and releases memory buffers.
  - The canvas clears to `--bg-panel` with an honest empty state:
    - *Title:* "Device Disconnected" (Lora 16px).
    - *Body:* "USB connection lost for POCO X6 Pro 5G. Reattach cable to resume teleoperation."
    - *Action:* Primary button "Return to Fleet Overview".

---

## 5. Viewer Toolbar & Controls

The toolbar spans the top of the center stage:

| Control | Icon / Label | Behavior & Shortcut |
| :--- | :--- | :--- |
| **Device Model** | `POCO X6 Pro 5G` | Displays device name in Lora 16px with platform badge. |
| **Orientation Toggle** | Outlined Rotate Icon | Sends ADB shell `settings put system user_rotation` (Ctrl+R). |
| **Scale Selector** | `Fit` / `50%` / `100%` | Adjusts rendering scale algorithm. |
| **Screenshot** | Outlined Camera Icon | Captures lossless PNG from device frame buffer and opens download (Ctrl+S). |
| **Screen Record** | Outlined Record Icon | Toggles MP4 screen capture on device (`screenrecord`). |
| **Fullscreen** | Outlined Maximize Icon | Enters distraction-free full-display mode (F11). |
| **End Lease / Lock** | `Release Lease` | Releases single-writer input lease back to the pool. |

---

## 6. Remote Interaction & Input Injection

### 6.1 Touch & Pointer Mapping
- **Click (Touch Down + Up):** Injects tap at normalized coordinates:
  $$x_{\text{device}} = \frac{x_{\text{canvas}}}{\text{width}_{\text{canvas}}} \times W_{\text{device}}, \quad y_{\text{device}} = \frac{y_{\text{canvas}}}{\text{height}_{\text{canvas}}} \times H_{\text{device}}$$
- **Click & Drag (Swipe / Scroll):** Records pointer down, movement delta, and pointer up; sends ADB swipe sequence or scrcpy touch motion packets.
- **Visual Touch Ripple:** Every registered tap renders a 20px terracotta ripple circle (`rgba(217, 119, 87, 0.40)`) that expands to 40px and fades out over 200ms, providing immediate tactile confirmation.

### 6.2 Hardware Navigation Control Bar
Fixed below the screen canvas:
- `Back` (triangle icon, `Escape` or `Right-Click`): Injects `KEYCODE_BACK` (code 4).
- `Home` (circle icon, `Middle-Click`): Injects `KEYCODE_HOME` (code 3).
- `Recents / App Switcher` (square icon): Injects `KEYCODE_APP_SWITCH` (code 187).
- `Power` (power icon): Injects `KEYCODE_POWER` (code 26).
- `Volume Down / Up` (speaker icons): Injects `KEYCODE_VOLUME_DOWN` (25) / `KEYCODE_VOLUME_UP` (24).

### 6.3 Physical Keyboard Forwarding
- When the canvas has focus, keyboard typing events are captured:
  - Standard alphanumeric characters are sent via `adb shell input text '<escaped_string>'`.
  - Enter key injects `KEYCODE_ENTER` (66).
  - Backspace key injects `KEYCODE_DEL` (67).

---

## 7. Supporting Panels (Right Rail)

The right rail provides 4 tabbed workspaces:
1. **Telemetry Tab:** Real-time gauges for CPU utilization, RAM consumption, battery %, and battery thermals (`32.4°C`).
2. **Logcat Tab:** High-velocity virtualized log feed with real-time severity filtering (`V`, `D`, `I`, `W`, `E`) and tag search (`KelvraCompanion`).
3. **Automation Tab:** One-click APK install dropzone, active test scripts, and pass/fail step indicators.
4. **Settings Tab:** Device display density (`wm density`), language/locale selector, and safe ADB shell command runner.
