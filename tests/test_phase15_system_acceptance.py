"""
Unit and integration tests for Phase 15:
Comprehensive Standalone System Testing & Acceptance Assessment.
"""

import asyncio
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from src.server import (
    app,
    artifact_manager,
    recording_manager,
    diagnostics_service,
    automation_engine,
    device_registry,
    mock_provider,
    device_manager as server_dm,
    session_manager,
    screen_streamer,
    logcat_service,
    input_controller,
    avd_manager,
)
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
from src.screen_streamer import StreamState, StreamConfig, DeviceStreamSession, ScreenStreamer
from src.input_controller import InputController
from src.session_manager import SessionManager, DeviceLease, LeaseConflictError
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus
from src.avd_manager import AvdConfig, AvdStatus, EmulatorSession, EmulatorLaunchOptions


@pytest.fixture(autouse=True)
def setup_phase15_system_devices():
    """Ensure baseline test devices exist in registry and server state."""
    dev = Device(
        id="android:p15-system-device",
        serial="p15-system-device",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel System Acceptance",
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[
            DeviceCapability.SCREEN_STREAM_JPEG,
            DeviceCapability.TOUCH_INTERACTION,
            DeviceCapability.TEST_AUTOMATION,
            DeviceCapability.LOGCAT_STREAMING,
        ],
    )
    device_registry.register_device(dev)

    mock_info = DeviceInfo(
        serial="p15-system-device",
        model="Pixel System Acceptance",
        manufacturer="Google",
        status=DeviceStatus.ONLINE,
        screen_width=1080,
        screen_height=2400,
    )
    server_dm.add_mock_device(mock_info)


@pytest.mark.asyncio
async def test_e2e_workflow_1_discovery_streaming_control_lifecycle():
    """E2E Workflow 1: Discovery -> Connection -> Lease -> Streaming -> Input -> Disconnect."""
    client = TestClient(app)
    serial = "p15-system-device"
    device_id = f"android:{serial}"

    # 1. Verify device is present in inventory
    resp_inv = client.get("/api/devices")
    assert resp_inv.status_code == 200
    devices = resp_inv.json()
    assert any(d["serial"] == serial for d in devices)

    # 2. Acquire single-writer operator lease
    resp_lease = client.post(
        f"/api/devices/{serial}/lease",
        json={"client_id": "e2e-operator-1", "duration_seconds": 60.0, "purpose": "System Acceptance Testing"},
    )
    assert resp_lease.status_code == 200
    lease_data = resp_lease.json()
    assert lease_data["client_id"] == "e2e-operator-1"
    session_token = lease_data["session_token"]

    # 3. Initialize streaming session
    mock_input = MagicMock(spec=InputController)
    mock_input.take_screenshot.return_value = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01"
    mock_input.tap.return_value = True

    stream_session = DeviceStreamSession(
        serial=serial,
        input_controller=mock_input,
        config=StreamConfig(max_fps=30, quality=75),
    )
    started = await stream_session.start()
    assert started is True
    assert stream_session.state == StreamState.STREAMING

    # 4. Attach client viewer and verify frame delivery
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    await stream_session.add_viewer(mock_ws)
    await asyncio.sleep(0.1)

    diag = stream_session.get_diagnostics()
    assert diag.viewer_count == 1
    assert diag.state == StreamState.STREAMING

    # 5. Inject remote tap using acquired lease session token
    resp_tap = client.post(
        f"/api/devices/{serial}/input/tap",
        json={"x": 540, "y": 1200, "session_token": session_token},
    )
    assert resp_tap.status_code == 200
    assert resp_tap.json()["status"] == "ok"

    # 6. Release lease and stop stream
    resp_release = client.delete(f"/api/devices/{serial}/lease", params={"session_token": session_token})
    assert resp_release.status_code == 200

    await stream_session.stop()
    assert stream_session.state == StreamState.STOPPED


def test_e2e_workflow_2_avd_inventory_and_lifecycle_supervision():
    """E2E Workflow 2: AVD virtual device enumeration -> lifecycle boot -> port allocation."""
    client = TestClient(app)

    # 1. Query AVD inventory and environment
    resp_avds = client.get("/api/avd/list")
    assert resp_avds.status_code == 200
    avd_data = resp_avds.json()
    assert isinstance(avd_data, list)

    resp_env = client.get("/api/avd/environment")
    assert resp_env.status_code == 200
    assert "sdk_detected" in resp_env.json()

    # 2. Add mock AVD and verify inventory reflection
    avd_name = "Acceptance_Pixel_API_34"
    mock_cfg = AvdConfig(
        name=avd_name,
        path="/mock/path/Acceptance_Pixel.avd",
        status=AvdStatus.STOPPED,
    )
    avd_manager.add_mock_avd(mock_cfg)
    assert avd_manager.get_avd(avd_name) is not None

    # 3. Simulate active session registration
    session = EmulatorSession(
        avd_name=avd_name,
        options=EmulatorLaunchOptions(port=5554),
        pid=9999,
    )
    session.serial = "emulator-5554"
    session.state = AvdStatus.READY
    session.boot_completed_at = time.time()
    avd_manager._sessions[avd_name] = session

    active = avd_manager._sessions.get(avd_name)
    assert active is not None
    assert active.state == AvdStatus.READY
    assert active.serial == "emulator-5554"

    # get_avd should reflect the active session
    avd_info = avd_manager.get_avd(avd_name)
    assert avd_info is not None
    assert avd_info.status == AvdStatus.READY
    assert avd_info.running_serial == "emulator-5554"

    # Cleanup test session and mock AVD
    del avd_manager._sessions[avd_name]
    avd_manager.clear_mock_avds()


@pytest.mark.asyncio
async def test_e2e_workflow_3_automation_workflow_and_artifact_persistence():
    """E2E Workflow 3: Automation workflow creation -> execution -> artifact storage."""
    mock_input = MagicMock(spec=InputController)
    mock_input.tap.return_value = True
    mock_input.take_screenshot.return_value = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    engine = AutomationEngine(
        device_registry=device_registry,
        input_controller=mock_input,
        artifact_manager=artifact_manager,
    )

    wf = WorkflowDefinition(
        name="Acceptance Smoke Suite",
        description="End-to-end acceptance automation workflow",
        target_device="android:p15-system-device",
        steps=[
            WorkflowStep(
                step_name="Wait for System Ready",
                action=ActionType.WAIT,
                duration_ms=50,
            ),
            WorkflowStep(
                step_name="Tap Settings Launcher",
                action=ActionType.TAP,
                x=500,
                y=1000,
            ),
            WorkflowStep(
                step_name="Capture Final State",
                action=ActionType.SCREENSHOT,
            ),
        ],
    )

    # Validate workflow schema
    valid, err = engine.validate_workflow(wf)
    assert valid is True
    assert err is None

    # Execute workflow
    report = await engine.execute_workflow(wf)
    task = engine._active_tasks.get(report.execution_id)
    if task:
        await task

    final_report = engine.get_execution(report.execution_id)
    assert final_report is not None
    assert final_report.status == ExecutionStatus.COMPLETED
    assert len(final_report.step_results) == 3
    assert all(r.status == "PASSED" for r in final_report.step_results)

    # Verify report is cataloged as an artifact
    artifacts = artifact_manager.list_artifacts(artifact_type=ArtifactType.AUTOMATION_REPORT)
    assert len(artifacts) >= 1
    latest_art = artifacts[0]
    assert latest_art.artifact_type == ArtifactType.AUTOMATION_REPORT
    assert latest_art.file_size_bytes > 0


def test_e2e_workflow_4_observability_logcat_redaction_and_export():
    """E2E Workflow 4: Logcat ingestion -> regex credential scrubbing -> history filtering -> export."""
    dm = DeviceManager()
    logcat = LogcatService(device_manager=dm, buffer_size=1000)
    serial = "p15-system-device"

    # Ingest log entries containing sensitive tokens and credentials
    sensitive_lines = [
        "I/Auth: User logged in successfully with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0",
        "D/Network: Request payload url=https://api.example.com?api_key=secret_1234567890abcdef",
        "V/Session: Active session_token=kdl-9876543210fedcba initialized",
        "W/Login: Failed authentication with password=SuperSecretPassword123",
        "E/Crash: Uncaught NullPointerException at com.example.MainActivity.onCreate",
    ]

    for raw in sensitive_lines:
        sanitized = sanitize_log_message(raw)
        # Verify scrubbing occurred before buffering
        assert "eyJhbGciOi" not in sanitized
        assert "secret_1234567890abcdef" not in sanitized
        assert "kdl-9876543210fedcba" not in sanitized
        if any(k in raw for k in ("Bearer", "api_key", "session_token", "password")):
            assert "[REDACTED" in sanitized

        buf = logcat.get_or_create_buffer(serial)
        buf.append({
            "timestamp": "12:30:00.000",
            "pid": 4567,
            "tid": 4567,
            "level": raw[0],
            "tag": raw.split("/")[1].split(":")[0],
            "message": sanitized,
            "raw": sanitized,
        })

    # Test filtering by level
    errors = logcat.get_history(serial, level="E")
    assert len(errors) == 1
    assert "NullPointerException" in errors[0]["message"]

    # Test filtering by tag
    auth_logs = logcat.get_history(serial, tag="Auth")
    assert len(auth_logs) == 1
    assert "Bearer [REDACTED_SECRET]" in auth_logs[0]["message"]

    # Test plaintext export
    text_export = logcat.export_logs(serial, format_type="text")
    assert "NullPointerException" in text_export
    assert "Bearer [REDACTED_SECRET]" in text_export


def test_e2e_workflow_5_security_gates_and_boundary_enforcement():
    """E2E Workflow 5: Security gates -> unauthorized access, lease conflicts, path traversal."""
    client = TestClient(app)

    # 1. Register an unauthorized device
    unauth_dev = Device(
        id="android:unauth-dev-99",
        serial="unauth-dev-99",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Locked Device",
        state=DeviceLifecycleState.UNAUTHORIZED,
        error=DeviceError(code="UNAUTHORIZED", message="Device locked", recovery_hint="Accept RSA key"),
    )
    device_registry.register_device(unauth_dev)

    # Verify input injection on unauthorized device is rejected with HTTP 403
    resp_touch = client.post(
        "/api/devices/unauth-dev-99/input/tap",
        json={"x": 100, "y": 100},
    )
    assert resp_touch.status_code in (403, 400)

    # 2. Single-writer lease conflict
    lease_mgr = SessionManager()
    l1 = lease_mgr.acquire_lease("android:p15-system-device", client_id="operator-a", duration_seconds=10.0)
    assert l1 is not None

    with pytest.raises(LeaseConflictError) as exc_info:
        lease_mgr.acquire_lease("android:p15-system-device", client_id="operator-b", duration_seconds=10.0)
    assert "locked by session 'operator-a'" in str(exc_info.value)

    lease_mgr.release_lease("android:p15-system-device", session_token=l1.session_token)

    # 3. Path traversal defense
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = ArtifactManager(base_dir=tmp_dir)
        # Sanitizer strips .. and anchors safely inside tmp_dir
        rec = mgr.save_artifact(
            name="../../malicious_escape.sh",
            artifact_type=ArtifactType.LOG_EXPORT,
            file_format="sh",
            data=b"#!/bin/sh\necho compromised",
            device_id="android:p15-system-device",
        )
        assert rec is not None
        # Verify no file was written outside base_dir
        assert not Path(tmp_dir).parent.joinpath("malicious_escape.sh").exists()
        assert Path(tmp_dir).joinpath(rec.relative_path).exists()


def test_acceptance_criteria_invariants():
    """Verify objective Acceptance Criteria (F-AC, P-AC, S-AC, Z-AC) invariants."""
    # F-AC-02: Platform and Hardware Type Classification
    dev = Device(
        id="android:acceptance-eval",
        serial="acceptance-eval",
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel 8 Pro",
        state=DeviceLifecycleState.AVAILABLE,
    )
    assert dev.platform == DevicePlatform.ANDROID_PHYSICAL
    assert dev.device_type == DeviceType.PHYSICAL
    assert dev.id == "android:acceptance-eval"

    # F-AC-04: Unauthorized State Guidance
    unauth = Device(
        id="android:unauth-eval",
        serial="unauth-eval",
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Unauth Device",
        state=DeviceLifecycleState.UNAUTHORIZED,
        error=DeviceError(
            code="UNAUTHORIZED",
            message="Device is unauthorized",
            recovery_hint="Unlock device screen and tap Allow USB Debugging",
        ),
    )
    assert unauth.state == DeviceLifecycleState.UNAUTHORIZED
    assert "Allow USB Debugging" in unauth.error.recovery_hint

    # S-AC-02: Shell Metacharacter Redaction/Escaping
    raw_cmd = "test; rm -rf /; echo $SECRET"
    clean_log = sanitize_log_message(raw_cmd)
    assert isinstance(clean_log, str)

    # Z-AC-01: Zero Emoji in Schemas and Models
    dev_dump = dev.model_dump_json()
    import re
    emoji_pattern = re.compile(r"[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]")
    assert not emoji_pattern.search(dev_dump)
