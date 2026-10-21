# KELVRA Device Lab — Automation Execution Security Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/AUTOMATION_EXECUTION_SECURITY.md`
- **Subsystem:** Automation & Observability Subsystem
- **Phase:** Phase 13 — Device Automation, Screenshots, Recordings, Logs & Diagnostics
- **Authority:** Process Isolation, Command Injection Prevention & Safe Execution Sandboxing
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary

Because the Automation Engine accepts arbitrary step definitions and executes commands against operating system bridges (such as the Android Debug Bridge `adb`), strict input validation and defense-in-depth security controls are required. This specification defines the security architecture that guarantees automation workflows cannot escape their execution sandbox, execute unauthorized shell payloads, or destabilize the host workstation.

---

## 2. Input Sanitization & Command Injection Defense

### 2.1 Package Name Sanitation
Unrestricted package parameters in `LAUNCH_APP` or `STOP_APP` could allow shell injection into underlying ADB commands.
- **Enforced Regex Pattern:** `^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$`
- **Rejected Values:** Any string containing whitespace, semicolons (`;`), pipes (`|`), ampersands (`&`), backticks, or subshell expansions (`$()`).

### 2.2 Text Input Escaping
Text characters injected into mobile applications via `TYPE_TEXT` are passed via ADB shell input. The `InputController` strictly escapes characters before process invocation:
```python
escaped_text = (
    text.replace(" ", "%s")
    .replace("\\", "\\\\")
    .replace("'", "\\'")
    .replace('"', '\\"')
    .replace("&", "\\&")
    .replace(";", "\\;")
    .replace("|", "\\|")
    .replace("<", "\\<")
    .replace(">", "\\>")
    .replace("`", "\\`")
    .replace("$", "\\$")
)
```

### 2.3 Coordinate Bounds Verification
To prevent driver crashes or invalid touch inputs, coordinate arguments for `TAP` and `SWIPE` are checked against device metadata:
- Coordinates must satisfy $0 \le x \le \text{screen\_width}$ and $0 \le y \le \text{screen\_height}$.
- Negative coordinates or values exceeding screen boundaries are rejected during pre-execution validation.

---

## 3. Concurrency & Denial-of-Service Defenses

1. **Single-Execution Lock per Target Device:**
   Each target device can only execute a single workflow at any instant. Attempting to flood a device with parallel workflows results in immediate HTTP 400 rejection without queuing unbounded background tasks.
2. **Deterministic Step Timeouts:**
   Every step defaults to a 15-second execution ceiling. No workflow step can hang indefinitely waiting for a stuck UI element or hung application package.
3. **Operator Revocation & Immediate Abort:**
   Workstation operators can abort any ongoing execution via `POST /api/automation/executions/{id}/cancel`. The engine issues an immediate cancellation signal to the active task and releases the device lock.

---

## 4. Single-Writer Lease Compatibility

When an operator holds an active teleoperation lease (`heldLeaseToken`), workflows initiated by that operator must pass the valid session token. Workflows attempting to inject input without a valid lease on a locked device are rejected with an authorization failure.
