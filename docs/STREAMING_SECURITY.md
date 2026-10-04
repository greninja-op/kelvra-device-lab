# KELVRA Device Lab — Video Streaming & Media Security

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/STREAMING_SECURITY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Media Stream Security & Real-Time Channel Protection
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Network Exposure & Binding Boundaries

Live video streaming exposes continuous visual frames of mobile screens that may display authentication tokens, QR codes, or private user interfaces.

### 1.1 Strict Localhost Binding
- **Default Workstation Posture:** Device Lab binds exclusively to loopback interfaces:
  `http://127.0.0.1:8098/` and `ws://127.0.0.1:8098/`
- **No Wildcard Binding:** Binds to `0.0.0.0` or public interface addresses are strictly forbidden during standalone development.
- **Reverse Proxying:** If remote access is required in future releases, it must be established through an authenticated TLS reverse proxy (such as KELVRA Bench's authenticated gateway) rather than exposing Device Lab's raw WebSocket port to the local area network.

---

## 2. WebSocket Stream Authentication & Handshake Verification

Every connection to `/ws/stream/{serial}` undergoes mandatory handshake verification:
1. **Origin Header Check:** WebSockets reject handshakes if the `Origin` header does not match authorized localhost origins (`http://127.0.0.1:*`, `http://localhost:*`).
2. **Scope Verification:** When auth is enabled (`KELVRA_AUTH_REQUIRED=1`), the query parameter `?token=kbt-...` is verified against the KELVRA Bench token store. The token must contain the `device:stream` scope.
3. **Session Expiry Disconnect:** If an active token expires or is revoked during a streaming session, the WebSocket connection is closed with status code `4401` (Unauthorized) and the stream pipeline halts immediately.

---

## 3. Media Artifacts & Screen Privacy Controls

### 3.1 Screenshot Access Security
- Screenshots captured via `POST /api/devices/{serial}/screenshot` are stored locally in the jailed directory `artifacts/evidence/`.
- Download endpoints verify that the requesting client possesses `device:read` scope and enforce canonical path checks to prevent downloading arbitrary host images.

### 3.2 Clipboard Privacy Isolation
- While `scrcpy` and ADB support clipboard synchronization, automatic syncing of the host OS clipboard to the device (or vice versa) is **disabled by default**.
- Automatic clipboard sharing creates an insidious attack vector where passwords or cryptographic keys copied by the developer on the host workstation are inadvertently leaked to mobile applications. Clipboard text can only be transferred via explicit user-initiated text injection.

### 3.3 Stream Resource Exhaustion Mitigations
- **Frame Queue Limits:** The server-side WebSocket frame buffer is capped at **2 frames**. If network backpressure builds up, intermediate non-keyframes are dropped immediately to prevent server memory bloat.
- **Idle Stream Timeout:** If no client heartbeats (`PING`) are received for **60 seconds**, the stream pipeline is automatically halted and the device's video encoder is stopped.
