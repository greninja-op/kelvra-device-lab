"""
Unit and integration tests for Phase 13:
Device Automation, Screenshots, Recordings, Logs, Diagnostics & Artifact Management.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.server import app, artifact_manager, recording_manager, diagnostics_service, automation_engine, device_registry, mock_provider, device_manager as server_dm
from src.artifact_manager import ArtifactManager, ArtifactType, ArtifactRecord
from src.recording_manager import RecordingManager, RecordingState
from src.diagnostics_service import DiagnosticsService
from src.automation_engine import (
    AutomationEngine,
    ActionType,
    ExecutionStatus,
    WorkflowStep,
    WorkflowDefinition,
)
from src.domain_model import (
    Device,
    DevicePlatform,
    DeviceType,
    DeviceLifecycleState,
    DeviceCapability,
    DeviceError,
)
from src.device_registry import DeviceRegistry
from src.mock_provider import MockDeviceProvider
from src.logcat_service import sanitize_log_message, LogcatService
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus


@pytest.fixture(autouse=True)
def setup_server_test_devices():
    # Register mock-pixel-7 in server device_manager
    mock_dev = DeviceInfo(
        serial="mock-pixel-7",
        model="Pixel 7",
        manufacturer="Google",
        status=DeviceStatus.ONLINE,
        screen_width=1080,
        screen_height=2400
    )
    server_dm.add_mock_device(mock_dev)

    # Register in server mock_provider & device_registry
    dev = Device(
        id="android:mock-pixel-7",
        serial="mock-pixel-7",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel 7 Mock",
        manufacturer="Google",
        model="Pixel 7",
        state=DeviceLifecycleState.AVAILABLE,
        screen_width=1080,
        screen_height=2400,
        capabilities=[
            DeviceCapability.DISCOVERY,
            DeviceCapability.SCREEN_STREAM_JPEG,
            DeviceCapability.SCREENSHOT_CAPTURE,
            DeviceCapability.TOUCH_INTERACTION,
            DeviceCapability.LOGCAT_STREAMING
        ]
    )
    mock_provider.add_device(dev)
    device_registry.reconcile()

    yield

    server_dm.remove_mock_device("mock-pixel-7")
    mock_provider.remove_device("android:mock-pixel-7")
    device_registry.reconcile()


@pytest.fixture
def temp_artifact_dir():
    d = tempfile.mkdtemp(prefix="test_artifacts_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def isolated_artifact_manager(temp_artifact_dir):
    return ArtifactManager(base_dir=temp_artifact_dir, quota_bytes=50 * 1024 * 1024)


@pytest.fixture
def mock_registry():
    reg = DeviceRegistry()
    prov = MockDeviceProvider("test_prov")
    reg.register_provider(prov)

    # 1. Available Android Device
    dev1 = Device(
        id="android:MOCK_P13_01",
        serial="MOCK_P13_01",
        provider_id="test_prov",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel 8 Pro Test",
        metadata={"screen_width": 1080, "screen_height": 2400},
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[
            DeviceCapability.SCREENSHOT_CAPTURE,
            DeviceCapability.SCREEN_STREAM_JPEG,
            DeviceCapability.TOUCH_INTERACTION,
            DeviceCapability.LOGCAT_STREAMING
        ]
    )
    prov.add_device(dev1)

    # 2. Unauthorized Android Device
    dev2 = Device(
        id="android:MOCK_P13_UNAUTH",
        serial="MOCK_P13_UNAUTH",
        provider_id="test_prov",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Locked Device",
        state=DeviceLifecycleState.UNAUTHORIZED,
        error=DeviceError(code="ADB_UNAUTHORIZED", message="RSA unconfirmed")
    )
    prov.add_device(dev2)

    # 3. Apple Physical Device
    dev3 = Device(
        id="apple:00008030-MOCKP13",
        serial="00008030-MOCKP13",
        provider_id="test_prov",
        platform=DevicePlatform.APPLE_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="iPhone 15 Pro Test",
        metadata={"screen_width": 1179, "screen_height": 2556},
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[DeviceCapability.DISCOVERY]
    )
    prov.add_device(dev3)

    reg.reconcile()
    return reg


# ==============================================================================
# 1. Artifact Manager Tests
# ==============================================================================

def test_artifact_manager_save_and_retrieve(isolated_artifact_manager):
    mgr = isolated_artifact_manager
    data = b"sample image payload bytes"
    rec = mgr.save_artifact(
        name="test_screen.jpeg",
        artifact_type=ArtifactType.SCREENSHOT,
        file_format="jpeg",
        data=data,
        device_id="android:MOCK1"
    )

    assert rec.artifact_id.startswith("art-")
    assert rec.file_size_bytes == len(data)
    assert rec.artifact_type == ArtifactType.SCREENSHOT

    retrieved = mgr.get_artifact(rec.artifact_id)
    assert retrieved is not None
    assert retrieved.artifact_id == rec.artifact_id

    file_path = mgr.get_artifact_file_path(rec.artifact_id)
    assert file_path is not None
    assert file_path.exists()
    assert file_path.read_bytes() == data


def test_artifact_manager_path_traversal_defense(isolated_artifact_manager):
    mgr = isolated_artifact_manager
    # Attempting to save with path traversal in name
    rec = mgr.save_artifact(
        name="../../etc/passwd.txt",
        artifact_type=ArtifactType.LOG_EXPORT,
        file_format="txt",
        data=b"malicious payload",
        device_id="android:MOCK1"
    )
    # The file must still be safely stored inside mgr.logs_dir
    file_path = mgr.get_artifact_file_path(rec.artifact_id)
    assert file_path is not None
    assert str(file_path).startswith(str(mgr.base_dir))
    assert ".." not in file_path.name


def test_artifact_manager_deletion_confirmation(isolated_artifact_manager):
    mgr = isolated_artifact_manager
    rec = mgr.save_artifact(
        name="delete_me.txt",
        artifact_type=ArtifactType.LOG_EXPORT,
        file_format="txt",
        data=b"temp content",
        device_id="android:MOCK1"
    )

    # Deletion without confirmation must raise ValueError
    with pytest.raises(ValueError, match="Explicit confirmation"):
        mgr.delete_artifact(rec.artifact_id, confirm=False)

    # Deletion with confirm=True succeeds
    assert mgr.delete_artifact(rec.artifact_id, confirm=True) is True
    assert mgr.get_artifact(rec.artifact_id) is None
    assert mgr.get_artifact_file_path(rec.artifact_id) is None


def test_artifact_manager_quota_pruning(temp_artifact_dir):
    # Quota is 10,000 bytes
    mgr = ArtifactManager(base_dir=temp_artifact_dir, quota_bytes=10000)
    chunk = b"X" * 3000

    # Save 3 chunks = 9,000 bytes
    rec1 = mgr.save_artifact("c1.txt", ArtifactType.LOG_EXPORT, "txt", chunk, "dev1")
    rec2 = mgr.save_artifact("c2.txt", ArtifactType.LOG_EXPORT, "txt", chunk, "dev1")
    rec3 = mgr.save_artifact("c3.txt", ArtifactType.LOG_EXPORT, "txt", chunk, "dev1")

    assert len(mgr.list_artifacts()) == 3

    # Save 4th chunk (3,000 bytes) -> 9,000 + 3,000 = 12,000 > 10,000 quota
    # Prunes oldest artifact (rec1)
    rec4 = mgr.save_artifact("c4.txt", ArtifactType.LOG_EXPORT, "txt", chunk, "dev1")
    assert mgr.get_artifact(rec1.artifact_id) is None
    assert mgr.get_artifact(rec4.artifact_id) is not None
    assert mgr.get_total_size_bytes() <= mgr.quota_bytes


# ==============================================================================
# 2. Recording Manager Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_recording_lifecycle(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    dm.add_mock_device(DeviceInfo(serial="MOCK_P13_01", model="Mock Phone", status=DeviceStatus.ONLINE))

    rm = RecordingManager(dm, isolated_artifact_manager, mock_registry)

    # 1. Start recording
    session = await rm.start_recording("MOCK_P13_01", max_duration_seconds=60)
    assert session.state == RecordingState.RECORDING
    assert session.serial == "MOCK_P13_01"

    # 2. Attempt duplicate start -> raises ValueError
    with pytest.raises(ValueError, match="already actively recording"):
        await rm.start_recording("MOCK_P13_01")

    # 3. Stop recording
    stopped = await rm.stop_recording("MOCK_P13_01")
    assert stopped.state == RecordingState.STOPPED
    assert stopped.artifact_id is not None
    assert stopped.file_size_bytes > 0

    # Artifact is recorded in catalog
    art = isolated_artifact_manager.get_artifact(stopped.artifact_id)
    assert art is not None
    assert art.artifact_type == ArtifactType.RECORDING


@pytest.mark.asyncio
async def test_recording_apple_device_rejection(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    rm = RecordingManager(dm, isolated_artifact_manager, mock_registry)

    # iOS recording must be rejected with clear explanation
    with pytest.raises(ValueError, match="not supported for iOS/iPadOS"):
        await rm.start_recording("apple:00008030-MOCKP13")


@pytest.mark.asyncio
async def test_recording_device_disconnect(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    dm.add_mock_device(DeviceInfo(serial="MOCK_P13_01", model="Mock Phone", status=DeviceStatus.ONLINE))

    rm = RecordingManager(dm, isolated_artifact_manager, mock_registry)
    session = await rm.start_recording("MOCK_P13_01")
    assert session.state == RecordingState.RECORDING

    # Simulate unexpected hardware disconnect
    rm.handle_device_disconnected("MOCK_P13_01")
    updated = rm.get_session("MOCK_P13_01")
    assert updated.state == RecordingState.FAILED
    assert "disconnected while recording" in updated.error_message


# ==============================================================================
# 3. Logcat Service & Sanitization Tests
# ==============================================================================

def test_log_sanitization():
    raw1 = "Authorization header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secretpayload"
    sanitized1 = sanitize_log_message(raw1)
    assert "eyJhbGci" not in sanitized1
    assert "Bearer [REDACTED_SECRET]" in sanitized1

    raw2 = "login request password=supersecretpassword123&username=admin"
    sanitized2 = sanitize_log_message(raw2)
    assert "supersecretpassword123" not in sanitized2
    assert "password=[REDACTED]" in sanitized2

    raw3 = "query url?api_key=ak_live_998877665544332211"
    sanitized3 = sanitize_log_message(raw3)
    assert "ak_live" not in sanitized3
    assert "api_key=[REDACTED]" in sanitized3


def test_logcat_history_and_export():
    dm = DeviceManager()
    ls = LogcatService(dm, buffer_size=100)
    buf = ls.get_or_create_buffer("dev_test_01")

    # Seed 5 entries with different levels
    levels = ["V", "D", "I", "W", "E"]
    for i, lvl in enumerate(levels):
        buf.append({
            "timestamp": f"12:00:0{i}.000",
            "pid": 1000 + i,
            "tid": 0,
            "level": lvl,
            "tag": "TestModule" if i % 2 == 0 else "NetworkEngine",
            "message": f"Log message number {i}",
            "raw": f"raw log line {i}"
        })

    # Query all
    all_logs = ls.get_history("dev_test_01", limit=50)
    assert len(all_logs) == 5

    # Filter level >= W (W, E)
    warn_plus = ls.get_history("dev_test_01", level="W")
    assert len(warn_plus) == 2

    # Filter tag search
    net_logs = ls.get_history("dev_test_01", tag="Network")
    assert len(net_logs) == 2

    # Export text
    exported_text = ls.export_logs("dev_test_01", format_type="text")
    assert "[I] TestModule" in exported_text

    # Export json
    exported_json = ls.export_logs("dev_test_01", format_type="json")
    assert "TestModule" in exported_json

    # Clear buffer
    ls.clear_buffer("dev_test_01")
    assert len(ls.get_history("dev_test_01")) == 0


# ==============================================================================
# 4. Diagnostics Service Tests
# ==============================================================================

def test_diagnostics_service(mock_registry):
    diag = DiagnosticsService(device_registry=mock_registry)
    diag.log_error("android:MOCK_P13_01", "STREAM_ERROR", "Pipeline dropped frame", operation="stream")

    report = diag.get_diagnostics("android:MOCK_P13_01")
    assert report is not None
    assert report.serial == "MOCK_P13_01"
    assert report.lifecycle_state == "available"
    assert report.is_authorized is True
    assert len(report.recent_errors) >= 1
    assert report.recent_errors[0]["error_code"] == "STREAM_ERROR"


# ==============================================================================
# 5. Automation Engine Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_automation_workflow_validation(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    from src.input_controller import InputController
    ic = InputController(dm, device_registry=mock_registry)
    ae = AutomationEngine(mock_registry, ic, isolated_artifact_manager)

    # 1. Invalid: Empty steps
    wf_empty = WorkflowDefinition(name="Empty", target_device="android:MOCK_P13_01", steps=[])
    valid, err = ae.validate_workflow(wf_empty)
    assert valid is False
    assert "at least one step" in err

    # 2. Invalid: Non-existent device
    wf_no_dev = WorkflowDefinition(
        name="NoDev",
        target_device="android:DOES_NOT_EXIST",
        steps=[WorkflowStep(action=ActionType.WAIT, duration_ms=100)]
    )
    valid, err = ae.validate_workflow(wf_no_dev)
    assert valid is False
    assert "not found in registry" in err

    # 3. Invalid: Unauthorized device
    wf_unauth = WorkflowDefinition(
        name="Unauth",
        target_device="android:MOCK_P13_UNAUTH",
        steps=[WorkflowStep(action=ActionType.WAIT, duration_ms=100)]
    )
    valid, err = ae.validate_workflow(wf_unauth)
    assert valid is False
    assert "unauthorized" in err

    # 4. Invalid: Apple touch/key action on Windows
    wf_apple = WorkflowDefinition(
        name="AppleTouch",
        target_device="apple:00008030-MOCKP13",
        steps=[WorkflowStep(action=ActionType.TAP, x=100, y=200)]
    )
    valid, err = ae.validate_workflow(wf_apple)
    assert valid is False
    assert "unavailable on iOS/iPadOS" in err

    # 5. Invalid: Out of bounds coordinates (Pixel 8 Pro is 1080x2400)
    wf_oob = WorkflowDefinition(
        name="OOB",
        target_device="android:MOCK_P13_01",
        steps=[WorkflowStep(action=ActionType.TAP, x=5000, y=9000)]
    )
    valid, err = ae.validate_workflow(wf_oob)
    assert valid is False
    assert "exceed screen resolution" in err

    # 6. Valid workflow
    wf_valid = WorkflowDefinition(
        name="ValidCheck",
        target_device="android:MOCK_P13_01",
        steps=[
            WorkflowStep(action=ActionType.WAIT, duration_ms=50),
            WorkflowStep(action=ActionType.ASSERT_STATE, expected_state="available")
        ]
    )
    valid, err = ae.validate_workflow(wf_valid)
    assert valid is True
    assert err is None


@pytest.mark.asyncio
async def test_automation_workflow_execution(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    dm.add_mock_device(DeviceInfo(serial="MOCK_P13_01", model="Mock Phone", status=DeviceStatus.ONLINE))

    from src.input_controller import InputController
    ic = InputController(dm, device_registry=mock_registry)
    ae = AutomationEngine(mock_registry, ic, isolated_artifact_manager)

    wf = WorkflowDefinition(
        name="SmokeRun",
        target_device="android:MOCK_P13_01",
        steps=[
            WorkflowStep(step_name="Pause briefly", action=ActionType.WAIT, duration_ms=20),
            WorkflowStep(step_name="Tap home button", action=ActionType.KEY, key="HOME"),
            WorkflowStep(step_name="Capture verification screenshot", action=ActionType.SCREENSHOT),
            WorkflowStep(step_name="Assert state is available", action=ActionType.ASSERT_STATE, expected_state="available")
        ]
    )

    report = await ae.execute_workflow(wf)
    assert report.status == ExecutionStatus.RUNNING

    # Wait for completion
    task = ae._active_tasks.get(report.execution_id)
    if task:
        await task

    completed_report = ae.get_execution(report.execution_id)
    assert completed_report.status == ExecutionStatus.COMPLETED
    assert len(completed_report.step_results) == 4
    for step_res in completed_report.step_results:
        assert step_res.status == "PASSED"

    # Screenshot step generated artifact
    screen_step = completed_report.step_results[2]
    assert screen_step.artifact_id is not None
    assert isolated_artifact_manager.get_artifact(screen_step.artifact_id) is not None

    # Report itself is saved as automation report artifact
    assert completed_report.artifact_id is not None
    rep_art = isolated_artifact_manager.get_artifact(completed_report.artifact_id)
    assert rep_art is not None
    assert rep_art.artifact_type == ArtifactType.AUTOMATION_REPORT


@pytest.mark.asyncio
async def test_automation_workflow_cancellation(mock_registry, isolated_artifact_manager):
    dm = DeviceManager()
    from src.input_controller import InputController
    ic = InputController(dm, device_registry=mock_registry)
    ae = AutomationEngine(mock_registry, ic, isolated_artifact_manager)

    # Long workflow with 5-second wait
    wf = WorkflowDefinition(
        name="LongRun",
        target_device="android:MOCK_P13_01",
        steps=[WorkflowStep(action=ActionType.WAIT, duration_ms=5000)]
    )

    report = await ae.execute_workflow(wf)
    assert report.status == ExecutionStatus.RUNNING

    # Immediate cancellation
    cancelled = await ae.cancel_execution(report.execution_id)
    assert cancelled is True

    # Check updated report
    updated = ae.get_execution(report.execution_id)
    assert updated.status == ExecutionStatus.CANCELLED


# ==============================================================================
# 6. REST API Endpoints Tests
# ==============================================================================

@pytest.fixture
def client():
    return TestClient(app)


def test_api_capture_and_list_screenshots(client):
    # Synchronize mock device
    client.get("/api/devices")

    # POST capture screenshot
    res = client.post("/api/devices/android:mock-pixel-7/screenshots", json={"max_width": 720, "quality": 75})
    assert res.status_code == 200
    data = res.json()
    assert "artifact_id" in data
    assert data["artifact_type"] == "SCREENSHOT"
    art_id = data["artifact_id"]

    # GET list screenshots for device
    res_list = client.get("/api/devices/android:mock-pixel-7/screenshots")
    assert res_list.status_code == 200
    screens = res_list.json()
    assert any(s["artifact_id"] == art_id for s in screens)


def test_api_apple_screenshot_rejection(client):
    # Register mock Apple device in registry
    dev = Device(
        id="apple:00008030-API-TEST",
        serial="00008030-API-TEST",
        provider_id="apple_physical",
        platform=DevicePlatform.APPLE_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="iPhone 15 Pro",
        state=DeviceLifecycleState.AVAILABLE
    )
    device_registry.register_device(dev)

    res = client.post("/api/devices/apple:00008030-API-TEST/screenshots")
    assert res.status_code == 422
    assert "iOS screenshot capture is experimental" in res.json()["detail"]


def test_api_recording_lifecycle(client):
    client.get("/api/devices")

    # 1. Start recording
    res = client.post("/api/devices/android:mock-pixel-7/recording/start", json={"max_duration_seconds": 60})
    assert res.status_code == 200
    sess = res.json()
    assert sess["state"] == "RECORDING"

    # 2. Get status
    res_status = client.get("/api/devices/android:mock-pixel-7/recording/status")
    assert res_status.status_code == 200
    assert res_status.json()["state"] == "RECORDING"

    # 3. Stop recording
    res_stop = client.post("/api/devices/android:mock-pixel-7/recording/stop")
    assert res_stop.status_code == 200
    stopped = res_stop.json()
    assert stopped["state"] == "STOPPED"
    assert stopped["artifact_id"] is not None


def test_api_device_diagnostics(client):
    client.get("/api/devices")
    res = client.get("/api/devices/android:mock-pixel-7/diagnostics")
    assert res.status_code == 200
    diag = res.json()
    assert diag["serial"] == "mock-pixel-7"
    assert diag["lifecycle_state"] == "available"
    assert "provider_health" in diag


def test_api_device_logs_and_export(client):
    client.get("/api/devices")

    # GET logs
    res = client.get("/api/devices/android:mock-pixel-7/logs?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["supported"] is True
    assert "logs" in data

    # Export text
    res_exp = client.get("/api/devices/android:mock-pixel-7/logs/export?format=text")
    assert res_exp.status_code == 200
    assert "text/plain" in res_exp.headers["content-type"]

    # Export json and save artifact
    res_art = client.get("/api/devices/android:mock-pixel-7/logs/export?format=json&save_artifact=true")
    assert res_art.status_code == 200
    exp_art = res_art.json()
    assert exp_art["status"] == "exported"
    assert "artifact" in exp_art


def test_api_automation_workflow_crud_and_inline(client):
    client.get("/api/devices")

    # 1. Create workflow
    wf_payload = {
        "name": "HealthCheckFlow",
        "target_device": "android:mock-pixel-7",
        "steps": [
            {"step_name": "Wait step", "action": "WAIT", "duration_ms": 20},
            {"step_name": "State check", "action": "ASSERT_STATE", "expected_state": "available"}
        ]
    }
    res_create = client.post("/api/automation/workflows", json=wf_payload)
    assert res_create.status_code == 200
    wf_data = res_create.json()
    wf_id = wf_data["workflow_id"]

    # 2. List workflows
    res_list = client.get("/api/automation/workflows")
    assert res_list.status_code == 200
    assert any(w["workflow_id"] == wf_id for w in res_list.json())

    # 3. Execute workflow
    res_exec = client.post(f"/api/automation/workflows/{wf_id}/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    exec_id = exec_data["execution_id"]

    # 4. Get execution status
    res_get_exec = client.get(f"/api/automation/executions/{exec_id}")
    assert res_get_exec.status_code == 200
    assert res_get_exec.json()["workflow_id"] == wf_id

    # 5. Execute inline workflow
    res_inline = client.post("/api/automation/execute-inline", json={"workflow": wf_payload})
    assert res_inline.status_code == 200
    assert "execution_id" in res_inline.json()


def test_api_artifacts_download_and_delete(client):
    # Save test artifact
    art = artifact_manager.save_artifact(
        name="download_test.txt",
        artifact_type=ArtifactType.LOG_EXPORT,
        file_format="txt",
        data=b"Download content verification",
        device_id="android:test"
    )

    # GET download
    res_dl = client.get(f"/api/artifacts/{art.artifact_id}/download")
    assert res_dl.status_code == 200
    assert res_dl.content == b"Download content verification"

    # DELETE without confirm -> 400
    res_del_fail = client.delete(f"/api/artifacts/{art.artifact_id}?confirm=false")
    assert res_del_fail.status_code == 400

    # DELETE with confirm -> 200
    res_del_ok = client.delete(f"/api/artifacts/{art.artifact_id}?confirm=true")
    assert res_del_ok.status_code == 200
    assert res_del_ok.json()["status"] == "deleted"

    # GET summary
    res_sum = client.get("/api/artifacts/storage/summary")
    assert res_sum.status_code == 200
    assert "total_bytes_used" in res_sum.json()
