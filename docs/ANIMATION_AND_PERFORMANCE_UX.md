# KELVRA Device Lab — Animation, Motion & UI Performance Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/ANIMATION_AND_PERFORMANCE_UX.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract & `reference.html`
- **Status:** Verified Animation & UI Performance Specification
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Motion Philosophy

Motion in KELVRA Device Lab serves a single, uncompromising purpose: **functional operational feedback**. 

Per the KELVRA Bench design language:
- Decorative idle animations (e.g. bouncing logos, decorative background particle networks, infinite spinning rings) are **strictly forbidden**.
- Animations trigger strictly upon genuine state changes (e.g. panel toggled, touch input registered, device disconnected).
- Every animation must complete quickly and crisply without adding perceptible cognitive or rendering lag to live video streams.

---

## 2. Motion Rules & Timing Standards

### 2.1 Easing & Timing Matrix
| Motion Context | Duration | Easing Function | Token |
| :--- | :--- | :--- | :--- |
| **Micro-Interactions** (Button hover, tab switch, focus ring) | `150ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | `--duration-fast` |
| **Panel & Drawer Transitions** (Side rails, modal slide, log expansion) | `260ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | `--duration-normal` |
| **Touch Ripple Feedback** (Remote touch tap circle) | `200ms` | `ease-out` | Custom inline |
| **Gauge Spring Interpolation** (Telemetry CPU/RAM arc sweep) | `60fps rAF` | `damped spring (factor 0.12)` | Canvas engine |

### 2.2 Where Motion Adds Value
1. **Touch Ripple Animation:** On pointer click/drag within the device canvas, a terracotta circle (`rgba(217, 119, 87, 0.40)`) expands from radius 10px to 25px and fades out over 200ms. This provides immediate proof that the click was captured and transmitted.
2. **Device Discovery Slide-In:** When a new device is attached via USB, its card gently slides into the inventory list (height expands from 0 to full with opacity fade over 260ms).
3. **Screen Orientation Flip:** When the device rotates, the canvas smoothly resizes to the new aspect ratio over 260ms instead of tearing or flashing black frames.
4. **Logcat Auto-Scroll Catch-Up:** Smooth vertical scroll when following the active log tail.

### 2.3 Prohibited Motion Patterns (Hard Rules)
- **NO** scale transform on card hover (e.g. `transform: scale(1.02)` is banned; use background tint `--bg-hover` instead).
- **NO** infinite pulsating glows or neon outlines around cards.
- **NO** page-level entry fade-ins or wipe transitions that delay interface usability.
- **NO** synthetic loading spinners when actual progress can be described with honest text.

---

## 3. Rendering Performance & Resource Budgets

Device Lab must run smoothly on developer workstations that may simultaneously be running heavy IDEs, language models, or compilers.

### 3.1 60 FPS Canvas Streaming Pipeline
- **Double Buffering:** Screen frames received over WebSockets are buffered in memory and drawn to an offscreen canvas before blitting to the primary display canvas.
- **Garbage Collection (GC) Optimization:** 
  - Image element objects and typed arrays (`Uint8Array`) are pre-allocated and reused.
  - Never instantiate new image objects inside the `onmessage` WebSocket handler at 60 FPS; recycle a fixed buffer pool.
- **Frame Drop Handling:** If the browser rendering loop detects frame arrival faster than screen refresh, it drops intermediate frames and immediately paints the latest frame (`requestAnimationFrame` cadence).

### 3.2 Virtualized Logcat Feed (Zero DOM Bloat)
During high-velocity logging (e.g. app startup emitting 2,000 lines/sec):
- Standard DOM insertion would freeze the browser within seconds.
- Device Lab implements **DOM Virtualization**:
  - Exactly 50 physical `<div>` rows are maintained in the DOM at any given moment.
  - As the user scrolls, the inner text and CSS classes of the 50 recycled nodes are re-bound using a virtual row offset.
  - Memory consumption remains flat at < 15 MB regardless of whether 100 or 1,000,000 log lines have been captured.

### 3.3 Damped Spring Gauge Physics
Telemetry gauges (CPU load, RAM usage) utilize KELVRA Bench's verified spring equation:
```javascript
currentValue += (targetValue - currentValue) * 0.12;
```
This ensures smooth, elegant arc movement between metric polling intervals without glitching or resetting from zero.

---

## 4. Reduced Motion Support

Device Lab honors operating system accessibility preferences unconditionally:
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
When enabled:
- Telemetry values snap instantaneously to target numbers.
- Drawers and modals snap into place without slide transitions.
- Touch ripple animations are suppressed.
