# Session Isolation and Single-Writer Lease Specification

## 1. Single-Writer Operator Lease Model

KELVRA Device Lab enforces a strict **Single-Writer Operator Lease** concurrency architecture (`SessionManager` in `src/session_manager.py`):
- Any number of clients may connect to a device's screen stream simultaneously in **Read-Only Viewer Mode**.
- Exactly **one** client session may hold **Writer Authority** for a given device at any given moment.
- Writer Authority is required to inject touch events (`tap`, `swipe`, `long_press`), trigger hardware keys (`BACK`, `HOME`, `POWER`), type text, or launch apps.

```
                                  +---------------------------------------+
                                  | Device: android:emulator-5554         |
                                  | State: AVAILABLE / CONNECTED          |
                                  +---------------------------------------+
                                                     |
                         +---------------------------+---------------------------+
                         |                                                       |
                         v                                                       v
        +---------------------------------+                     +---------------------------------+
        | Read-Only Stream Pool           |                     | Single-Writer Lease Authority   |
        | - Viewer Client 1 (Web UI)      |                     | - Held by: operator-web-ui      |
        | - Viewer Client 2 (CI Runner)   |                     | - Token: 7f3a9e...              |
        | - Viewer Client 3 (Observer)    |                     | - Expires: in 285s              |
        | Allowed: View live frames       |                     | Allowed: Inject touch, keys     |
        +---------------------------------+                     +---------------------------------+
```

## 2. Collision Rejection Contract (HTTP 409)

When Client B attempts to acquire an operator lease on a device currently held by Client A:
1. `SessionManager.acquire_lease()` detects an unexpired lease and raises `LeaseConflictError`.
2. The server responds with **HTTP 409 Conflict**:
```json
{
  "detail": {
    "code": "DEVICE_ALREADY_LEASED",
    "message": "Device 'android:emulator-5554' is already leased by 'client-A'.",
    "held_by": "client-A",
    "expires_in_seconds": 240.5
  }
}
```
3. Client B is prevented from overriding or interfering with Client A's session.

## 3. Heartbeat Renewal and Inactivity Timeout

- **Default Inactivity Timeout**: Leases are granted with an initial TTL of 300 seconds (5 minutes).
- **Client Heartbeat**: Active operator clients submit periodic renewal heartbeats via `POST /api/devices/{serial}/lease/renew` every 15-20 seconds.
- **Automatic Expiration**: If a client abruptly closes its browser or crashes without releasing the lease, the lease expires after the TTL. `SessionManager._cleanup_expired_locked()` automatically purges the expired lease and notifies the `DeviceRegistry` to transition the device state back to `AVAILABLE`.

## 4. Forced Revocation and Administrative Override

An administrator or supervisory automation runner can revoke a lease regardless of holder identity:
- Endpoint: `DELETE /api/devices/{serial}/lease?force=true`
- The active lease is revoked immediately.
- The previous holder's subsequent input commands will be rejected with HTTP 409 or HTTP 403.
- The revocation event is logged to the system audit ledger.
