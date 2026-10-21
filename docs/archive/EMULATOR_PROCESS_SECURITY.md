# Emulator Process Security, Isolation & Authorization

## 1. Overview
Operating system process execution is the highest-risk capability in KELVRA Device Lab. In Phase 11, the server invokes external binaries (`emulator`, `avdmanager`, `sdkmanager`, `adb`) and handles client requests to create, launch, and delete virtual devices.

Without rigorous controls, this surface is vulnerable to command injection, directory traversal, resource exhaustion, and unauthorized process destruction.

This document details the security architecture and defensive controls protecting the emulator subsystem.

---

## 2. Threat Analysis & Mitigations

| Threat Vector | Attack Scenario | Mitigation in Phase 11 |
|---|---|---|
| **Command Injection** | Malicious shell metacharacters in AVD name (e.g. `Pixel; rm -rf /`) | `shell=False` everywhere; Strict alphanumeric regex validation `^[a-zA-Z0-9_\-\.]+$` |
| **Path Traversal** | Specifying relative traversal tokens (e.g. `../../Windows/System32`) | Explicit rejection of `..`, `/`, `\` in AVD names and path parameters |
| **Subprocess Hijacking** | Forcing the server to launch untrusted binaries | Strict path resolution against discovered SDK directories only; no user-supplied binary paths |
| **Console Telnet Exposure** | Unauthenticated access to the emulator telnet control port (`5554`) | Localhost-only port binding; Android auth token verification (`~/.emulator_console_auth_token`) |
| **Accidental / Malicious Deletion** | Rapid deletion of team test profiles via forged API calls | Mandatory `confirm=true` query parameter; active session lock prevents deletion of running instances |
| **Process Orphanage** | Emulator processes remaining active after server crash or exit | Lifespan shutdown hook `avd_manager.shutdown_all()` terminates all tracked child processes |

---

## 3. Safe Subprocess Execution Standard
All process execution in the AVD subsystem conforms to the following mandatory standards:

1. **No Shell Invocations**:
   - Spawning processes through `shell=True` or cmd.exe wrappers is strictly prohibited.
   - Arguments are always passed as discrete string arrays:
     ```python
     cmd = [emulator_path, f"@{name}", "-port", str(port), "-no-window"]
     proc = await asyncio.create_subprocess_exec(*cmd, stdout=..., stderr=...)
     ```
2. **Explicit Timeouts**:
   - Short-lived commands (`avdmanager`, `adb shell getprop`) enforce strict timeouts (e.g. 10s to 60s).
   - Indefinite blocking calls are forbidden.
3. **Bounded Standard Output / Error Reading**:
   - Buffer sizes are capped to prevent memory exhaustion from verbose log floods.

---

## 4. Emulator Console Port Security
When the Android emulator opens its telnet console on port `5554`, it enforces a token-based authentication mechanism:
1. The emulator reads or generates a cryptographically random secret in `$HOME/.emulator_console_auth_token`.
2. Any telnet client connecting to the console must issue `auth <token>` before issuing commands.
3. In KELVRA Device Lab, direct telnet commands are avoided in favor of the authenticated ADB socket interface (`adb -s emulator-<port> emu kill`), which handles auth token negotiation internally.

---

## 5. Lifespan Cleanup Contract
To ensure that background QEMU processes do not leak when the Device Lab daemon is stopped or restarted:
1. `AvdManager` maintains an in-memory dictionary of running process handles: `_active_sessions: dict[str, EmulatorSession]`.
2. The FastAPI server lifecycle definition binds `avd_manager.shutdown_all()` to the shutdown hook:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       yield
       if avd_manager is not None:
           await avd_manager.shutdown_all()
   ```
3. During server shutdown, all active emulators receive a graceful termination signal, ensuring clean hypervisor teardown and port release.
