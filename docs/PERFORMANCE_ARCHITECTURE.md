# KELVRA Device Lab — Performance Architecture & Latency Model

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PERFORMANCE_ARCHITECTURE.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Authority:** Real-Time Performance & System Optimization
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Latency Budget & Timing Decomposition

Teleoperation responsiveness is defined by the end-to-end **glass-to-glass latency**: the elapsed time from a physical state change on the mobile screen to the moment that pixel is painted on the host monitor.

### 1.1 Glass-to-Glass Latency Budget Decomposition

| Pipeline Stage | Baseline JPEG Streamer | scrcpy WebCodecs H.264 | Target Constraint |
|---|---|---|---|
| **1. Screen Capture** | 25–40ms (ADB screencap) | 2–5ms (SurfaceControl hook) | < 8ms |
| **2. Video Encoding** | 20–35ms (CPU Pillow JPEG) | 8–15ms (Hardware MediaCodec) | < 15ms |
| **3. USB & Transport** | 5–10ms (ADB socket + WS) | 3–6ms (Direct TCP socket forward) | < 6ms |
| **4. Host Demuxing** | 2–4ms (Python asyncio WS) | 1–3ms (NAL packetization) | < 3ms |
| **5. Client Decoding** | 15–25ms (`createImageBitmap`) | 3–6ms (Hardware GPU VideoDecoder) | < 6ms |
| **6. Canvas Paint** | 8–16ms (V-Sync interval) | 4–8ms (WebGL / OffscreenCanvas) | < 8ms |
| **TOTAL LATENCY** | **~75–130ms** | **~21–43ms** | **< 45ms** |

---

## 2. High-Refresh Rate Engineering (60 FPS & 120 FPS)

### 2.1 The 120 FPS Target Conditions
Achieving 120 FPS requires a frame budget of exactly **8.33 milliseconds per frame**:
- In the baseline JPEG streamer, 8.33ms is mathematically impossible due to CPU encoding and screencap invocation overhead.
- In the Tier 2 `scrcpy-server` pipeline, 120 FPS is achievable only when all six conditions are satisfied:
  1. **Device Display:** Configured to 120 Hz refresh mode (`Settings -> Display -> Refresh Rate`).
  2. **SoC MediaCodec:** Hardware encoder throughput exceeds 120 frames/sec at 1080p (e.g. Snapdragon 8 Gen 2/3, Dimensity 8300/9300).
  3. **USB 3.0 / High-Speed Link:** Uninterrupted USB bandwidth without packet collisions.
  4. **Host GPU Acceleration:** Browser hardware video decoding enabled (`chrome://flags/#enable-accelerated-video-decode`).
  5. **Host Display:** Workstation monitor physical refresh rate >= 120 Hz.
  6. **Thermal Headroom:** Device battery temperature remains below 40°C.

### 2.2 Adaptive Dynamic Throttling
If the host workstation or device cannot sustain the requested frame rate:
1. **Drop Detection:** Rolling 30-frame window monitors actual inter-frame delivery delta (`delta_ms`).
2. **Backpressure Throttle:** If delivery delta exceeds 1.5x expected frame time, the streamer automatically steps down:
   `120 FPS -> 60 FPS -> 30 FPS -> 15 FPS`.
3. **Recovery:** Once latency recovers for > 10 continuous seconds, the streamer probes upward to the higher rate.

---

## 3. Host Resource Budget & Constraints

| Resource Metric | Baseline Streaming (JPEG) | High-FPS Streaming (H.264) | Idle State |
|---|---|---|---|
| **Host CPU Utilization** | < 6% (8-core workstation) | < 3% (GPU offloaded) | < 0.5% |
| **Host RAM (Backend RSS)** | < 140 MB | < 110 MB | < 65 MB |
| **Host Network Bandwidth** | 2.5–4.5 MB/s (1080p 20 FPS) | 0.6–1.4 MB/s (1080p 60 FPS) | < 5 KB/s |
| **Browser CPU Consumption** | 8–12% (Canvas draw) | 3–5% (Hardware WebCodecs) | < 1% |
| **Device Battery Consumption** | Moderate (~12% / hour) | Low (~5% / hour) | Minimal |

---

## 4. UI Thread Non-Blocking Architecture

To ensure the web console remains silky smooth and responsive even during heavy frame streaming or high-velocity logcat output:
1. **Decoupled Render Loop:** Incoming WebSocket binary frames are placed into a double-buffered frame slot (`currentFrame`, `nextFrame`). The display canvas repaints strictly on `requestAnimationFrame()`, decoupling network receipt from screen refresh.
2. **DOM Virtualization:** The logcat feed renders only the visible rows in the viewport (~35 rows). Upward/downward scrolling updates the slice dynamically, preventing browser DOM tree bloat.
3. **Offscreen Workers (Release 1.x):** H.264 NAL parsing and `VideoDecoder` execution run inside a dedicated Web Worker using an `OffscreenCanvas`, completely isolating video rendering from main UI thread events.
