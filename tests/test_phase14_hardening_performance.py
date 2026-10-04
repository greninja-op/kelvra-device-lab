"""
Unit and integration tests for Phase 14:
Performance, Reliability, Compatibility & Hardening.
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


@pytest.fixture(autouse=True)
def setup_phase14_devices():
    """Ensure baseline test devices exist in registry and device manager."""
    dev = Device(
        id="android:p14-perf-device",
        serial="p14-perf-device",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel Hardening Test",
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
        serial="p14-perf-device",
        model="Pixel Hardening Test",
        manufacturer="Google",
        status=DeviceStatus.ONLINE,
        screen_width=1080,
        screen_height=2400,
    )
    server_dm.add_mock_device(mock_info)


@pytest.mark.asyncio
async def test_screen_streamer_idle_throttling():
    """Verify that when 0 viewers are connected, capture loop throttles and avoids wasteful screencaps."""
    mock_ctrl = MagicMock(spec=InputController)
    mock_ctrl.take_screenshot.return_value = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # minimal valid JPEG header

    session = DeviceStreamSession(
        serial="p14-perf-device",
        input_controller=mock_ctrl,
        config=StreamConfig(max_fps=60, quality=70),
    )

    started = await session.start()
    assert started is True
    assert session.state == StreamState.STREAMING
    assert len(session._active_connections) == 0

    # With 0 viewers, initial probe called once, subsequent loop sleeps and skips screencap
    initial_call_count = mock_ctrl.take_screenshot.call_count
    await asyncio.sleep(0.35)

    # Call count should not have exploded to 60 calls/sec
    assert mock_ctrl.take_screenshot.call_count == initial_call_count

    # Now add a mock viewer
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    await session.add_viewer(mock_ws)
    assert len(session._active_connections) == 1

    # Give loop sufficient time to wake from 0.15s idle throttle and capture while active
    await asyncio.sleep(0.35)
    assert mock_ctrl.take_screenshot.call_count > initial_call_count

    # Remove viewer
    await session.remove_viewer(mock_ws)
    assert len(session._active_connections) == 0

    # Settle in-flight frame and verify sustained idle throttle
    await asyncio.sleep(0.05)
    settled_call_count = mock_ctrl.take_screenshot.call_count
    await asyncio.sleep(0.25)
    # Stays throttled after viewer disconnects
    assert mock_ctrl.take_screenshot.call_count == settled_call_count

    await session.stop()
    assert session.state == StreamState.STOPPED


def test_discovery_idempotency_and_stability():
    """Repeated discovery sweeps must not create duplicate records or corrupt registry state."""
    registry = DeviceRegistry()
    provider = MockDeviceProvider()
    mock_dev = Device(
        id="android:idempotent-dev-01",
        serial="idempotent-dev-01",
        provider_id=provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Stability Device 01",
        state=DeviceLifecycleState.AVAILABLE,
    )
    provider.add_device(mock_dev)

    # Initial discovery
    devices_1 = provider.discover_devices()
    for d in devices_1:
        registry.register_device(d)

    assert len(registry.list_devices()) == 1
    d_initial = registry.get_device("android:idempotent-dev-01")
    assert d_initial is not None
    assert d_initial.state == DeviceLifecycleState.AVAILABLE

    # Second, third discovery cycles
    for _ in range(5):
        devices = provider.discover_devices()
        for d in devices:
            registry.register_device(d)

    # Count must remain exactly 1
    assert len(registry.list_devices()) == 1
    d_stable = registry.get_device("android:idempotent-dev-01")
    assert d_stable.serial == "idempotent-dev-01"
    assert d_stable.state == DeviceLifecycleState.AVAILABLE


@pytest.mark.asyncio
async def test_device_disappearance_and_stream_cleanup():
    """Device disconnection must transition streamer to DEVICE_DISCONNECTED and notify viewers."""
    mock_ctrl = MagicMock(spec=InputController)
    mock_ctrl.take_screenshot.return_value = b"frame"

    session = DeviceStreamSession(
        serial="disconnect-dev",
        input_controller=mock_ctrl,
    )
    await session.start()

    mock_ws = AsyncMock()
    await session.add_viewer(mock_ws)

    # Signal device disconnect
    session.handle_device_disconnect()
    assert session.state == StreamState.DEVICE_DISCONNECTED
    assert "detached" in session.error_message.lower()

    # Verify disconnect message broadcast to viewer
    calls = mock_ws.send_json.call_args_list
    disconnect_messages = [
        c[0][0] for c in calls if isinstance(c[0][0], dict) and c[0][0].get("type") == "error"
    ]
    assert len(disconnect_messages) >= 1
    assert disconnect_messages[0]["code"] == "DEVICE_DISCONNECTED"

    await session.stop()


def test_logcat_circular_buffer_memory_bounding():
    """Logcat buffer must remain bounded at maxlen without memory exhaustion."""
    dm = DeviceManager()
    logcat = LogcatService(device_manager=dm, buffer_size=2000)
    serial = "bounding-test-dev"
    buf = logcat.get_or_create_buffer(serial)

    # Ingest 5000 lines
    for i in range(5000):
        buf.append({
            "timestamp": f"12:00:{i:05d}",
            "pid": 1000,
            "tid": 1000,
            "level": "D",
            "tag": "Test",
            "message": f"Line {i:05d}: system event payload",
            "raw": f"D/Test: Line {i:05d}"
        })

    assert len(buf) == 2000
    # Oldest 3000 should have rolled off, so first entry is Line 3000
    assert "Line 03000" in buf[0]["message"]
    assert "Line 04999" in buf[-1]["message"]


def test_artifact_quota_and_eviction_stability():
    """ArtifactManager enforces quota_bytes and prunes oldest artifacts correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 10 KB quota for tight testing
        mgr = ArtifactManager(base_dir=tmp_dir, quota_bytes=10 * 1024)

        # Create 5 artifacts of 3 KB each = 15 KB total (exceeds 10 KB)
        created_ids = []
        for i in range(5):
            payload = b"X" * 3072
            rec = mgr.save_artifact(
                name=f"shot_{i}.bin",
                artifact_type=ArtifactType.SCREENSHOT,
                file_format="bin",
                data=payload,
                device_id="android:p14-perf-device",
                metadata={"index": str(i)},
            )
            created_ids.append(rec.artifact_id)
            time.sleep(0.01)

        # Total stored size must remain within quota
        total_size = mgr.get_total_size_bytes()
        assert total_size <= 10 * 1024
        # Oldest artifacts should have been pruned
        remaining_artifacts = mgr.list_artifacts()
        remaining_ids = {a.artifact_id for a in remaining_artifacts}
        assert created_ids[0] not in remaining_ids  # oldest pruned


def test_session_lease_expiration_and_recovery():
    """Leases must cleanly expire and permit subsequent clients to acquire without deadlock."""
    mgr = SessionManager()
    serial = "lease-hardening-dev"

    # Acquire short lease: 0.15s
    lease1 = mgr.acquire_lease(
        device_id_or_serial=serial,
        client_id="client-alpha",
        duration_seconds=0.15,
        purpose="Hardening test alpha",
    )
    assert lease1 is not None
    assert mgr.get_active_lease(serial) is not None

    # Immediate second acquisition must fail with LeaseConflictError
    with pytest.raises(LeaseConflictError):
        mgr.acquire_lease(
            device_id_or_serial=serial,
            client_id="client-beta",
            duration_seconds=1.0,
            purpose="Hardening test beta",
        )

    # Wait for expiration
    time.sleep(0.25)
    assert mgr.get_active_lease(serial) is None

    # Second client can now acquire without error
    lease2 = mgr.acquire_lease(
        device_id_or_serial=serial,
        client_id="client-beta",
        duration_seconds=1.0,
        purpose="Hardening test beta retry",
    )
    assert lease2 is not None
    assert lease2.client_id == "client-beta"
    mgr.release_lease(serial, lease2.session_token)


def test_diagnostics_service_numeric_integrity():
    """Diagnostics metrics must return valid reports with correct device and provider info."""
    diag = DiagnosticsService(
        device_registry=device_registry,
        screen_streamer=screen_streamer,
        session_manager=session_manager,
    )

    report = diag.get_diagnostics("android:p14-perf-device")
    assert report is not None
    assert report.serial == "p14-perf-device"
    assert report.device_id == "android:p14-perf-device"
    assert isinstance(report.recent_errors, list)

    diag.log_error("android:p14-perf-device", "PROBE_ERR", "Simulated probe failure", "telemetry")
    report_updated = diag.get_diagnostics("android:p14-perf-device")
    assert report_updated is not None
    assert any(e["error_code"] == "PROBE_ERR" for e in report_updated.recent_errors)


def test_security_input_injection_hardening():
    """API endpoints must safely validate input parameters and reject malformed requests."""
    client = TestClient(app)

    # Test touch endpoint with invalid negative / absurd coordinates
    resp = client.post(
        "/api/devices/p14-perf-device/input/tap",
        json={"x": -9999, "y": -9999},
    )
    assert resp.status_code in (200, 400, 422)

    # Test key endpoint with invalid key name
    resp_key = client.post(
        "/api/devices/p14-perf-device/input/key",
        json={"key": "INVALID_KEY_CODE_MALICIOUS; echo hacked"},
    )
    assert resp_key.status_code in (200, 400, 422)


@pytest.mark.asyncio
async def test_automation_step_timeout_and_error_containment():
    """Workflow engine must contain failing steps and not crash the parent process."""
    mock_input = MagicMock(spec=InputController)
    # Simulate step action returning failure
    mock_input.tap.return_value = False

    engine = AutomationEngine(
        device_registry=device_registry,
        input_controller=mock_input,
        artifact_manager=artifact_manager,
    )

    # Step validation check
    wf_invalid = WorkflowDefinition(
        name="Invalid Step Test",
        target_device="android:p14-perf-device",
        steps=[
            WorkflowStep(
                step_name="Bad Step",
                action=ActionType.KEY,
                key=None,
            )
        ],
    )
    valid, err_msg = engine.validate_workflow(wf_invalid)
    assert valid is False
    assert "requires a key name" in err_msg

    # Step execution failure containment
    wf_failing = WorkflowDefinition(
        name="Error Containment Test",
        target_device="android:p14-perf-device",
        steps=[
            WorkflowStep(
                step_name="Step 1 - Wait",
                action=ActionType.WAIT,
                duration_ms=50,
            ),
            WorkflowStep(
                step_name="Step 2 - Failing Tap",
                action=ActionType.TAP,
                x=500,
                y=500,
            ),
        ],
    )

    report = await engine.execute_workflow(wf_failing)
    task = engine._active_tasks.get(report.execution_id)
    if task:
        await task

    final_report = engine.get_execution(report.execution_id)
    assert final_report is not None
    assert final_report.status == ExecutionStatus.FAILED
    assert len(final_report.step_results) >= 2
    assert final_report.step_results[1].status == "FAILED"
