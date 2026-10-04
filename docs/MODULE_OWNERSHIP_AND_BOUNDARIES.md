# KELVRA Device Lab — Module Ownership & Boundary Governance

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/MODULE_OWNERSHIP_AND_BOUNDARIES.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Boundary Posture:** STRICT MODULAR SEGREGATION
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. System Boundary Architecture

To prevent architectural degradation, coupling entanglement, and regressions, clear system boundaries and ownership domains are established between **KELVRA Bench**, **KELVRA Device Lab**, and the **Host Operating System Environment**.

```
+-----------------------------------------------------------------------------------------+
|                                    KELVRA BENCH                                         |
|                                                                                         |
|  - Swarm Task Dispatch & Card Lifecycle        - Voice & Persona Synthesis Engine       |
|  - Git Worktree Lifecycle & Branch Merges       - Global Authentication (`kbt-*` Tokens) |
|  - Diff Review & Human-in-the-Loop Gates        - Desktop Tauri / Vite Host Shell        |
+-----------------------------------------------------------------------------------------+
                                             |
                                  [ REST / EventBus Link ]
                                             |
+--------------------------------------------v--------------------------------------------+
|                                 KELVRA DEVICE LAB                                       |
|                                                                                         |
|  - Device Registry & State Machines             - Low-Latency Screen Streamer           |
|  - Android Physical / AVD Providers             - Single-Writer Input & Lease Arbiter   |
|  - Apple Host Lockdown Provider                 - Sanitized Circular Logcat Buffer      |
|  - Declarative Automation Step Runner           - Artifact Quota & LRU Manager          |
+-----------------------------------------------------------------------------------------+
                                             |
                                  [ Subprocess Sandboxing ]
                                             |
+--------------------------------------------v--------------------------------------------+
|                               HOST SYSTEM / HARDWARE                                    |
|                                                                                         |
|  - Android SDK Tools (`adb.exe`, `emulator.exe`)                                        |
|  - Apple Mobile Device Service (AMDS / `usbmuxd` on TCP 27015)                          |
|  - USB Host Controllers & Connected Hardware Devices                                   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Granular Ownership Matrix

| Functional Capability | Primary Owner | Secondary / Consumer | Boundary Rule |
|:---|:---:|:---:|:---|
| **Swarm Orchestration** | KELVRA Bench | KELVRA Device Lab | Device Lab NEVER dictates swarm task priorities. It only executes dispatched device steps. |
| **Kanban Task Cards** | KELVRA Bench | KELVRA Device Lab | Device Lab publishes results to Bench EventBus; Bench updates task card status. |
| **Hardware Discovery** | KELVRA Device Lab | KELVRA Bench | Bench queries `/api/devices` or listens to `DEVICE_DISCOVERED` events. Zero direct `adb` calls in Bench. |
| **Device Lease Arbitration** | KELVRA Device Lab | KELVRA Bench | Bench agents must explicitly acquire a lease before sending input control actions. |
| **Screen Streaming Pipeline**| KELVRA Device Lab | KELVRA Bench | Device Lab handles screencap capture and JPEG encoding; Bench embeds the viewer. |
| **Log Scrubbing & Buffer** | KELVRA Device Lab | KELVRA Bench | Secrets are sanitized at Device Lab ingestion before entering the circular buffer. |
| **Artifact Lifecycle** | KELVRA Device Lab | KELVRA Bench | Bench references artifact paths/URLs returned by Device Lab; Device Lab manages 500 MB quota. |
| **Host Tool Execution** | KELVRA Device Lab | N/A | Subprocesses are sandboxed in Device Lab with `shell=False`, timeouts, and allowlisting. |
| **Voice / Speech Subsystems**| KELVRA Bench | N/A | Device Lab has ZERO involvement with TTS/STT or `kelvra-voice`. Absolute non-interference. |

---

## 3. Strict Boundary Rules

### Rule 1: No Direct In-Process Imports
Under no circumstances may KELVRA Bench import Python modules directly from `Kelvra/KELVRA Device Lab/src/` (e.g. `from src.android_provider import AndroidProvider` is strictly forbidden inside Bench). All communication must traverse the network loopback (`http://127.0.0.1:8098`).

### Rule 2: No Direct Hardware Tooling in Bench
KELVRA Bench must never invoke `adb`, `fastboot`, `emulator`, or `usbmuxd` directly from its own subprocess routines. All mobile hardware interactions must route through Device Lab's REST/WebSocket endpoints.

### Rule 3: Single Direction Event Publishing
Device Lab publishes status events outward to Bench via `POST http://127.0.0.1:8099/api/events`. Device Lab does not poll Bench for work; Bench pushes work to Device Lab via `/api/automation/execute-inline`.

### Rule 4: Zero Voice / Audio Subsystem Interference
The `kelvra-voice` repository and Bench's internal `tts_engine.py` / `voice_engine.py` remain entirely untouched. Device Lab does not consume, alter, or reconfigure voice pipelines.

### Rule 5: Non-Escalation of Permissions
Device Lab enforces token validation and single-writer leases on all incoming requests. Even if a Bench swarm agent makes an API call, it cannot bypass lease exclusivity or execute unverified shell commands.
