# KELVRA Device Lab — Environment Discovery Report (`docs/ENVIRONMENT_DISCOVERY.md`)

## 1. Verified Workspace Root & Structure

- **Workspace Container:** `C:\my files in athuls lap\my files in athuls lap\projects\PLANNING\`
- **KELVRA Root Container:** `C:\my files in athuls lap\my files in athuls lap\projects\PLANNING\Kelvra\`
- **Project Assigned Directory:** `C:\my files in athuls lap\my files in athuls lap\projects\PLANNING\Kelvra\KELVRA Device Lab\`
- **Active Terminal Context:** Terminal 1

The KELVRA root directory is a non-Git container folder containing 10 independent Git repositories, shared automation scripts, and session logs.

---

## 2. Repository Inventory & Branch Boundaries

Each product within `Kelvra/` operates as an independent Git repository with its own `.git` directory, remote, and revision history:

| Subsystem / Project | Local Directory | Default / Current Branch | Remote Origin | Working Tree Status |
|---|---|---|---|---|
| **KELVRA Device Lab** | `Kelvra/KELVRA Device Lab/` | `main` | `https://github.com/greninja-op/kelvra-device-lab.git` | Clean (tracking `origin/main`) |
| **Kelvra Mobile** | `Kelvra/Kelvra Mobile/` | `main` | `https://github.com/greninja-op/kelvra-mobile.git` | 1 uncommitted file (PROTECTED / READ-ONLY) |
| **Kelvra Agent** | `Kelvra/kelvra-agent/` | `main` | `https://github.com/greninja-op/kelvra-agent.git` | Clean (PROTECTED / READ-ONLY) |
| **Kelvra Bench** | `Kelvra/kelvra-bench/` | `main` | `https://github.com/greninja-op/CLI-WORKFLOW.git` | 7 uncommitted data/log files (PROTECTED / READ-ONLY) |
| **Kelvra Security** | `Kelvra/kelvra-security/` | `main` | `https://github.com/greninja-op/kelvra-security.git` | Clean (PROTECTED / READ-ONLY) |
| **Kelvra Skills** | `Kelvra/kelvra-skills/` | `main` | `https://github.com/greninja-op/kelvra-skills.git` | Clean (PROTECTED / READ-ONLY) |
| **Kelvra Space** | `Kelvra/kelvra-space/` | `main` | `https://github.com/greninja-op/kelvra-space.git` | Clean (PROTECTED / READ-ONLY) |
| **Kelvra Voice** | `Kelvra/kelvra-voice/` | `main` | `https://github.com/greninja-op/EchoScribe.git` | 4 uncommitted files (PROTECTED / READ-ONLY) |
| **Kelvra Ward** | `Kelvra/kelvra-ward/` | `main` | `https://github.com/greninja-op/kelvra-ward.git` | Clean (PROTECTED / READ-ONLY) |
| **Marketing Website** | `Kelvra/website/` | `main` | `https://github.com/greninja-op/kelvra-marketing-page.git` | 1 uncommitted file (PROTECTED / READ-ONLY) |
| **Central Monorepo** | Ephemeral staging (`.staging-monorepo`) | `main` | `https://github.com/greninja-op/KELVRA.git` | Managed via `scripts/sync-kelvra-monorepo.ps1` |

---

## 3. Dedicated Service Ports Map

To guarantee strict isolation and eliminate runtime collisions between concurrent terminals:

- `:8765` — KELVRA Voice (FastAPI / sherpa-onnx STT & Piper/Sarvam TTS)
- `:8099` — KELVRA Bench (Swarm orchestrator & Control Room)
- `:5173` — KELVRA Bench Frontend (Vite dev server)
- `:8090` — KELVRA Space (Command centre)
- `:8095` — Kelvra Agent (Autonomous agent runtime)
- `:8100` — Kelvra Security (Screen & audit runtime guard)
- `:8101` — Kelvra Ward (Attestation & release gatekeeper)
- **`:8098` — KELVRA Device Lab** (Allocated standalone port for Device Lab REST & WebSockets)

---

## 4. Environment & Session Coordination File Findings

1. **Environment Security Audit:**
   - Evaluated `.env` and `.env.example` templates across the entire filesystem.
   - Zero private API keys, passwords, or production tokens are present in plain text.
   - Device Lab maintains strictly project-local configuration via `.env.example` inside `Kelvra/KELVRA Device Lab/`.
   - Shared root environment mutations are strictly forbidden.

2. **Session Coordination Files:**
   - `Kelvra/.kelvra-session.md`: Canonical multi-terminal coordination document established at the KELVRA root. Records active projects, working directories, active phases, port allocations, and file boundaries.
   - `Kelvra/sessions.md`: Summary status document linked with `.kelvra-session.md`.
   - `Kelvra/sessions/SESSIONS.md`: Historic append-only log with dedicated sections per terminal (`## Terminal 1`, `## Terminal 2`, `## Terminal 3`). Terminal 1 owns its section exclusively.
   - `Kelvra/CONTEXT.md`: Monorepo-level architecture and status document (v5.13).

---

## 5. Available Development Runtimes & Toolchains

The Windows host environment provides the following verified developer tools:

- **Python:** 3.13.7 (`python.exe` at `C:\Users\Athira Aswin\AppData\Local\Programs\Python\Python313\python.exe`)
- **Android Debug Bridge (ADB):** Version 1.0.41 (Platform-tools 37.0.1 at `C:\Users\Athira Aswin\AppData\Local\Android\Sdk\platform-tools\adb.exe`)
- **Git:** Version 2.45.2.windows.1
- **PowerShell:** Version 5.1 / Core
- **Node.js / npm:** Available for Vite / web bundling

---

## 6. Physical Hardware Discovery via ADB

Running `adb devices -l` reveals a live physical companion device attached via USB:

- **Serial Number:** `8TCABAIFWOZTDICI`
- **Product:** `duchamp_in`
- **Model:** `2311DRK48I` (POCO X6 Pro 5G)
- **Architecture:** `arm64-v8a`
- **OS Level:** Android 14 (API Level 34)
- **Status:** `device` (Authorized and online)
