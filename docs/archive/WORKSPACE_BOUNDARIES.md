# KELVRA Device Lab — Workspace Boundaries & Collision Prevention (`docs/WORKSPACE_BOUNDARIES.md`)

## 1. Absolute Isolation Guarantee

KELVRA Device Lab operates as an independent subsystem within the broader KELVRA workspace.
Because multiple terminals run simultaneously against the same filesystem, strict boundaries must be preserved to prevent data loss or build interference.

**Device Lab Allocated Path:**
`C:\my files in athuls lap\my files in athuls lap\projects\PLANNING\Kelvra\KELVRA Device Lab\`

All source code, documentation, tests, static assets, and local configuration must remain inside this folder.

---

## 2. Protected Project Enclaves (Strictly Read-Only)

Under no circumstances may any terminal or agent working on Device Lab touch, stage, format, modify, or delete files inside the following directories:

1. **KELVRA Voice (`Kelvra/kelvra-voice/`):**
   - **Protection Level:** CRITICAL / READ-ONLY
   - **Current State:** 4 uncommitted files in progress by Terminal 1's prior voice phase.
   - **Rule:** Never execute Git commands (`git add`, `git checkout`, `git reset`, `git stash`) targeting Voice files. Do not restart Voice processes on port `:8765`.

2. **KELVRA Bench (`Kelvra/kelvra-bench/`):**
   - **Protection Level:** CRITICAL / READ-ONLY
   - **Current State:** 7 uncommitted files in `data/` and `logs/` representing active swarm and paired device state.
   - **Rule:** Do not edit Bench source code, migration files, or dependency manifests. Device Lab reads Bench files (such as `DESIGN.md` and `data/paired_devices.json`) strictly in read-only mode.

3. **Kelvra Mobile (`Kelvra/Kelvra Mobile/`):**
   - **Protection Level:** HIGH / READ-ONLY
   - **Current State:** Active Kotlin Multiplatform companion codebase.
   - **Rule:** Do not edit Android/iOS source code or Gradle build configurations from Device Lab.

4. **Kelvra Agent, Security, Ward, Space, and Skills:**
   - **Protection Level:** READ-ONLY
   - **Rule:** Treat all sibling directories as immutable external libraries/contracts.

5. **Shared Container Root (`Kelvra/` and `PLANNING/`):**
   - **Protection Level:** READ-ONLY (except canonical coordination files)
   - **Rule:** Do not create ad-hoc root scripts, root packages, or shared node_modules.

---

## 3. Dedicated Service Ports & Process Independence

Each ecosystem subsystem is assigned an exclusive networking port. Device Lab never binds to ports reserved for other services:

- `:8765` — Voice (Protected)
- `:8099` — Bench (Protected)
- `:5173` — Bench Vite Dev Server (Protected)
- `:8090` — Space (Protected)
- `:8095` — Agent (Protected)
- `:8100` — Security (Protected)
- `:8101` — Ward (Protected)
- **`:8098` — KELVRA Device Lab** (Assigned standalone port)

---

## 4. Multi-Terminal Coordination Protocol

Communication across the three development terminals occurs through shared filesystem records, not memory or assumptions:

1. **Canonical Coordination Document:**
   - `Kelvra/.kelvra-session.md` is the canonical multi-terminal coordination file.
   - Each terminal reads this file before beginning work and updates only its assigned section upon completing a milestone.
2. **Session Log:**
   - `Kelvra/sessions/SESSIONS.md` provides historic tracking. Terminal 1 claims and updates `## Terminal 1` exclusively.
3. **Locking Protocol:**
   - Physical lock files in `Kelvra/.kelvra-locks/` are inspected prior to touching shared infrastructure.
4. **Zero Cross-Repository Git Operations:**
   - Git operations (`git add`, `git commit`, `git push`, `git checkout`) must always execute with the working directory set to `Kelvra/KELVRA Device Lab/`. Never run broad commands from the container root.
