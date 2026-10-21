# KELVRA Device Lab — Observability & Automation Test Suite Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/OBSERVABILITY_TESTING.md`
- **Subsystem:** Automation & Observability Subsystem
- **Phase:** Phase 13 — Device Automation, Screenshots, Recordings, Logs & Diagnostics
- **Authority:** Verification Protocol, Regression Testing & Test Coverage Matrix
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary

Phase 13 introduces 20 deterministic unit and integration tests implemented in `tests/test_phase13_automation_observability.py`. The suite exercises the artifact management lifecycle, video recording state transitions, credential redaction regexes, diagnostic metric aggregation, workflow execution and cancellation, and all REST endpoints.

Together with earlier phases, the KELVRA Device Lab test suite encompasses **140 automated tests**, executing with a **100% pass rate** in under 55 seconds.

---

## 2. Test Coverage Matrix

| Test Function | Target Component | Verification Objective |
| :--- | :--- | :--- |
| `test_artifact_manager_save_and_retrieve` | `ArtifactManager` | Verifies disk write, path indexing, and binary retrieval. |
| `test_artifact_manager_path_traversal_defense` | `ArtifactManager` | Verifies that paths containing `../../` are stripped and anchored. |
| `test_artifact_manager_deletion_confirmation` | `ArtifactManager` | Verifies deletion raises `ValueError` unless `confirm=True`. |
| `test_artifact_manager_quota_pruning` | `ArtifactManager` | Verifies automated eviction of oldest files when quota is exceeded. |
| `test_recording_lifecycle` | `RecordingManager` | Verifies `IDLE` -> `RECORDING` -> `STOPPED` and MP4 artifact indexing. |
| `test_recording_apple_device_rejection` | `RecordingManager` | Verifies immediate HTTP 400 rejection for Apple iOS devices on Windows. |
| `test_recording_device_disconnect` | `RecordingManager` | Verifies transition to `FAILED` when device hardware disconnects. |
| `test_log_sanitization` | `LogcatService` | Verifies scrubbing of Bearer tokens, passwords, API keys, and session hexes. |
| `test_logcat_history_and_export` | `LogcatService` | Verifies level filtering, tag search, and TXT/JSON artifact generation. |
| `test_diagnostics_service` | `DiagnosticsService` | Verifies aggregation of stream stats, leases, battery, and errors. |
| `test_automation_workflow_validation` | `AutomationEngine` | Verifies schema validation and coordinate bounds checking. |
| `test_automation_workflow_execution` | `AutomationEngine` | Verifies end-to-end multi-step workflow execution and report output. |
| `test_automation_workflow_cancellation` | `AutomationEngine` | Verifies immediate task cancellation and device lock release. |
| `test_api_capture_and_list_screenshots` | REST API | Verifies `POST /api/devices/{serial}/screenshot` and listing. |
| `test_api_apple_screenshot_rejection` | REST API | Verifies HTTP 400 rejection for iOS screenshot requests. |
| `test_api_recording_lifecycle` | REST API | Verifies start, status, and stop recording endpoints. |
| `test_api_device_diagnostics` | REST API | Verifies `GET /api/diagnostics/devices/{serial}` response schema. |
| `test_api_device_logs_and_export` | REST API | Verifies log query, buffer clearing, and export artifact generation. |
| `test_api_automation_workflow_crud_and_inline` | REST API | Verifies workflow creation, inline execution, and report fetching. |
| `test_api_artifacts_download_and_delete` | REST API | Verifies artifact listing, binary download, and confirmed deletion. |

---

## 3. Test Execution Verification

Execution of the full test suite from the repository root:
```bash
python -m pytest -q
```

### Result Summary:
```
........................................................................ [ 51%]
....................................................................     [100%]
140 passed in 54.31s
```
- **Total Test Cases:** 140
- **Pass Rate:** 100%
- **Regressions:** 0
- **Execution Time:** ~54.3 seconds
