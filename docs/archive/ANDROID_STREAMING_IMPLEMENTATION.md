# Android Screen Streaming Implementation Specification

## 1. Architectural Overview

The KELVRA Device Lab screen streaming pipeline provides real-time, low-latency visual teleoperation for attached Android physical and virtual devices over WebSocket transport. The subsystem decouples frame acquisition from network transmission using an asynchronous multiplexing pipeline with non-blocking backpressure management.

```
+-----------------------------------------------------------------------------+
| Android Physical / Virtual Device (ADB Daemon)                              |
+-----------------------------------------------------------------------------+
                                      |
                                      | exec-out screencap -p / minicap pipe
                                      v
+-----------------------------------------------------------------------------+
| DeviceManager / Provider Capture Worker (Background asyncio Task)          |
+-----------------------------------------------------------------------------+
                                      |
                                      | Decoded / Scaled JPEG Buffer
                                      v
+-----------------------------------------------------------------------------+
| DeviceStreamSession (Capture Loop & Frame Producer)                        |
| - Target Resolution Scaling (480p, 720p, 1080p)                             |
| - Quality Compression Factor (1-100)                                        |
| - Target FPS Rate Limiter (15, 30, 60 FPS)                                  |
| - Real Rolling 1-Second Window FPS Counter                                  |
| - Monotonic Frame Sequence & Byte Counter                                   |
+-----------------------------------------------------------------------------+
                                      |
                 +--------------------+--------------------+
                 |                                         |
                 v                                         v
+-----------------------------------+     +-----------------------------------+
| Viewer Queue 1 (Fast Network)     |     | Viewer Queue 2 (Slow Network)     |
| [ Frame N-1, Frame N ]            |     | [ Frame N (Drop N-1 if Full) ]    |
+-----------------------------------+     +-----------------------------------+
                 |                                         |
                 v                                         v
+-----------------------------------+     +-----------------------------------+
| WebSocket Client: Operator        |     | WebSocket Client: Observer        |
+-----------------------------------+     +-----------------------------------+
```

## 2. Capture Pipeline and Rate Limiting

The capture pipeline is encapsulated within `DeviceStreamSession` in `src/screen_streamer.py`.

### 2.1 Configuration Parameters (`StreamConfig`)
- `max_width: int` (Default: 720): Maximum bounding width for downscaling. Aspect ratio is preserved.
- `quality: int` (Default: 65): JPEG compression quality (1-100).
- `max_fps: int` (Default: 30): Target capture frame rate limit. Frame pacing enforces minimum inter-frame sleep `interval = 1.0 / max_fps`.
- `transport: StreamTransport` (Default: `WEBSOCKET_BINARY`): Transport protocol format.

### 2.2 Adaptive Rate Pacing
Frame pacing is strictly computed with monotonic clock measurements:
```python
start_time = time.monotonic()
# ... frame acquisition and encoding ...
elapsed = time.monotonic() - start_time
sleep_time = max(0.0, frame_interval - elapsed)
if sleep_time > 0:
    await asyncio.sleep(sleep_time)
```
This ensures that slow frame capture does not accumulate negative delays or burst frames onto the network.

## 3. Backpressure and Frame Dropping Policy

To guarantee zero queue bloat and minimum latency for live interactive teleoperation:
1. Each connected WebSocket client has an isolated bounded queue (`asyncio.Queue(maxsize=2)`).
2. When the capture loop generates a new frame, it distributes the frame to all registered viewer queues.
3. If a viewer queue is full (client processing slower than generation rate), the oldest pending frame is dropped immediately:
```python
if queue.full():
    try:
        queue.get_nowait()
        session.dropped_frames += 1
    except asyncio.QueueEmpty:
        pass
queue.put_nowait(frame_data)
```
4. This ensures client latency never exceeds 1-2 frames regardless of client download speed.

## 4. Multi-Viewer Multiplexing Architecture

Device Lab decouples screen capture from client connections:
- Exactly **one** capture loop runs per active device, regardless of whether 1, 5, or 20 clients are observing the stream.
- The single capture loop multicasts encoded JPEG frames to all registered viewer queues.
- Viewers join dynamically via `screen_streamer.add_viewer(serial, queue)` and leave via `remove_viewer(serial, queue)`.
- When the last viewer disconnects and no explicit stream lease is active, the capture loop gracefully stops after an idle timeout to conserve workstation CPU and USB bus bandwidth.

## 5. WebSocket Frame Wire Protocol

The stream WebSocket endpoint is hosted at `/ws/devices/{serial}/stream` and `/ws/devices/{serial}/screen`.

### 5.1 JSON Frame Delivery Payload
Each frame is delivered as a JSON string containing the base64-encoded JPEG image and real-time metrics:
```json
{
  "type": "frame",
  "serial": "emulator-5554",
  "data": "/9j/4AAQSkZJRgABAQE...",
  "fps": 28.5,
  "frame_id": 482,
  "timestamp": 1727984800.124
}
```

### 5.2 Control and Lifecycle Payloads
- **Connection Confirmation**:
  `{"type": "connected", "serial": "emulator-5554", "state": "Streaming", "fps": 30.0}`
- **State Transition Notification**:
  `{"type": "state", "serial": "emulator-5554", "state": "Stopped"}`
- **Error / Detachment Alert**:
  `{"type": "error", "serial": "emulator-5554", "code": "DEVICE_DISCONNECTED", "message": "Device detached during capture"}`
