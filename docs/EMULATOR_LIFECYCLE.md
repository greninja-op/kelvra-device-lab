# Android Emulator Lifecycle, Boot Detection & Process Supervision

## 1. Overview
Managing Android emulators requires coordinating operating system process lifecycles, TCP console ports, ADB connection loops, guest operating system boot states, and central Device Registry registration.

This document describes the state machine, launch parameters, asynchronous boot polling loop, and graceful shutdown sequence implemented in KELVRA Device Lab.

---

## 2. Emulator Lifecycle State Machine

```
               [ STOPPED ]
                    |
                    | launch_avd(name)
                    v
              [ LAUNCHING ]  <-- Subprocess spawned, port assigned
                    |
                    | ADB port detects emulator
                    v
               [ BOOTING ]   <-- getprop sys.boot_completed loop
                    |
          +---------+---------+
          |                   |
          v (boot ok)         v (timeout > 180s or process crash)
     [ RUNNING ]          [ ERROR ]
          |
          | stop_avd(name) / server shutdown
          v
     [ STOPPING ]
          |
          v (emu kill / SIGTERM)
     [ STOPPED ]
```

### State Descriptions
1. **STOPPED**: The AVD configuration exists on disk, but no OS process is running.
2. **LAUNCHING**: The `emulator` process has been spawned. Console and ADB ports (`5554`, `5555`) are being allocated.
3. **BOOTING**: The emulator daemon is reachable via ADB, and the guest Linux kernel / Android runtime are initializing. The boot tracking loop polls guest properties.
4. **RUNNING**: Android has emitted `sys.boot_completed=1` and `dev.bootcomplete=1`. The instance is registered into the KELVRA `DeviceRegistry` as `DevicePlatform.ANDROID_VIRTUAL` with state `DeviceLifecycleState.AVAILABLE`.
5. **STOPPING**: Graceful shutdown has been requested via `adb emu kill` or SIGTERM.
6. **ERROR**: The process crashed unexpectedly, exited with a non-zero code, or timed out during the boot sequence.

---

## 3. Port Allocation & Multi-Instance Isolation
Android emulators use paired TCP ports:
- **Odd Port**: ADB daemon transport (e.g. `5555`).
- **Even Port**: Emulator telnet control console (e.g. `5554`).

The canonical ADB serial number is derived directly from the even console port: `emulator-<even_port>` (e.g. `emulator-5554`).

`AvdManager` manages port allocation across multiple concurrent instances:
1. Base port starts at `5554`.
2. Steps in increments of 2 (`5554`, `5556`, `5558`, up to `5584`).
3. Checks local socket availability before assigning a port to avoid port collisions with other local services.

---

## 4. Launch Parameter Matrix
The emulator process is launched with strict flag isolation to ensure headless server compatibility and resource predictability:

```bash
emulator @Pixel_7_API_34 \
  -port 5554 \
  -no-window \
  -no-audio \
  -no-boot-anim \
  -gpu swiftshader_indirect \
  -read-only (optional) \
  -wipe-data (optional)
```

| Parameter | Subsystem Impact |
|---|---|
| `-port <port>` | Fixes the console port deterministically. |
| `-no-window` | Suppresses native host GUI window creation (enables headless server execution). |
| `-no-audio` | Disables audio subsystem emulation, saving host CPU cycles. |
| `-no-boot-anim` | Disables the graphical Android boot animation, accelerating boot time by 30-50%. |
| `-gpu <mode>` | Enforces `swiftshader_indirect` or `host` rendering. |
| `-no-snapshot` | (Optional) Forces a clean cold boot from disk images. |
| `-wipe-data` | (Optional) Formats user data partition before booting. |

---

## 5. Boot Detection Sequence
Once the process is spawned, `AvdManager._track_boot_sequence()` runs as a non-blocking background `asyncio` task:

1. **Phase 1: Process Liveness Check**: Verifies that `proc.poll() is None`. If the process exited immediately, reads stderr and transitions to `ERROR`.
2. **Phase 2: ADB Daemon Detection**: Polls `adb devices` until `emulator-<port>` transitions from `offline` to `device`.
3. **Phase 3: Android Runtime Property Verification**: Periodically executes:
   ```bash
   adb -s emulator-<port> shell getprop sys.boot_completed
   adb -s emulator-<port> shell getprop dev.bootcomplete
   ```
4. **Phase 4: Registry Integration**: When both properties return `1`:
   - Queries model and API level properties.
   - Creates or updates `Device` entry in `DeviceRegistry`.
   - Transitions state to `DeviceLifecycleState.AVAILABLE`.
   - Transitions AVD session to `AvdStatus.RUNNING`.
   - Emits event to active WebSocket viewers.

---

## 6. Graceful Termination & Crash Recovery
When stopping an emulator instance:
1. **Tier 1 (Clean Console Command)**: Executes `adb -s emulator-<port> emu kill`. This requests the emulator hypervisor to flush disk caches, finalize snapshot states, and cleanly exit.
2. **Tier 2 (Graceful Signal)**: If the process does not exit within 5 seconds, issues `proc.terminate()` (SIGTERM).
3. **Tier 3 (Forced Kill)**: If still alive after another 5 seconds, issues `proc.kill()` (SIGKILL).
4. **Registry Cleanup**: Transitions the corresponding device in `DeviceRegistry` to `DeviceLifecycleState.UNAVAILABLE` and removes the active session lock.
