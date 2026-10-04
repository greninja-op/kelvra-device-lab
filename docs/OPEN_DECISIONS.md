# KELVRA Device Lab — Open Architectural Decisions & Integration Roadmap (`docs/OPEN_DECISIONS.md`)

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/OPEN_DECISIONS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 12 — iOS & iPadOS Capability Investigation and Integration
- **Authority:** Security Review & Architecture Governance
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Confirmed Security & Architectural Decisions

| Decision Topic | Status | Selected Architecture & Security Posture |
|---|---|---|
| **Android Screen Streaming (MVP)** | `Confirmed` | Native ADB screencap + Pillow in-memory JPEG WebSocket server (zero external binaries). |
| **Android Screen Streaming (1.x)** | `Confirmed` | Genymobile `scrcpy-server` H.264 video adapter over forwarded ADB socket with WebCodecs decoding. |
| **Android Input Injection** | `Confirmed` | Native ADB `input` commands for MVP; `scrcpy` binary control socket for Release 1.x. |
| **Shell Invocation Security** | `Confirmed` | 100% prohibition of shell string concatenation (`shell=False`); strict command allowlist. |
| **Device Trust & Pairing** | `Confirmed` | Zero bypass of Android RSA authorization prompts or Apple "Trust This Computer" dialogs. |
| **Session Concurrency Model** | `Confirmed` | Single-Writer Lease exclusivity for control/testing; uncapped concurrent read-only stream viewers. |
| **Stream Lifecycle FSM** | `Confirmed` | Explicit 9-state state machine (`StreamState`) with detachment handling and client error notification. |
| **Rolling Window FPS** | `Confirmed` | 1.0-second sliding window monotonic FPS computation; zero fabricated or simulated rates. |
| **Backpressure Frame Dropping** | `Confirmed` | Bounded viewer queues (`maxsize=2`) dropping stale frames $O(1)$ under network congestion. |
| **Single-Writer Collision Policy** | `Confirmed` | HTTP 409 Conflict returning current lease holder and remaining expiration countdown. |
| **Text Shell Sanitization** | `Confirmed` | Space conversion to `%s` and backslash-escaping of shell metacharacters (`\`, `'`, `"`, `$`, `;`, etc.). |
| **Input Bounds Checking** | `Confirmed` | Non-negative and screen resolution boundary enforcement rejecting out-of-bounds inputs. |
| **Secret Redaction in Streams** | `Confirmed` | Real-time streaming regex scrubbing Bearer tokens, API keys, and passwords to `[REDACTED_SECRET]`. |
| **File Storage Sandboxing** | `Confirmed` | Canonical path resolution jails uploads to `/scratch/` and evidence to `/artifacts/evidence/`. |
| **Process Privileges** | `Confirmed` | Least privilege enforcement: non-elevated user-space execution; never Administrator or root. |
| **Audit Event Retention** | `Confirmed` | Bounded SQLite audit retention: 10,000 events or 30 calendar days max; evidence capped at 2.0 GB. |
| **Bench Integration Model** | `Confirmed` | Autonomous service on `:8098` + non-blocking EventBus bridge (`/api/events`) + embedded workspace panel. |
| **Zero Emoji Policy** | `Confirmed` | 100% strict compliance across code, UI, logs, docs, and commit messages. |
| **Design System Alignment** | `Confirmed` | Strict adoption of Bench tokens (`#262624`, `#1E1E1C`, `#D97757`, Lora, Inter, JetBrains Mono). |
| **Viewport Aspect Ratio** | `Confirmed` | Dynamic pillarbox/letterbox algorithm inside dark container panel (`#1A1918`); zero stretch. |
| **Logcat Virtualization** | `Confirmed` | Fixed 50-row DOM recycling pool sustaining 60 FPS scrolling during 1,000 lines/sec bursts. |
| **Touch Interaction Feedback** | `Confirmed` | 200ms terracotta ripple (`rgba(217, 119, 87, 0.45)`) on pointer click/drag; zero decorative idle motion. |
| **SPA Route Fallback** | `Confirmed` | Explicit FastAPI GET handlers for all 7 navigation routes serving `static/index.html`. |
| **Vanilla ES6 Architecture** | `Confirmed` | Zero third-party frontend dependencies; lightweight `DeviceLabApp` with hash router and toast engine. |
| **Composite Device Identifiers** | `Confirmed` | Format `<platform_prefix>:<serial>` enforced across all boundaries for stability and disambiguation. |
| **10-State Lifecycle FSM** | `Confirmed` | Strict transition table governing `DISCOVERED` through `CONNECTED` and `DISCONNECTED`. |
| **Provider Layer Abstraction** | `Confirmed` | Pluggable `BaseDeviceProvider` interface isolating ADB CLI details from registry. |
| **Thread-Safe Device Registry** | `Confirmed` | Central in-memory registry with RLock guard, auto-reconciliation, and disappearance detection. |
| **Honest Empty States** | `Confirmed` | Zero fake devices or fabricated telemetry; authentic empty state when hardware is absent. |
| **Output Bounding & Process Killing** | `Confirmed` | Hard 5.0s timeout with `proc.kill()` + `proc.wait()`; stdout buffer capped at 64 KB to stop DoS. |
| **Multi-Stage ADB Path Discovery** | `Confirmed` | Constructor path -> `ADB_PATH` env -> system `PATH` -> standard OS platform-tools locations. |
| **Read-Only Property Caching** | `Confirmed` | 60.0-second TTL cache for device metadata with explicit invalidation and disconnect pruning. |
| **Unauthorized Hardware Isolation** | `Confirmed` | REST endpoints for properties and display return HTTP 403 Forbidden until physical RSA acceptance. |
| **AVD INI Parsing Protocol** | `Confirmed` | Custom headerless INI parser extracting key-value pairs without standard parser header crashes. |
| **AVD Creation Non-Interactive Pipeline**| `Confirmed` | Subprocess stdin automation piping `b"no\n"` to bypass interactive custom profile CLI prompts. |
| **AVD Console Port Allocation** | `Confirmed` | Base port 5554 stepping by 2 with active socket availability checks preventing collision. |
| **AVD Single Registry Integration** | `Confirmed` | Booted emulators register directly as `ANDROID_VIRTUAL` in `AVAILABLE` state for immediate streaming. |
| **AVD Deletion Confirmation Safety** | `Confirmed` | Mandatory `confirm=true` query parameter and active session locking preventing accidental disk deletion. |
| **Apple Host usbmux Integration** | `Confirmed` | Native Windows AMDS daemon connectivity on TCP port 27015 + `%ProgramData%\Apple\Lockdown` record parsing. |
| **GPLv3 Licensing Boundary** | `Confirmed` | Zero in-process import of GPLv3 libraries (`pymobiledevice3`); all toolchain operations isolated to CLI subprocesses. |
| **Apple Streaming Feasibility Posture**| `Confirmed` | Non-deceptive Inspection Mode on Windows; zero fabricated streaming players or fake touch injection. |
| **Apple Pairing State FSM Mapping** | `Confirmed` | Passcode-locked and unconfirmed trust states map directly to `UNAUTHORIZED` with clear remediation instructions. |
| **Artifact Storage Quota & LRU Pruning**| `Confirmed` | 500 MB default workstation quota with automatic LRU eviction of oldest assets on capacity threshold breach. |
| **Automation Concurrency Isolation** | `Confirmed` | Single-runner execution lock per device rejecting concurrent runs with HTTP 400. |
| **iOS Observability Truthful Posture**| `Confirmed` | Honest HTTP 400 rejection for iOS screen recordings and screenshots on Windows host without deceptive simulation. |
| **Log Credential Redaction Standard** | `Confirmed` | Strict inline regex scrubbing of Bearer tokens, passwords, API keys, and session tokens before memory buffer ingestion. |
| **Streamer Idle Loop Throttling**     | `Confirmed` | 150ms sleep and bypass of screencap calls when viewer count is 0, eliminating idle CPU thrashing. |
| **Logcat Bounded Ingestion Queue**    | `Confirmed` | Fixed-capacity `collections.deque(maxlen=2000)` guaranteeing O(1) appends and ~2 MB memory cap. |
| **Windows Subprocess Invocation Safety** | `Confirmed` | 100% list-based arguments with `shell=False`, dynamic `.exe` resolution, and kill fallbacks. |
| **Accessible Zero-Emoji Design Standard** | `Confirmed` | Pure SVG vector iconography and WCAG 2.1 AA compliance; strict zero-emoji prohibition enforced. |
| **Hybrid Out-of-Process Architecture** | `Confirmed` | Approach 4 selected: Device Lab runs as autonomous service on `:8098`; Bench connects via async HTTP/WS bridge adapter. |
| **Bench Feature Flag Isolation**       | `Confirmed` | `KELVRA_DEVICE_LAB_ENABLED=true/false` provides instant zero-downtime rollback and graceful offline degradation. |
| **Versioned Integration Contract v1.0**| `Confirmed` | REST, WebSocket, and EventBus (`POST /api/events`) interface formally versioned as immutable v1.0 specification. |
| **Mutual Non-Interference Boundary**   | `Confirmed` | Absolute prohibition against modifying `kelvra-voice` or core `kelvra-bench` modules; zero in-process imports. |
| **Token Translation Security Gate**   | `Confirmed` | Bench global `kbt-*` tokens translate to scoped Device Lab operator roles; unauthorized actions rejected. |
| **Bridge Exception Isolation Boundary** | `Confirmed` | Catching `ConnectError`, `ConnectTimeout`, `TimeoutException`, and `NetworkError` prevents Windows socket connection failures from bubbling into Bench. |
| **Strict Schema Coordinate Bounding**  | `Confirmed` | Normalized `[0.0, 1.0]` coordinates enforced at Bench APIRouter layer before bridge dispatch. |

---

## 2. Open Technical & Design Decisions for Subsequent Phases

### Open Decision 1: Token Auth Mode in Standalone CLI vs Bench Integration
- **Context:** Bench supports both `local` (no auth required on loopback) and `required` (strict `kbt-` token header validation) modes (`KELVRA_BENCH_AUTH_MODE`).
- **Confirmed Resolution:** Default to open localhost loopback for standalone developer ergonomics, enforcing strict `kbt-` header validation when `KELVRA_AUTH_REQUIRED=1` or when accessed outside localhost.

### Open Decision 2: Bundling scrcpy-server.jar vs User-Provided Payload
- **Context:** `scrcpy-server.jar` is an Apache 2.0 pre-compiled Java binary.
- **Current Assessment:** Bundling verified `scrcpy-server-v2.4.jar` inside `assets/` with verified SHA-256 hash provides seamless out-of-the-box performance for Release 1.x without external download friction.

### Open Decision 3: WebCodecs Offscreen Canvas Worker Architecture
- **Context:** WebCodecs H.264 decoding in Release 1.x can run on the main browser thread or inside a Web Worker using `OffscreenCanvas`.
- **Current Assessment:** Standardizing on Web Worker decoding with OffscreenCanvas for Release 1.x, with graceful fallback to main thread for older browser engines.

### Open Decision 4: Multi-Device Concurrency Cap on Workstation Displays
- **Context:** Streaming multiple 60 FPS feeds simultaneously can strain GPU decoding and USB host controller bandwidth.
- **Current Assessment:** Standardize on exactly 1 active high-FPS teleoperation stream in the main studio viewport, with background devices displaying low-rate thumbnail previews (1 frame every 3 seconds) in the inventory grid.

### Open Decision 5: Logcat & Syslog Export Format Standard
- **Context:** Developers and swarm agents benefit from exporting filtered logs for bug reports or PR evidence.
- **Current Assessment:** Provide both raw text export (`.log`) and structured JSON lines (`.jsonl`) with ISO-8601 timestamps and parsed log levels across both Android and Apple platforms in Phase 13.
