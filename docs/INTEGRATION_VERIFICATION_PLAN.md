# INTEGRATION_VERIFICATION_PLAN.md
# KELVRA Device Lab — Phase 18 Integration Verification Plan

## 1. Overview and Mission
This document outlines the systematic verification strategy for the Phase 17 integration of KELVRA Device Lab into KELVRA Bench. The goal is to provide rigorous, evidence-based verification across functional compatibility, security boundaries, fault tolerance, performance baselines, and regression prevention.

## 2. Scope of Verification
1. **Module & Service Boundaries**:
   - Out-of-process isolation: KELVRA Device Lab daemon on port 8098; KELVRA Bench orchestrator on port 8099.
   - Sibling isolation: Zero modifications or dependencies on KELVRA Voice (`kelvra-voice/`).
2. **Configuration & Feature Flagging**:
   - `KELVRA_DEVICE_LAB_ENABLED` defaulting to `false`.
   - Dynamic tab and MCP tool behavior under disabled, offline, and online conditions.
3. **Integration Contract**:
   - HTTP bridge API completeness (`/api/device-lab/*` on Bench proxying to `/api/*` on Device Lab).
   - Single-writer lease arbitration and conflict handling (HTTP 409).
   - Coordinate validation and boundary enforcement.
4. **Hardware & Environment Abstraction**:
   - ADB runtime discovery on Windows host.
   - Apple platform capability negotiation and honest limitation handling.
5. **Streaming, Diagnostics & Observability**:
   - Telemetry polling and circular logcat retrieval.
   - Screenshot capture and declarative workflow execution.
6. **Security & Guardrails**:
   - Zero-emoji enforcement.
   - Input coordinate validation, path sanitization, and secret redaction.

## 3. Test Suites & Tooling Matrix
- **Bench Integration Suite**: `Kelvra/kelvra-bench/tests/test_device_lab_integration.py` (FastAPI TestClient, mock transports, offline injection, MCP tool dispatch).
- **Bench Core Regression Suite**: `Kelvra/kelvra-bench/tests/test_ward_gatekeeper.py`, `test_ward_tab.py`, `test_tool_gateway.py`, `test_core.py`.
- **Device Lab Standalone Suite**: `Kelvra/KELVRA Device Lab/tests/` (155 automated unit and integration tests across Android, Apple, AVD, streaming, and observability).
- **Static & Regex Linters**: Python UTF-8 sweep enforcing zero raw Unicode emojis across newly created and modified files.

## 4. Acceptance Criteria
- [x] Zero regressions across preexisting KELVRA Bench test suites.
- [x] 100% pass rate on Device Lab standalone suite (155/155 tests).
- [x] 100% pass rate on Bench integration suite (24/24 tests).
- [x] Safe failure degradation when Device Lab daemon is offline.
- [x] Complete isolation of host execution authority and secrets.
- [x] Zero raw Unicode emojis.
