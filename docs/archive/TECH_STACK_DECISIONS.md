# KELVRA Device Lab — Technology Stack Decisions & Evaluation

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/TECH_STACK_DECISIONS.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Evaluation Criteria:** Architectural fit, performance, security, operational cost, ecosystem compatibility
- **Decision Status Values:** `Approved`, `Provisional`, `Unresolved`
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Stack Evaluation Matrix Summary

| Architectural Domain | Selected Technology | Decision Status | Primary Rationale |
|---|---|---|---|
| **Backend Runtime** | Python 3.13 + FastAPI + Uvicorn | `Approved` | Ecosystem alignment with Bench (:8099) and Voice (:8765); high async concurrency for WebSockets. |
| **Frontend Architecture** | Vanilla ECMAScript Modules + CSS Custom Properties + HTML5 Canvas | `Approved` | 0 MB node_modules footprint; zero compile step; instant hot-reload; native high-DPI canvas. |
| **Video Stream Pipeline (MVP)** | Binary WebSocket + In-Memory JPEG Compression | `Approved` | 100% device compatibility; zero external binary dependencies; sub-120ms latency. |
| **Video Stream Pipeline (1.x)** | `scrcpy-server` MediaCodec + WebCodecs H.264 | `Approved` | Ultra-low latency (< 45ms) and 60 FPS (120 FPS provisional); minimal bandwidth. |
| **Device Subprocess Management** | `asyncio.subprocess` with Windows Process Creation Flags | `Approved` | Clean asynchronous lifecycle; prevents orphan processes; non-blocking I/O. |
| **Local State Store** | SQLite 3 with Write-Ahead Logging (WAL) | `Approved` | Embedded, zero-maintenance, crash-resilient; mirrors Bench's `bench_state.db`. |
| **ADB Protocol Client** | Direct ADB Server Socket Client (`127.0.0.1:5037`) + CLI Fallback | `Approved` | Bypasses process spawning overhead for high-frequency queries; high reliability. |
| **UI Automation Driver (MVP)** | Native ADB Shell (`input tap/swipe`, UIAutomator hierarchy dump) | `Approved` | Zero-dependency baseline; fast execution for smoke tests. |
| **Declarative Automation (1.x)** | Maestro YAML Runner Integration | `Provisional` | Developer-friendly YAML flows; non-flaky accessibility tree assertions. |
| **Apple iOS Client (Windows)** | `pymobiledevice3` over `usbmuxd` | `Approved` | Pure-Python usbmuxd and lockdown protocol client for diagnostics on Windows host. |
| **Testing Framework** | PyTest + pytest-asyncio | `Approved` | Fast, deterministic test discovery; unit, integration, and mock suites. |

---

## 2. Detailed Technology Evaluations

### 2.1 Backend Framework & Runtime
- **Selected Technology:** Python 3.13 with FastAPI and Uvicorn (`src/server.py`).
- **Why It Fits:**
  - Standard runtime across the KELVRA ecosystem (`kelvra-bench`, `kelvra-voice`, `kelvra-security`, `kelvra-ward`).
  - Native asynchronous event loop (`asyncio`) allows thousands of concurrent WebSocket connections and streaming frames with minimal overhead.
  - Automatic OpenAPI / Swagger generation enables rapid integration with Bench agents and tooling.
- **Alternatives Considered:**
  - *Node.js / Express:* Excellent WebSocket performance, but introduces a second major runtime and npm dependency tree into an existing Python-dominated ecosystem.
  - *Go / Gin:* High performance, but increases compilation friction and prevents rapid scriptable iteration by Python-based autonomous agents.
- **Trade-offs:** Python GIL is bypassed through async I/O and multiprocessing/threading for heavy video frame encoding.
- **Operational Cost:** Minimal. Reuses existing host Python 3.13 installation.
- **Security Implications:** Standard ASGI server sandboxed to localhost (`127.0.0.1:8098`).
- **Decision Status:** `Approved`.

---

### 2.2 Frontend Architecture & Presentation
- **Selected Technology:** Vanilla ECMAScript (ES6+) Modules, native CSS Custom Properties, and HTML5 `<canvas>` (`static/index.html`, `app.js`, `style.css`).
- **Why It Fits:**
  - **Zero Node Footprint:** Requires no `npm install`, no `node_modules` (saving hundreds of megabytes), and no bundler (Vite/Webpack) build step during standalone development.
  - **Direct Pixel Control:** HTML5 Canvas provides immediate, unencumbered pixel blitting for screen streaming via `CanvasRenderingContext2D.drawImage` and `createImageBitmap`.
  - **Exact Bench Contract:** Utilizes the exact CSS custom properties specified in `Kelvra/design-reference/reference.html`.
- **Alternatives Considered:**
  - *React / Vue / Svelte:* Introduce substantial build complexity and bundle overhead for what is essentially a focused high-performance hardware viewport.
  - *PyWebView Desktop Wrapper:* Feasible for standalone desktop app, but running in the browser enables simultaneous access by both human developers and headless testing agents.
- **Trade-offs:** Manual DOM manipulation for complex state, mitigated by small component surface area and strict state-driven rendering.
- **Operational Cost:** Zero build time. Files served directly as static assets by FastAPI.
- **Decision Status:** `Approved`.

---

### 2.3 Streaming Transport Engine
- **Selected Technology:** Two-Tier Hybrid Architecture:
  1. *Tier 1 (MVP Baseline):* Binary WebSocket streaming of JPEG compressed frames.
  2. *Tier 2 (Release 1.x):* `scrcpy-server.jar` H.264 video stream over WebSocket with in-browser WebCodecs decoding.
- **Why It Fits:**
  - Provides a guaranteed working baseline that functions immediately on 100% of Android devices without deploying binaries to the device.
  - Upgrades smoothly to sub-45ms latency and 60 FPS (with provisional 120 FPS) via hardware `MediaCodec` once initial stability is verified.
- **Alternatives Considered:**
  - *WebRTC:* Overly complex signaling and peer connection negotiation for a local loopback link.
  - *Raw PNG Streaming:* Unacceptable bandwidth consumption (over 25 MB/s at 1080p).
- **Trade-offs:** JPEG streaming consumes higher CPU on the device than hardware H.264, making the Tier 2 upgrade essential for long-running high-FPS sessions.
- **Decision Status:** `Approved`.

---

### 2.4 Device Process Management
- **Selected Technology:** `asyncio.subprocess` with Windows Process Creation Flags (`CREATE_NO_WINDOW`, `0x08000000`).
- **Why It Fits:**
  - Prevents annoying flashing CMD console windows on Windows when spawning background ADB commands.
  - Ensures clean asynchronous stdout/stderr reading without blocking the server event loop.
  - Enables deterministic PID tracking and process tree termination to prevent zombie ADB/scrcpy processes.
- **Security Implications:** Commands are invoked with explicit argument arrays (`["adb", "-s", serial, "shell", ...]`), strictly forbidding shell string concatenation (`shell=False`).
- **Decision Status:** `Approved`.

---

### 2.5 Local Persistence Store
- **Selected Technology:** Embedded SQLite 3 with Write-Ahead Logging (`WAL` mode).
- **Why It Fits:**
  - Zero-maintenance embedded storage; requires no external database server (Docker, PostgreSQL).
  - WAL mode allows concurrent readers while a background writer updates device telemetry and test logs.
  - Aligns with KELVRA Bench's state architecture (`bench_state.db`).
- **Alternatives Considered:**
  - *Plain JSON Files:* Prone to file corruption during unexpected host power loss or concurrent terminal writes.
- **Decision Status:** `Approved`.
