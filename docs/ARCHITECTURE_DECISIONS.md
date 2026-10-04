# KELVRA Device Lab — Architecture Decision Records (ADR)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/ARCHITECTURE_DECISIONS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Authority:** Architecture Review Board
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. ADR-01: Dedicated Standalone Service on Port :8098
- **Context:** Device Lab is being developed concurrently while KELVRA Voice, Bench, and Space operate in sibling directories.
- **Decision:** Run Device Lab as an independent FastAPI service binding to `127.0.0.1:8098`.
- **Rationale:** Guarantees zero port collisions with Bench (:8099), Voice (:8765), Security (:8100), Ward (:8101), Space (:8090), and Agent (:8095). Prevents process interference.
- **Status:** `Approved`.

---

## 2. ADR-02: Zero-Node Vanilla ECMAScript & Canvas Presentation Layer
- **Context:** The frontend requires high-performance frame rendering and styling matching KELVRA Bench.
- **Decision:** Build the standalone web console with vanilla ES6 modules, native CSS custom properties, and HTML5 `<canvas>`, with zero `node_modules` or bundler toolchains.
- **Rationale:** Eliminates hundreds of megabytes of npm dependencies, enables instant file editing without rebuilds, and provides direct GPU pixel control via Canvas 2D/WebGL contexts.
- **Status:** `Approved`.

---

## 3. ADR-03: Two-Tier Hybrid Streaming Architecture
- **Context:** High-refresh video streaming is desirable, but external binaries (like `scrcpy-server`) can complicate initial zero-dependency setup.
- **Decision:** Implement a two-tier streaming pipeline:
  1. *Tier 1 (MVP Baseline):* In-memory JPEG compression over binary WebSocket (15–30 FPS).
  2. *Tier 2 (Release 1.x):* Hardware MediaCodec H.264 video stream via `scrcpy-server` with in-browser WebCodecs decoding (60 FPS baseline, provisional 120 FPS target).
- **Rationale:** Ensures 100% immediate reliability on all Android devices, with a clear upgrade path for ultra-low latency.
- **Status:** `Approved`.

---

## 4. ADR-04: Isolated Managed Subprocess Architecture for Device Toolchains
- **Context:** Background processes (ADB logcat, scrcpy, emulators) can crash or become zombies.
- **Decision:** Manage toolchains as explicit child subprocesses spawned via `asyncio.subprocess` with Windows `CREATE_NO_WINDOW` flags and PID registration.
- **Rationale:** Isolates the main FastAPI server from toolchain crashes and prevents annoying flashing CMD console windows on Windows.
- **Status:** `Approved`.

---

## 5. ADR-05: Single-Writer / Multiple-Reader Lease Model
- **Context:** Multiple clients (e.g. human supervisor and automated testing agent) may view the same device simultaneously.
- **Decision:** Allow unlimited concurrent read-only viewers (telemetry, logcat, video stream), but enforce an exclusive single-writer lease for touch/key injection and test execution.
- **Rationale:** Prevents race conditions and conflicting touch inputs during automated test runs.
- **Status:** `Approved`.

---

## 6. ADR-06: Fire-and-Forget EventBus Bridge to KELVRA Bench
- **Context:** Device Lab must report test results and telemetry to KELVRA Bench without hard coupling.
- **Decision:** Implement an asynchronous HTTP client in `bench_bridge.py` publishing events to Bench's `/api/events` endpoint in a non-blocking fire-and-forget manner.
- **Rationale:** Allows Device Lab to run 100% autonomously when Bench is offline, while automatically streaming events when Bench is active.
- **Status:** `Approved`.

---

## 7. ADR-07: Embedded SQLite with Write-Ahead Logging (WAL)
- **Context:** Need persistent storage for device metadata, test logs, and session history without heavy external database servers.
- **Decision:** Use Python's built-in `sqlite3` engine configured with `PRAGMA journal_mode=WAL;`.
- **Rationale:** Zero external dependencies, high concurrency for background logging, and alignment with Bench's storage architecture.
- **Status:** `Approved`.

---

## 8. ADR-08: Least Privilege User-Space Operation
- **Context:** Accessing mobile hardware often tempts developers to run services as Administrator.
- **Decision:** Strictly enforce non-elevated user-space execution. Device Lab will never require Administrator on Windows or root on Linux.
- **Rationale:** Mitigates the risk of hostile or malformed APKs compromising the developer workstation.
- **Status:** `Approved`.

---

## 9. ADR-09: Explicit Command Allowlisting without Shell String Concatenation
- **Context:** Invocations like `adb shell input text <str>` are vulnerable to shell injection.
- **Decision:** Strictly prohibit shell string formatting (`shell=False`). Use structured argument arrays and reject any shell metacharacters in user inputs.
- **Rationale:** Completely closes command injection attack vectors.
- **Status:** `Approved`.

---

## 10. ADR-10: Dynamic Capability Negotiation via `BaseDeviceProvider`
- **Context:** Physical Android devices, Android emulators, and Apple devices support different features.
- **Decision:** Require all providers to subclass `BaseDeviceProvider` and declare explicit capabilities via `get_capabilities()`.
- **Rationale:** Prevents deceptive simulated features; allows the UI to truthfully enable or disable controls based on what the connected device actually supports.
- **Status:** `Approved`.

---

## 11. ADR-11: Strict GPLv3 Process Boundary for Apple iOS Tooling (`pymobiledevice3`)
- **Context:** `pymobiledevice3` provides pure-Python iOS lockdown and syslog communication, but is licensed under copyleft GPLv3.
- **Decision:** Encapsulate `pymobiledevice3` strictly as an isolated external subprocess CLI worker communicating over standard I/O and JSON pipes. Forbid direct in-process Python imports (`import pymobiledevice3`) within KELVRA core modules.
- **Rationale:** Protects KELVRA proprietary and permissively licensed codebases from viral GPLv3 source distribution obligations while utilizing mature iOS diagnostic capabilities.
- **Status:** `Approved`.

---

## 12. ADR-12: Non-Redistribution Policy for Proprietary Android SDK Toolchains
- **Context:** Device Lab requires ADB and emulator binaries (`adb.exe`, `emulator.exe`), which are covered by Google's proprietary Android SDK License Agreement.
- **Decision:** Do not bundle, redistribute, or package Google Android SDK binaries within Device Lab repositories or distributions. Require the developer to install Android Platform Tools locally.
- **Rationale:** Eliminates legal infringement risks under Google SDK terms and avoids distributing platform-specific binaries.
- **Status:** `Approved`.
