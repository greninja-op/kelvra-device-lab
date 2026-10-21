# KELVRA Device Lab — Maintenance & Change Management Policy

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/MAINTENANCE_CHANGE_POLICY.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Phase:** Phase 21 — Post-Acceptance Handoff & Maintenance Readiness
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Principles of Maintenance

To maintain system integrity, reproducibility, and security, all future modifications to KELVRA Device Lab must adhere to these cardinal rules:

1. **Context First:** Every session or maintenance task must begin by reading [`docs/DEVICE_LAB_CURRENT_STATE.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_CURRENT_STATE.md) and [`docs/DEVICE_LAB_PROJECT_KNOWLEDGE.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/DEVICE_LAB_PROJECT_KNOWLEDGE.md).
2. **Strict Project Boundary:** Writable modifications must remain strictly confined inside `Kelvra/KELVRA Device Lab/` (except when updating the integration bridge in `kelvra-bench/`). Never touch `kelvra-voice` or unrelated repositories.
3. **Evidence-Based Verifiability:** No task or bug fix may be claimed as complete without executing the relevant regression test suite and recording actual outputs.
4. **Zero-Emoji Prohibition:** Absolute prohibition against raw Unicode emojis (`[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]`). Only authentic SVG vector assets are permitted.
5. **Platform Honesty:** Never simulate fake video frames, fake touch responses, or fake telemetry. Rejection responses must be transparent.

---

## 2. Standard Maintenance Workflow

### Step 1: Pre-Maintenance Inspection
Before making any file modifications:
- Verify current repository and branch: `git status -s` in `Kelvra/KELVRA Device Lab/`.
- Confirm working tree is clean and no concurrent agent locks are active in `Kelvra/sessions/SESSIONS.md`.
- Run baseline test suite: `python -m pytest -q` (must show 155 passed).

### Step 2: Bounded Change Implementation
- Restrict modifications to the exact target module or bug fix.
- Preserve existing comments, docstrings, and architectural invariants.
- Ensure external subprocesses continue to invoke with `shell=False` and argument lists.

### Step 3: Regression Verification
- Run standalone regression suite: `python -m pytest -q` in `Kelvra/KELVRA Device Lab/`.
- If integration interfaces were modified, run the Bench integration suite: `python -m pytest -v tests/test_device_lab_integration.py` in `Kelvra/kelvra-bench/`.
- Run the automated emoji regex sweep across all modified files.

### Step 4: Documentation Synchronization
- Update [`docs/PROJECT_STATE.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/PROJECT_STATE.md) and [`docs/IMPLEMENTATION_LOG.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/IMPLEMENTATION_LOG.md).
- Update [`DEVICE_LAB_CURRENT_STATE.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/DEVICE_LAB_CURRENT_STATE.md) in root and `docs/`.
- If an architectural decision changed, record it in [`docs/OPEN_DECISIONS.md`](file:///c:/my%20files%20in%20athuls%20lap/my%20files%20in%20athuls%20lap/projects/PLANNING/Kelvra/KELVRA%20Device%20Lab/docs/OPEN_DECISIONS.md).

### Step 5: Stop Condition
- Present an evidence-based report.
- Do not commit, push, or publish without explicit operator instruction.
