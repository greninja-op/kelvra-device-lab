# Streaming Diagnostics and Telemetry Specification

## 1. Zero-Fabrication Policy

KELVRA Device Lab enforces a strict **Zero-Fabrication Policy** for all telemetry, diagnostics, and performance metrics:
- Frame rates (FPS) must never be hardcoded, simulated, or randomized.
- Latencies must reflect real elapsed timestamps, not placeholder constants.
- If a metric cannot be measured or the stream is paused, the UI displays `0.0 FPS` or `-- ms`, never fake data.

## 2. Real-Time Telemetry Metrics

The stream session tracks operational metrics across its lifecycle:

| Metric | Source | Unit | Description |
|---|---|---|---|
| `fps` | `DeviceStreamSession._fps_timestamps` | frames/sec | Calculated over a rolling 1.0-second sliding window: count of frames captured within `now - 1.0s`. |
| `total_frames` | Monotonic counter | frames | Total count of frames successfully captured and encoded since stream start. |
| `dropped_frames` | Queue overflow counter | frames | Total frames discarded due to client backpressure or queue congestion. |
| `bytes_sent` | Accumulator | bytes | Total payload bytes generated and distributed across all viewer queues. |
| `startup_duration_ms` | Elapsed clock | milliseconds | Time elapsed between `StreamState.PREPARING` and the emission of the first valid frame. |
| `active_viewers` | `len(session.viewers)` | clients | Count of concurrent active WebSocket client connections subscribing to this stream. |
| `reconnect_attempts`| Counter | count | Total automatic reconnect sequences triggered during this stream session. |

## 3. Diagnostic REST API Endpoint

Clients and monitoring harnesses query real-time stream metrics via `GET /api/devices/{serial}/stream/status`.

### Sample Response:
```json
{
  "serial": "emulator-5554",
  "state": "Streaming",
  "fps": 29.8,
  "total_frames": 1420,
  "dropped_frames": 4,
  "bytes_sent": 84920112,
  "startup_duration_ms": 112.5,
  "active_viewers": 2,
  "reconnect_attempts": 0
}
```

If the stream is not running, the endpoint returns:
```json
{
  "serial": "emulator-5554",
  "state": "Idle",
  "fps": 0.0,
  "total_frames": 0,
  "dropped_frames": 0,
  "bytes_sent": 0,
  "startup_duration_ms": 0.0,
  "active_viewers": 0,
  "reconnect_attempts": 0
}
```

## 4. UI Telemetry HUD and Inspector

The Device Viewer Studio panel (`#devices-studio-panel`) presents these diagnostics in two prominent locations:
1. **Header HUD Badges**:
   - Resolution badge (`#studio-hud-res`): Displays native device resolution (e.g. `1080x2400`).
   - Live FPS badge (`#studio-hud-fps`): Displays measured FPS updating in real-time (e.g. `29.8 FPS`).
   - Lease badge (`#studio-lease-badge`): Displays current lease authority (`Read-Only Viewer`, `Exclusive Operator`, or `Locked (<holder>)`).
2. **Diagnostics Inspector Card**:
   - Real-time tabular breakdown of Measured FPS, Frames Sent, Dropped Frames, Bytes Transferred, Startup Duration, and Active Viewers.
   - Live Single-Writer Lease status card with lease holder identity and remaining expiration countdown.
