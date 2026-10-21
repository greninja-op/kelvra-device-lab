# Apple Device Pairing, Trust & Lockdown Security
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. The Apple Trust Model

Connecting an iOS or iPadOS device to a workstation requires mutual cryptographic trust establishment. Apple strictly forbids unauthenticated data transfers over USB to prevent unauthorized data extraction or malicious manipulation.

### 1.1 Mutual Authentication Architecture

```
+-------------------------------------------------------------+
|                      Host Workstation                       |
|                                                             |
|  - Host Certificate: HostCertificate.pem                    |
|  - Host Private Key: HostPrivateKey.pem                     |
|  - System BUID: SystemBUID.plist                            |
+-------------------------------------------------------------+
                               ^
                               | SSL/TLS Handshake
                               v
+-------------------------------------------------------------+
|                     Target Apple Device                     |
|                                                             |
|  - Device Certificate: DeviceCertificate                    |
|  - Root CA Certificate: RootCertificate                     |
|  - Escrow Bag: Encrypted user keys                          |
+-------------------------------------------------------------+
```

When a device connects to a new computer:
1. `lockdownd` generates an ephemeral pairing challenge.
2. The device displays the native system dialog: **"Trust This Computer?"**.
3. The user must unlock the device with their passcode and tap **Trust**.
4. The device signs the host's certificate and writes an encrypted pairing record (`<UDID>.plist`) to the host's lockdown directory.

---

## 2. Pairing State Mapping in KELVRA Device Lab

KELVRA Device Lab maps Apple lockdown authentication responses directly into the unified `DeviceLifecycleState` finite state machine:

| Apple Lockdown Status | `ApplePairingState` | Unified `DeviceLifecycleState` | Error Code | Actionable UI Guidance |
|---|---|---|---|---|
| `Paired` | `PAIRED` | `AVAILABLE` | `None` | Device fully trusted and ready for inspection. |
| `PasscodeLocked` | `PASSCODE_LOCKED` | `UNAUTHORIZED` | `APPLE_PASSCODE_LOCKED` | *"Unlock device passcode to enable communication."* |
| `PairingDialogResponsePending` | `TRUST_REQUIRED` | `UNAUTHORIZED` | `APPLE_TRUST_REQUIRED` | *"Unlock device and tap 'Trust This Computer' on the screen."* |
| `UserDeniedPairing` | `UNPAIRED` | `UNAUTHORIZED` | `APPLE_PAIRING_DENIED` | *"Pairing was rejected on device. Reconnect USB cable to retry."* |
| `Unpaired` | `UNPAIRED` | `UNAUTHORIZED` | `APPLE_UNPAIRED` | *"Device pairing record not found. Pair workstation to proceed."* |

---

## 3. Pairing Verification & Trigger API

### 3.1 Trust State Endpoint
`GET /api/devices/{device_id}/apple/trust`

Response Payload:
```json
{
  "device_id": "00008030-001144A83653C02E",
  "pairing_state": "PAIRED",
  "is_paired": true,
  "is_locked": false,
  "requires_user_action": false,
  "guidance": "Device is trusted and paired with this workstation."
}
```

### 3.2 Pair Trigger Endpoint
`POST /api/devices/{device_id}/apple/pair`

Executes pairing initiation via `idevicepair pair` or native usbmux challenge.
- If the device is unlocked and the user accepts: returns `200 OK` with `pairing_state: "PAIRED"`.
- If the device is locked or awaiting response: returns `400 Bad Request` with an explicit recovery instruction:
  *"Please unlock your iPhone/iPad and tap 'Trust This Computer' on the screen."*

---

## 4. Troubleshooting Pairing Failures

1. **Stale Pairing Certificate**:
   If an iOS device was recently restored or had its location & privacy settings reset, the existing `<UDID>.plist` pairing record becomes invalid.
   - *Resolution*: Delete `%ProgramData%\Apple\Lockdown\<UDID>.plist`, disconnect the USB cable, reconnect, and accept the fresh trust prompt.
2. **Access Denied to Lockdown Directory**:
   If Device Lab is executed under a restricted service account lacking read permissions to `%ProgramData%\Apple\Lockdown`:
   - *Resolution*: Ensure the service account belongs to the `Administrators` or `Authenticated Users` group with read access.
