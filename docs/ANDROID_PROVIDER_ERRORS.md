# KELVRA Device Lab — Android Provider Errors & Diagnostics (`docs/ANDROID_PROVIDER_ERRORS.md`)

## 1. Error Taxonomy & Classification

All errors originating from ADB subprocess execution, hardware parsing, or state management are classified into structured, strongly typed diagnostic codes:

| Error Code | Origin | Description | Resolution Strategy |
|:---|:---|:---|:---|
| `ADB_NOT_FOUND` | Provider Initialization | No valid `adb` binary found on host system `PATH` or standard SDK directories. | Install Android SDK platform-tools or supply custom path via Settings. |
| `ADB_UNAUTHORIZED` | Hardware Handshake | Device is attached via USB/Wi-Fi but host RSA public key is not trusted. | Unlock physical device screen and tap "Allow USB debugging". |
| `DEVICE_OFFLINE` | Subsystem Communication | ADB daemon communicates with device transport but Android framework is unresponsive. | Replug USB cable, restart device, or run `adb reconnect`. |
| `ADB_STATE_BOOTLOADER` | Hardware State | Device is in Fastboot / Bootloader mode. | Reboot into Android OS (`fastboot reboot`). |
| `ADB_STATE_RECOVERY` | Hardware State | Device is in Recovery console. | Select "Reboot system now" from recovery menu. |
| `ADB_STATE_SIDELOAD` | Hardware State | Device is waiting for an OTA sideload package. | Complete update or reboot device. |
| `ADB_COMMAND_TIMEOUT` | Process Execution | ADB subprocess exceeded 5.0-second execution deadline. | Process terminated with `proc.kill()`; check USB cable or daemon responsiveness. |
| `INVALID_STATE_TRANSITION`| Lifecycle FSM | Attempted an illegal lifecycle transition (e.g. `UNAUTHORIZED` -> `CONNECTED`). | Resolve blocking condition before acquiring connection lease. |

---

## 2. Structured Error Data Model

Errors attached to devices conform to the `DeviceError` schema (`src/domain_model.py`):

```json
{
  "code": "ADB_UNAUTHORIZED",
  "message": "Device is unauthorized. Unlock device screen and tap 'Allow USB debugging' on the RSA prompt.",
  "timestamp": "2026-10-04T01:25:00.123456Z"
}
```

When querying device endpoints (`/api/devices/{id}/properties` or `/api/devices/{id}/display`) for unauthorized or offline hardware, FastAPI returns standardized HTTP problem details:

```json
{
  "detail": "Device android:ABC12345 is unauthorized. Confirm RSA key on physical screen."
}
```

---

## 3. Provider Self-Healing & Diagnostics

1. **Daemon Restart Resilience:** If the ADB server daemon terminates or crashes, `AndroidDeviceProvider` automatically attempts reconnection on the subsequent discovery poll.
2. **Zombie Process Defense:** In the event of command timeouts, the runtime manager executes `proc.kill()` and `proc.wait(timeout=1.0)` to eliminate process table bloat.
3. **Cache Eviction on Detach:** When a device is unplugged, stale properties are purged from memory, preventing incorrect configuration reuse upon reconnecting different hardware.
