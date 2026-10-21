# KELVRA Device Lab — Independent Repository Strategy

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/REPOSITORY_STRATEGY.md`
- **Subsystem:** KELVRA Device Lab
- **Current Git Remote:** `https://github.com/greninja-op/kelvra-device-lab.git`
- **Current Branch:** `main`
- **Umbrella Monorepo:** `https://github.com/greninja-op/KELVRA.git`
- **Planning Mirror:** `PROJECT-PLANNING` (`sync-kelvra.ps1`)
- **Authority:** Standalone Development & Monorepo Synchronization Policy
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview and Core Philosophy

KELVRA Device Lab is developed under an **independent-first lifecycle model**. 

While it is architecturally designated to eventually dock into KELVRA Bench, all primary development, commits, version tags, and feature implementations take place inside its own dedicated folder and Git repository:
- **Dedicated Directory:** `Kelvra/KELVRA Device Lab/`
- **Dedicated Git Repository:** `https://github.com/greninja-op/kelvra-device-lab.git`

This isolation ensures:
1. **Zero Impact on Sibling Work:** Other KELVRA products—most critically KELVRA Voice, which is undergoing active development in a concurrent IDE session—remain completely undisturbed.
2. **Clean, Unpolluted Commit History:** Device Lab commits reflect pure mobile testing and teleoperation domain concerns without being tangled with unrelated Bench, Voice, or Space commits.
3. **Autonomous Validation:** Continuous integration, test suites, and lint sweeps can be run with zero dependency on external orchestrators or running services.

---

## 2. Independent Repository Initialization & Current State

- **Current Repository Status:** The repository has already been initialized inside `Kelvra/KELVRA Device Lab/` with remote `origin` pointing to `https://github.com/greninja-op/kelvra-device-lab.git`.
- **Default Branch:** `main`
- **Initial Baseline Commit:** `e07f617` (Initial foundation architecture, ADB discovery, and control room scaffolding).
- **Prohibition on Unauthorized Remote Actions:** In accordance with user rules, agents must **never** force-push, overwrite remotes, re-initialize, delete branches, or push unverified commits without explicit user instructions and validation gates.

---

## 3. Git History Preservation & Commit-Date Rule

To ensure accurate engineering metrics and historical fidelity across repositories:
1. **True Creation Date Rule (MANDATORY):** Every commit must carry the true creation date of the work (both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`), never the later time it was staged or committed. If work is finalized or committed after an analysis pause, the commit must be timestamped to the date the work was actually performed.
2. **Linear, Atomic History:** Commits must be focused and self-contained (e.g. `feat(stream): implement WebSocket binary frame streamer`, `docs(contract): document Bench design tokens`).
3. **Conventional Commits:** Standard prefixes (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `chore:`) are enforced.
4. **Emoji Prohibition in Commits:** Commit messages must NEVER contain raw Unicode emojis or decorative slop glyphs.

---

## 4. Monorepo Synchronization & Umbrella Mirroring

KELVRA employs a 4-stage synchronization architecture for all independent products. The umbrella monorepo (`https://github.com/greninja-op/KELVRA.git`) serves as an aggregated distribution and reference artifact:

### The 4-Stage Pipeline
1. **Stage 1 — Independent Product Repository:** Commit and push changes directly to `kelvra-device-lab.git` on branch `main` once tests pass.
2. **Stage 2 — Independent Status Verification:** Confirm that `git status` is clean and all unit tests pass with zero regressions.
3. **Stage 3 — Planning Mirror:** Mirror updates to `PROJECT-PLANNING` via `PROJECT-PLANNING/scripts/sync-kelvra.ps1` to preserve multi-project historical tracking.
4. **Stage 4 — Central KELVRA Monorepo Sync:** Synchronize folder contents into the umbrella repository via `Kelvra/scripts/sync-kelvra-monorepo.ps1` (cloud staging with 0 MB persistent local footprint).

*Note: During standalone Phase A through G, synchronization to the central monorepo is performed only when a milestone is completed and explicitly requested.*

---

## 5. Branching Strategy

For standalone development inside `kelvra-device-lab`:
- **`main`:** The authoritative production-ready branch. Every commit on `main` must pass all test suites (unit, integration, zero-emoji lint).
- **`feature/<phase-name>`:** When developing complex multi-step subsystems (e.g. `feature/scrcpy-streaming`, `feature/ios-provider`), work may branch from `main` and be merged via fast-forward or squash merge after comprehensive testing.
- **Git Worktree Isolation:** When executing parallel subagent tasks, agents must employ the `git-worktree` skill to isolate branch working trees under `.worktrees/` rather than modifying the active working tree.

---

## 6. Conflict Prevention & Multi-Session Protection

Because concurrent Anti-gravity sessions operate within `Kelvra/`, strict collision avoidance protocols are active:

### 6.1 Logical Claims via `Kelvra/sessions/SESSIONS.md`
- Every active session/terminal declares its role and logical claims in `Kelvra/sessions/SESSIONS.md` under its assigned section before touching files.
- Device Lab work exclusively claims `Kelvra/KELVRA Device Lab/**`.

### 6.2 Physical Lockfiles via `Kelvra/.kelvra-locks/`
- Prior to wide edits, atomic lockfiles (`.kelvra-locks/<product>.lock`) can be placed.
- Overlapping with another session's lock or `touches:` declaration is strictly prohibited.

### 6.3 Absolute Sibling Protection (Especially KELVRA Voice)
- Under no circumstances may any Git command run from the `Kelvra/` root or modify `kelvra-voice/`, `kelvra-bench/`, `kelvra-security/`, `kelvra-ward/`, or `kelvra-space/`.
- All Git commands (`git status`, `git add`, `git commit`, `git diff`) must be executed with Cwd set strictly to `Kelvra/KELVRA Device Lab/`.

---

## 7. Dependency Boundaries

Device Lab maintains a completely independent dependency manifest:
- **Python Backend:** `Kelvra/KELVRA Device Lab/requirements.txt`
  - FastAPI, Uvicorn, WebSockets, pure-python-adb / adbutils, Pillow, PyTest.
  - Dependencies are installed in Device Lab's dedicated environment; never at the KELVRA monorepo root.
- **Web Frontend:** Self-contained vanilla ECMAScript modules and native CSS tokens in `Kelvra/KELVRA Device Lab/static/` (zero node_modules footprint required for standalone serving, maximizing lightweight portability).
- **No Shared Build Output:** Device Lab build artifacts, pytest caches (`.pytest_cache`), and temporary media reside exclusively inside its folder.

---

## 8. Release Versioning & Integration Pathway (Phase H)

### 8.1 Standalone Semantic Versioning
- `v0.1.x`: Phase A-B (Discovery, Architecture, Design Contract)
- `v0.2.x`: Phase C (Standalone UI & Mock Feeds)
- `v0.3.x`: Phase D (Android physical & virtual device providers)
- `v0.4.x`: Phase E (Full streaming, input control, logcat, test runner)
- `v0.5.x`: Phase F (Comprehensive standalone validation)
- `v1.0.0`: Phase G-H (Validated release ready for KELVRA Bench docking)

### 8.2 Ownership of Future Changes
- Post-integration, `kelvra-device-lab` remains the canonical standalone upstream for device virtualization and testing.
- Bench integration will import Device Lab either as an isolated submodule or a vendored package with dedicated adapter hooks, preserving Device Lab's capability to run as a standalone service at all times.
