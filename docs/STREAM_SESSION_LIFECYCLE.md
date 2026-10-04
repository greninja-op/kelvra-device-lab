# Stream Session Lifecycle Specification

## 1. 9-State Stream Lifecycle Model

The screen streamer implements an explicit 9-state finite state machine (`StreamState`) defined in `src/screen_streamer.py`:

```
               +---------------------------------------------------------+
               |                                                         |
               v                                                         |
          +---------+                                                    |
          |  IDLE   |                                                    |
          +---------+                                                    |
               |                                                         |
               | start_stream()                                          |
               v                                                         |
          +-----------+                                                  |
          | PREPARING |                                                  |
          +-----------+                                                  |
               |                                                         |
               | capture worker created                                  |
               v                                                         |
          +----------+           error                                   |
          | STARTING |--------------------------+                        |
          +----------+                          |                        |
               |                                |                        |
               | first frame captured           |                        |
               v                                v                        |
         +-----------+    worker crash    +----------+                   |
   +---->| STREAMING |------------------->|  FAILED  |                   |
   |     +-----------+                    +----------+                   |
   |           |                                                         |
   |           | network dropped                                         |
   |           v                                                         |
   |     +--------------+                                                |
   +-----| RECONNECTING |                                                |
         +--------------+                                                |
               |                                                         |
               | stop requested                                          |
               +-----------------------+                                 |
               |                       |                                 |
               | stop_stream()         |                                 |
               v                       v                                 |
          +----------+           +--------------------+                  |
          | STOPPING |           | DEVICE_DISCONNECTED|                  |
          +----------+           +--------------------+                  |
               |                                                         |
               | background tasks joined                                 |
               v                                                         |
          +----------+                                                   |
          | STOPPED  |---------------------------------------------------+
          +----------+
```

## 2. State Definitions and Transition Contract

| State | Description | Permitted Next States |
|---|---|---|
| `IDLE` | No capture task exists. Zero resource utilization. | `PREPARING` |
| `PREPARING` | Negotiating resolution, validating device authorization, creating capture task. | `STARTING`, `FAILED` |
| `STARTING` | Spawned capture loop; waiting for first valid frame buffer from ADB/codec. | `STREAMING`, `FAILED` |
| `STREAMING` | Actively acquiring frames, calculating rolling FPS, multicasting to viewer queues. | `STOPPING`, `RECONNECTING`, `FAILED`, `DEVICE_DISCONNECTED` |
| `RECONNECTING` | Transient frame capture failure; attempting non-destructive reconnect without tearing down WebSocket subscribers. | `STREAMING`, `FAILED`, `STOPPING` |
| `STOPPING` | Teardown initiated; signaling cancellation to capture task, waiting for worker exit. | `STOPPED` |
| `STOPPED` | Capture task joined, viewer queues flushed, state reset. | `IDLE`, `PREPARING` |
| `FAILED` | Terminal capture error (e.g. ADB daemon crash, unsupported display protocol). | `IDLE`, `PREPARING` |
| `DEVICE_DISCONNECTED` | Device physical USB detachment detected mid-stream. Subscribers alerted with `DEVICE_DISCONNECTED`. | `STOPPED`, `IDLE` |

## 3. Detachment Signal Handling Protocol

When an active device is abruptly unplugged:
1. `DeviceRegistry` or `DeviceManager` receives hardware disconnect event.
2. `screen_streamer.handle_device_disconnect(serial)` is invoked.
3. The stream session transitions immediately to `StreamState.DEVICE_DISCONNECTED`.
4. A broadcast alert is posted to all subscriber queues:
   `{"type": "error", "code": "DEVICE_DISCONNECTED", "message": "Device detached during capture"}`
5. The capture loop terminates and cleans up resources without raising unhandled background exceptions.
6. The session manager revokes all active leases held on the disconnected device.

## 4. Concurrent Stream Collision Handling

If a client requests `POST /api/devices/{serial}/stream/start` while the device is already in `STREAMING` state:
- The server does **not** fail with an error.
- The server returns HTTP 200 with the active stream's current metadata and session status.
- The client connects its WebSocket to the existing stream session, instantly receiving the multicast frames.
- This supports arbitrary read-only multi-observer fan-out without duplicate capture overhead.
