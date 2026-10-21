# KELVRA Device Lab — Session Isolation & Resource Coordination

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SESSION_ISOLATION.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Multi-Session Concurrency & Access Arbitration
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Concurrency Architecture: Single-Writer / Multiple-Reader Pattern

Device Lab supports multiple concurrent users, human supervisors, and autonomous Bench agents viewing fleet state simultaneously. To eliminate command race conditions, input thrashing, and test interference:

```
[Connected Physical Device (e.g. POCO X6 Pro 5G)]
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
[READ-ONLY POOL]         [EXCLUSIVE WRITER LEASE]
- Unlimited Viewers      - EXACTLY ONE Session Holder
- Video Stream (/ws)     - Touch / Swipe / Key Injection
- Telemetry (/api)       - App Install / Launch / Stop
- Logcat Stream (/ws)    - Automation Test Execution
```

### 1.1 Read-Only Viewer Sessions (Uncapped)
- Any authorized client possessing `device:read` / `device:stream` may connect to a device's WebSocket video feed, telemetry stream, and logcat channel.
- Viewing a screen does **not** lock out other engineers or agents from monitoring the device.

### 1.2 Exclusive Writer Lease (Mutually Exclusive)
- Interactive touch teleoperation, text typing, hardware button clicks, APK installations, and automated test runs require an **Exclusive Writer Lease**.
- Exactly **one** client session (`client_id` + `session_token`) may hold the Writer Lease for a given device at any single instant.
- A session cannot inherit, share, or transfer its lease to another session implicitly.

---

## 2. Lease Acquisition, Collision & Preemption Rules

### 2.1 Lease Acquisition
A client requests an exclusive lease via:
`POST /api/devices/{serial}/lease` with payload:
```json
{
  "client_id": "agent-qa-worktree-3",
  "lease_duration_seconds": 120,
  "purpose": "Smoke verification of build 5.23"
}
```
If the device is available (`ONLINE`), the registry grants the lease and transitions device state to `BUSY`.

### 2.2 Collision Handling (When Device Is Already Leased)
If Session B attempts to acquire a lease or send touch/key commands to a device currently held by Session A:
1. The request is immediately rejected with **HTTP 409 Conflict** (`code: DEVICE_ALREADY_LEASED`).
2. The response details who holds the lease and its remaining expiration time:
   ```json
   {
     "success": false,
     "error": {
       "code": "DEVICE_ALREADY_LEASED",
       "message": "Device is locked by 'agent-qa-worktree-3'.",
       "details": {
         "held_by": "agent-qa-worktree-3",
         "expires_in_seconds": 45
       }
     }
   }
   ```
3. Input commands from Session B are silently dropped at the backend input controller boundary.

### 2.3 Administrator Preemption
Only an authorized Local Device Owner or administrative token possessing `device:admin` can explicitly revoke an active lease (`DELETE /api/devices/{serial}/lease?force=true`), terminating the active test and releasing the device.

---

## 3. Heartbeats, Expiration & Automatic Cleanup

- **Heartbeat Requirement:** Lease holders must refresh their lease via WebSocket heartbeat or HTTP ping every **15 seconds**.
- **Automatic Expiration:** If 20 seconds elapse without a heartbeat, the lease automatically expires. The device state transitions back to `AVAILABLE`.
- **Hardware Disconnect Cleanup:** If the physical USB cable is unplugged:
  1. The lease is immediately voided.
  2. The active writer is notified with WebSocket event `DEVICE_UNPLUGGED`.
  3. Video capture sockets and logcat child processes are killed within <= 500ms.
- **Cross-Session Data Leakage Prevention:**
  - When a writer session releases a device or finishes a test run, the `TestRunner` executes a cleanup routine:
    - Stops the target application (`am force-stop`).
    - Clears transient scratch files.
    - Flushes clipboard buffers.
