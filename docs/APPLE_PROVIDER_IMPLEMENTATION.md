# Apple Device Provider Implementation Guide
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Architecture & Component Hierarchy

The Apple Device Provider (`AppleDeviceProvider`) serves as the integration bridge connecting Apple physical iOS and iPadOS hardware to KELVRA Device Lab's unified device management architecture.

### 1.1 Class Hierarchy and Contracts

```
               +----------------------------------+
               |        BaseDeviceProvider        |
               |         (src/domain.py)          |
               +----------------------------------+
                                ^
                                | implements
               +----------------------------------+
               |       AppleDeviceProvider        |
               |     (src/apple_provider.py)      |
               +----------------------------------+
                   |              |            |
                   v              v            v
        +------------------+ +---------+ +---------------------+
        | AppleEnvironment | | Product | | Subprocess Boundary |
        |     Detector     | | Mapper  | | (libimobiledevice / |
        |                  | |         | |  pymobiledevice3)   |
        +------------------+ +---------+ +---------------------+
```

`AppleDeviceProvider` satisfies all abstract contract requirements defined in `BaseDeviceProvider`:
- `provider_id`: Unique identifier (`"apple_physical"`).
- `discover_devices()`: Returns a list of standardized `Device` domain model objects.
- `connect_device(device_id)`: Verifies connectivity and updates device status.
- `disconnect_device(device_id)`: Cleans up active sessions or watchers.
- `get_device_health(device_id)`: Returns operational diagnostics, pairing state, and ping latency.

---

## 2. Model Mapping: `AppleDeviceModelMapper`

Apple devices report internal hardware identifiers over lockdown (e.g. `iPhone16,1`, `iPad13,16`) rather than commercial marketing names. To deliver a first-class user experience, `AppleDeviceModelMapper` maintains a comprehensive lookup table:

```python
MODEL_NAMES = {
    # iPhones
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    # iPads
    "iPad13,16": "iPad Air (5th gen)",
    "iPad13,17": "iPad Air (5th gen)",
    "iPad14,3": "iPad Pro 11-inch (4th gen)",
    "iPad14,4": "iPad Pro 11-inch (4th gen)",
    "iPad14,5": "iPad Pro 12.9-inch (6th gen)",
    "iPad14,6": "iPad Pro 12.9-inch (6th gen)",
    "iPad16,3": "iPad Pro 11-inch (M4)",
    "iPad16,5": "iPad Pro 13-inch (M4)",
}
```

If an unknown identifier is encountered, the mapper falls back gracefully to a human-readable format:
- `iPhone18,1` -> `"Apple iPhone (iPhone18,1)"`
- `iPad15,1` -> `"Apple iPad (iPad15,1)"`

---

## 3. Subprocess Isolation for GPL Compliance

To safeguard KELVRA Device Lab from GPL copyleft viral contamination:
1. `pymobiledevice3` and `libimobiledevice` utilities are never imported directly into the Python application runtime.
2. All high-level tooling interactions are dispatched via isolated `subprocess.run` invocations with explicit timeouts:

```python
def _run_cli_command(self, args: List[str], timeout: float = 3.0) -> Optional[str]:
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return None
    return None
```

---

## 4. API Endpoints

The Apple Device Provider registers dedicated REST routes in `src/server.py`:

1. `GET /api/providers/apple/health`:
   Returns host environment diagnostics, usbmux port availability, lockdown directory status, and discovered toolchain.
2. `GET /api/providers/apple/capabilities`:
   Returns the full 12-item capability classification catalog with support levels and notes.
3. `GET /api/devices/{device_id}/apple/trust`:
   Queries the pairing and trust state for an individual Apple device.
4. `POST /api/devices/{device_id}/apple/pair`:
   Triggers a pairing handshake request to prompt the target device for authorization.
