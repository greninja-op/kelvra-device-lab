# Android Remote Input Control Specification

## 1. Supported Input Methods

The input injection subsystem (`InputController` in `src/input_controller.py`) exposes programmatic remote control over attached Android devices.

| Method | Target Android Command | Parameters | Precondition |
|---|---|---|---|
| **Tap** | `input tap <x> <y>` | `x: int`, `y: int` | Coordinate within display bounds `[0, W-1]`, `[0, H-1]`; valid writer lease token. |
| **Swipe / Drag** | `input swipe <x1> <y1> <x2> <y2> <duration_ms>` | `x1, y1, x2, y2: int`, `duration_ms: int` | Both start and end coordinates within display bounds; duration in `[50, 5000]ms`; valid writer lease token. |
| **Long Press** | `input swipe <x> <y> <x> <y> <duration_ms>` | `x, y: int`, `duration_ms >= 500` | Coordinates within display bounds; valid writer lease token. |
| **Hardware Key** | `input keyevent <KEYCODE>` | `key: str` | Valid key name; valid writer lease token. |
| **Text Typing** | `input text "<sanitized_string>"` | `text: str` | Shell-escaped string; valid writer lease token. |

## 2. Key Code Mapping Table

Hardware buttons are mapped to Android standard keyevent integers:

| Key Name | Android Keycode Constant | Integer Value | Description |
|---|---|---|---|
| `BACK` | `KEYCODE_BACK` | 4 | System back button / gesture |
| `HOME` | `KEYCODE_HOME` | 3 | Return to launcher home screen |
| `APP_SWITCH` / `RECENTS` | `KEYCODE_APP_SWITCH` | 187 | Open recent applications carousel |
| `POWER` | `KEYCODE_POWER` | 26 | Wake display or trigger power menu |
| `VOLUME_UP` | `KEYCODE_VOLUME_UP` | 24 | Increment system volume |
| `VOLUME_DOWN` | `KEYCODE_VOLUME_DOWN` | 25 | Decrement system volume |

## 3. Coordinate Bounds Validation Contract

To prevent out-of-bounds input execution, all tap and swipe endpoints perform strict range validation before sending ADB commands:
1. `InputController` inspects the target device's native resolution `(screen_width, screen_height)`.
2. Negative coordinates (`x < 0` or `y < 0`) are rejected immediately with HTTP 400 (`Bad Request`).
3. Out-of-bounds coordinates (`x >= screen_width` or `y >= screen_height`) are rejected immediately with HTTP 400 (`Bad Request: Coordinates out of screen bounds`).
4. If resolution metadata is unavailable on a device, inputs are validated against non-negative constraint (`x >= 0, y >= 0`).

## 4. Text Sanitization and Shell Injection Defense

Directly executing `input text` via ADB shell introduces shell injection risks if characters like `;`, `&`, `|`, `'`, `"`, or `$()` are included.

KELVRA Device Lab enforces a strict sanitization protocol:
1. In Android ADB `input text`, spaces must be formatted as `%s` or escaped.
2. Shell metacharacters (`\`, `'`, `"`, `$`, `;`, `&`, `|`, `<`, `>`, '`') are preceded by a backslash escape or converted safely.
3. Whitespace characters: spaces are replaced with `%s`.
4. Resulting string is safely quoted and dispatched via `adb shell input text "<escaped_text>"`.

## 5. Security and Authorization Enforcement

Every input method requires:
1. **Device Authorization Check**:
   The target device must be registered and must NOT be in `UNAUTHORIZED` or `UNAVAILABLE` state. Attempting input on an unauthorized device returns HTTP 403 (`Forbidden`).
2. **Single-Writer Lease Exclusivity Check**:
   If an operator lease is held on the device, the incoming request must present the matching `session_token`.
   - Missing or mismatching lease token returns HTTP 409 (`Conflict: Device is exclusively locked by session '<client_id>'`).
   - If no lease is held, requests without a token are rejected with HTTP 403 requiring lease acquisition.
