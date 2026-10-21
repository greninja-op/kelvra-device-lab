# KELVRA Device Lab — Project State (`docs/PROJECT_STATE.md`)

## 1. Project Identity
- **Project Name:** KELVRA Device Lab
- **System Role:** Standalone mobile device teleoperation, screen streaming, telemetry, and automated testing laboratory for physical and virtual Android and Apple devices.
- **Assigned Workspace Directory:** `Kelvra/KELVRA Device Lab/`
- **Independent Git Repository:** `https://github.com/greninja-op/kelvra-device-lab.git`
- **Current Git Branch:** `main`
- **Dedicated Service Port:** `:8098`
- **Eventual Integration Destination:** KELVRA Bench (`Kelvra/kelvra-bench/`) — Deferred until explicit user authorization
- **Assigned Coordination Channel:** Terminal 1 in `Kelvra/sessions/SESSIONS.md` and `Kelvra/.kelvra-session.md`
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 2. Current Phase
- **Current Phase:** Phase 24 — Implementation Review & Regression Verification
- **Phase Status:** COMPLETE (`REVIEW PASSED`)
- **Review Summary:** Full verification and regression audit of Phase 23 deliverables completed:
  1. Daemonization Assets Audit: `deploy/kelvra-device-lab.service` and `deploy/install_windows_service.bat` verified correct, secured, and syntactically sound.
  2. Pre-Flight Script Audit: `deploy/deploy_check.py` executed live with exit code 0 (`[DEPLOYMENT READY]`).
  3. Multi-Device Soak & Concurrency Audit: `tests/test_phase23_soak_concurrency.py` verified (6/6 passing in 2.55s).
  4. Zero Regression Verification: Standalone suite (161/161 passed in 31.08s), Bench integration suite (24/24 passed in 4.76s); total 185/185 passed (100% pass rate).
  5. Packaging Audit: Verified `dist/kelvra_device_lab-1.0.0-py3-none-any.whl` (127,719 bytes).
  6. Zero Defect Ledger: 0 open defects (P0: 0, P1: 0, P2: 0, P3: 0).
  7. Zero Emoji Rule: 100% verified (0 raw Unicode emojis across all files).
  8. Review Outcome: `REVIEW PASSED`.

---

## 3. Completed Work (Phases 14–24 Deliverables)
- [x] **Phase 14 — Performance Hardening & Reliability:** Complete & Verified.
- [x] **Phase 15 — Standalone System Testing & Acceptance:** Complete & Verified.
- [x] **Phase 16 — Integration Preparation & Controlled Synchronization:** Complete & Verified.
- [x] **Phase 17 — Controlled KELVRA Device Lab Integration:** Complete & Verified.
- [x] **Phase 18 — Integration Verification, Regression & Stabilization:** Complete & Verified.
- [x] **Phase 19 — Release Readiness & Standalone Release Preparation:** Complete & Verified.
- [x] **Phase 20 — Release Candidate Validation & Final Acceptance:** Complete & Verified.
- [x] **Phase 21 — Post-Acceptance Handoff & Maintenance Readiness:** Complete & Verified.
- [x] **Phase 22 — Roadmap & Next-Stage Planning:** Complete & Verified.
- [x] **Phase 23 — Priority Implementation & Verified Progress:** Complete & Verified.
- [x] **Phase 24 — Implementation Review & Regression Verification:** Complete & Verified.

---

## 4. Pending Work (Upcoming Phases)
- **Phase 25 — Next-Priority Implementation & Verification:** Ready for initiation upon explicit user authorization (Horizon 2: WebCodecs H.264 60 FPS Teleoperation Pipeline).

---

## 5. Confirmed Decisions
1. **Dedicated Project Boundary:** All files reside strictly within `Kelvra/KELVRA Device Lab/`.
2. **Dedicated Port :8098:** Eliminates port collisions with sibling services (`:8099`).
3. **Bench Aesthetic Compliance:** Full alignment with KELVRA Bench palette (`#262624`, `#1E1E1C`, `#D97757`, Lora, Inter, JetBrains Mono, zero emojis).
4. **Two-Tier Streaming Strategy:** Zero-dependency JPEG WebSocket baseline for MVP; opt-in 60 FPS WebCodecs H.264 (`scrcpy-server`) for Release 1.x.
5. **GPLv3 Subprocess Isolation:** `pymobiledevice3` runs strictly in an isolated subprocess CLI boundary; zero in-process Python imports in KELVRA core.
6. **Non-Redistribution of Android SDK:** Rely on host-installed platform-tools (`adb.exe`, `emulator.exe`); never bundle proprietary Google binaries.
7. **Single-Writer Lease Exclusivity:** Unlimited concurrent stream viewers; exactly one exclusive single-writer lease for input injection and automated test runs.
8. **Subprocess Sandboxing:** Strict allowlist of binaries, prohibition of shell invocation (`shell=False`), hard timeouts, 64 KB output bounding, and process killing.
9. **Aspect Ratio Preservation:** Viewport letterbox/pillarbox algorithm inside `--bg-panel` (`#1A1918`); zero stretch.
10. **Vanilla ES6 Architecture:** Zero third-party frontend frameworks or build steps; native browser execution.
11. **Zero Personal Data Extraction:** Safe hardware/OS metadata only; zero access to accounts, SMS, contacts, camera, or personal documents.
12. **Zero Fabricated Metrics:** Measured rolling window FPS and timestamps only; zero simulated or fake rates.
13. **Headerless INI Parser:** Specialized parser parsing line-by-line key-value pairs without standard parser header crashes.
14. **Non-Interactive AVD Creation:** Subprocess stdin automation piping `b"no\n"` to bypass interactive custom profile CLI prompts.
15. **Single Device Registry Integration:** Booted emulators register directly as `ANDROID_VIRTUAL` in `AVAILABLE` state for immediate streaming.
16. **Apple Host usbmux Integration:** Native Windows AMDS daemon connectivity on TCP port 27015 + `%ProgramData%\Apple\Lockdown` record parsing.
17. **Apple Streaming Feasibility Posture:** Non-deceptive Inspection Mode on Windows; zero fabricated streaming players or fake touch injection.
18. **Apple Model Mapping Standard:** 30+ iPhone/iPad product types mapped to commercial labels via `AppleDeviceModelMapper` with robust fallback.
19. **Apple Pairing State FSM Mapping:** Passcode-locked and unconfirmed trust states map directly to `UNAUTHORIZED` with clear remediation instructions.
20. **Artifact Storage Quota & LRU Pruning:** 500 MB default workstation quota with automated LRU eviction of oldest assets on capacity threshold breach.
21. **Automation Concurrency Isolation:** Single-runner execution lock per device rejecting concurrent runs with HTTP 400.
22. **iOS Observability Truthful Posture:** Honest HTTP 400 rejection for iOS screen recordings and screenshots on Windows host without deceptive simulation.
23. **Log Credential Redaction Standard:** Strict inline regex scrubbing of Bearer tokens, passwords, API keys, and session tokens before memory buffer ingestion.
24. **Hybrid Out-of-Process Architecture:** Approach 4 implemented preserving standalone teleoperation on `:8098` and communicating via async HTTP/WS adapter.
25. **Bench Feature Flag Isolation:** `KELVRA_DEVICE_LAB_ENABLED=true/false` providing instant zero-downtime rollback.
26. **PEP 517/621 Packaging Standard:** Modern `pyproject.toml` metadata defining dependencies, wheel build system, and scripts.
27. **Dual-Path Static Asset Resolution:** Runtime fallback inspecting relative repository path and installed package directory.
28. **Multi-Launcher Execution Suite:** Root launchers (`run_standalone.py`, `.bat`, `.sh`) enabling zero-configuration execution.
29. **Release Candidate Traceability Standard:** Wheel cryptographic hash, file manifests, and live subprocess verification required for acceptance.
30. **Post-Acceptance Maintenance Governance Policy:** Standardized pre-task context recovery, test verification, zero-emoji sweeps, and change isolation.
31. **3-Horizon Roadmap & Phase 23 Contract:** Structured trajectory across Immediate (Daemonization & Soak), Next (WebCodecs 60 FPS), and Later (macOS & Enterprise RBAC).

---

## 6. Current Repository State
- **Directory:** `Kelvra/KELVRA Device Lab/`
- **Git Branch:** `main`
- **Remote Origin:** `https://github.com/greninja-op/kelvra-device-lab.git`
- **Working Tree:** Complete standalone application shell, navigation, device inventory, production-hardened Android Physical Device Provider, screen streaming, single-writer leasing, remote input injection, AVD management, iOS/iPadOS physical device integration foundation, Phase 13 device automation, screenshots, recordings, logs & diagnostics, Phase 14 hardening, Phase 15 system acceptance, Phase 16 integration readiness deliverables, Phase 17 controlled integration implementation, Phase 18 integration stabilization, Phase 19 release packaging, Phase 20 release candidate validation, Phase 21 maintenance handoff, and Phase 22 roadmap planning; zero unapproved commits or pushes.

---

## 7. Safe Next Action
- Present Phase 22 Roadmap & Next-Stage Planning Report to user and halt execution. Do NOT commit, push, publish, deploy, or begin Phase 23 without explicit user authorization.
