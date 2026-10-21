# Screen Streaming Performance Analysis & Resolution Tiers

## 1. Resolution and Quality Tiers

KELVRA Device Lab provides three optimized streaming tiers balancing visual fidelity against host workstation CPU and network overhead:

| Tier | Max Width | JPEG Quality | Target FPS | Typical Bandwidth | Workstation Overhead | Intended Use Case |
|---|---|---|---|---|---|---|
| **480p Low Overhead** | 480 px | 55 | 15 - 30 FPS | 400 - 800 Kbps | Minimal (< 3% CPU) | Fleet monitoring, multiple background devices, slow network links |
| **720p Balanced (Default)** | 720 px | 65 | 30 FPS | 1.2 - 2.5 Mbps | Low (~ 5% CPU) | Interactive teleoperation, debugging, automated test observation |
| **1080p High Definition** | 1080 px | 80 | 30 - 60 FPS | 3.5 - 6.0 Mbps | Moderate (~ 10% CPU) | Visual UI regression testing, pixel inspection, media verification |

## 2. Capture Pipeline Latency Breakdown

The teleoperation round-trip latency comprises four stages:

1. **Device Frame Acquisition**:
   - `exec-out screencap -p`: ~60-120ms per frame depending on USB bus and device GPU compositor.
   - Minicap native surface reader (when installed): ~15-30ms per frame.
2. **Host Resizing and JPEG Compression**:
   - Fast bilinear downscaling to target tier width: ~3-6ms.
   - JPEG encoding at specified quality: ~4-8ms.
3. **WebSocket Transmission**:
   - Localhost / LAN transmission of ~40-90 KB frame payload: ~1-3ms.
4. **Client Canvas Rendering**:
   - Browser `Image.onload` and `CanvasRenderingContext2D.drawImage`: ~2-5ms.

Total end-to-end teleoperation latency in the balanced tier is measured at **~80-140ms**, well within interactive operational thresholds.

## 3. Backpressure and Memory Protection

- **Zero Unbounded Buffering**: Viewer queues are bounded to `maxsize=2`. If a client network stutters, stale frames are discarded in constant time $O(1)$.
- **Single Process Encoding**: Encoding occurs exactly once per captured frame. Adding additional viewers does not duplicate CPU encode workloads.
- **Detachment Resource Recovery**: When a device disconnects or all viewers exit, capture loops terminate within 500ms and garbage-collect frame buffers.
