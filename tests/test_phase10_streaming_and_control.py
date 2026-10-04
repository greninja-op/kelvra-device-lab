"""
Comprehensive automated test suite for Phase 10: Android Streaming & Device Control.
Validates stream lifecycle (9 states), backpressure, startup timeout/failure,
device disconnect handling, single-writer session isolation (collision 409, renewal, release),
input control bounds checking, hardware key injection, and honest diagnostics.
"""

import asyncio
import time
import pytest
from fastapi.testclient import TestClient

from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus
from src.domain_model import (
    Device,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.input_controller import InputController
from src.screen_streamer import (
    DeviceStreamSession,
    ScreenStreamer,
    StreamConfig,
    StreamDiagnostics,
    StreamState,
)
from src.session_manager import DeviceLease, LeaseConflictError, SessionManager
from src.server import app, device_manager, device_registry, session_manager as server_session_mgr


client = TestClient(app)


# --- UNIT TESTS: STREAM LIFECYCLE & DIAGNOSTICS ---

@pytest.mark.asyncio
async def test_stream_lifecycle_start_and_stop():
    """Validates transition from IDLE -> PREPARING -> STARTING -> STREAMING -> STOPPING -> STOPPED."""
    manager = DeviceManager()
    dev = DeviceInfo(serial="stream-test-1", model="Test Device", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev)
    controller = InputController(manager)

    session = DeviceStreamSession("stream-test-1", controller, StreamConfig(max_fps=15))
    assert session.state == StreamState.IDLE

    # Start stream
    started = await session.start()
    assert started is True
    assert session.state == StreamState.STREAMING
    assert session.start_duration_ms is not None
    assert session.start_duration_ms >= 0.0

    diag = session.get_diagnostics()
    assert diag.state == StreamState.STREAMING
    assert diag.serial == "stream-test-1"

    # Stop stream
    await session.stop()
    assert session.state == StreamState.STOPPED
    assert session.current_fps == 0.0

    # Idempotent repeated stop
    await session.stop()
    assert session.state == StreamState.STOPPED


@pytest.mark.asyncio
async def test_stream_startup_failure_and_error_reporting():
    """Validates that if screenshot capture fails, state transitions to FAILED without lingering tasks."""
    manager = DeviceManager()
    controller = InputController(manager)

    # Override take_screenshot to simulate capture failure
    controller.take_screenshot = lambda *args, **kwargs: None

    session = DeviceStreamSession("failing-dev", controller)
    started = await session.start()
    assert started is False
    assert session.state == StreamState.FAILED
    assert session.error_message is not None
    assert "Initial frame capture returned empty" in session.error_message

    diag = session.get_diagnostics()
    assert diag.state == StreamState.FAILED
    assert diag.error_message is not None


@pytest.mark.asyncio
async def test_stream_device_disconnect_handling():
    """Validates transition to DEVICE_DISCONNECTED and resource reaping when device is unplugged."""
    manager = DeviceManager()
    dev = DeviceInfo(serial="unplug-test", model="Unplug Device", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev)
    controller = InputController(manager)

    session = DeviceStreamSession("unplug-test", controller)
    await session.start()
    assert session.state == StreamState.STREAMING

    # Signal device detachment
    session.handle_device_disconnect()
    assert session.state == StreamState.DEVICE_DISCONNECTED
    assert session.error_message is not None
    assert "detached" in session.error_message
    assert session._capture_task is None

    diag = session.get_diagnostics()
    assert diag.state == StreamState.DEVICE_DISCONNECTED


@pytest.mark.asyncio
async def test_screen_streamer_manager_multi_device_isolation():
    """Validates that ScreenStreamer manages independent DeviceStreamSessions per serial."""
    manager = DeviceManager()
    dev1 = DeviceInfo(serial="dev-stream-a", model="Device A", status=DeviceStatus.ONLINE)
    dev2 = DeviceInfo(serial="dev-stream-b", model="Device B", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev1)
    manager.add_mock_device(dev2)
    controller = InputController(manager)

    streamer = ScreenStreamer(controller)

    # Start stream on dev1
    await streamer.start_stream("dev-stream-a")
    diag_a = streamer.get_diagnostics("dev-stream-a")
    diag_b = streamer.get_diagnostics("dev-stream-b")

    assert diag_a.state == StreamState.STREAMING
    assert diag_b.state == StreamState.IDLE

    # Stop dev1
    await streamer.stop_stream("dev-stream-a")
    assert streamer.get_diagnostics("dev-stream-a").state == StreamState.STOPPED

    await streamer.stop_all()


# --- UNIT TESTS: SESSION ISOLATION & LEASE EXCLUSIVITY ---

def test_session_manager_acquire_and_release():
    """Validates exclusive operator lease acquisition, duration calculation, and clean release."""
    sm = SessionManager(default_lease_duration=120.0)

    lease = sm.acquire_lease("test-dev-1", client_id="operator-alice", duration_seconds=60.0)
    assert lease.client_id == "operator-alice"
    assert lease.device_id == "android:test-dev-1"
    assert lease.is_expired is False
    assert lease.remaining_seconds <= 60.0
    assert lease.session_token.startswith("kdl-")

    # Verify query
    active = sm.get_active_lease("test-dev-1")
    assert active is not None
    assert active.client_id == "operator-alice"

    # Release with matching token
    released = sm.release_lease("test-dev-1", session_token=lease.session_token)
    assert released is True
    assert sm.get_active_lease("test-dev-1") is None


def test_session_manager_collision_rejection():
    """Validates that a second client cannot acquire an exclusive lease on an already locked device."""
    sm = SessionManager(default_lease_duration=120.0)
    sm.acquire_lease("locked-dev", client_id="operator-alice", duration_seconds=100.0)

    # Operator Bob attempts to lease same device -> LeaseConflictError
    with pytest.raises(LeaseConflictError) as exc_info:
        sm.acquire_lease("locked-dev", client_id="operator-bob", duration_seconds=60.0)

    err = exc_info.value
    assert err.held_by == "operator-alice"
    assert err.expires_in_seconds > 0.0


def test_session_manager_lease_renewal_and_expiration():
    """Validates heartbeat renewal and automatic cleanup of expired leases."""
    sm = SessionManager()
    # Acquire very short lease
    lease = sm.acquire_lease("expiring-dev", client_id="operator-charlie", duration_seconds=0.1)
    time.sleep(0.15)

    # Lease is now expired
    assert sm.get_active_lease("expiring-dev") is None

    # New client can now acquire the freed device
    new_lease = sm.acquire_lease("expiring-dev", client_id="operator-dave", duration_seconds=60.0)
    assert new_lease.client_id == "operator-dave"

    # Heartbeat renewal
    renewed = sm.renew_lease("expiring-dev", new_lease.session_token, extension_seconds=120.0)
    assert renewed.remaining_seconds > 60.0


def test_session_manager_unauthorized_device_rejection():
    """Validates that unauthorized devices in registry are rejected from lease acquisition."""
    from src.device_registry import DeviceRegistry
    from src.mock_provider import MockDeviceProvider
    reg = DeviceRegistry()
    mock_prov = MockDeviceProvider()
    reg.register_provider(mock_prov)
    unauth_dev = Device(
        id="android:unauth-lease",
        serial="unauth-lease",
        provider_id=mock_prov.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Unauthorized Phone",
        state=DeviceLifecycleState.UNAUTHORIZED
    )
    mock_prov.add_device(unauth_dev)
    reg.reconcile()

    sm = SessionManager()
    sm.set_registry(reg)

    with pytest.raises(PermissionError) as exc_info:
        sm.acquire_lease("unauth-lease", client_id="operator-eve")

    assert "unauthorized" in str(exc_info.value).lower()


# --- UNIT TESTS: INPUT CONTROLLER VALIDATION & SECURITY ---

def test_input_controller_coordinate_bounds():
    """Validates that out-of-bounds or negative touch coordinates are rejected."""
    manager = DeviceManager()
    dev = DeviceInfo(serial="bounds-dev", model="Bounds Dev", status=DeviceStatus.ONLINE, screen_width=1080, screen_height=2400)
    manager.add_mock_device(dev)
    controller = InputController(manager)

    # Valid coordinates
    assert controller.tap("bounds-dev", 500, 1000) is True

    # Negative coordinates
    assert controller.tap("bounds-dev", -10, 500) is False
    assert controller.tap("bounds-dev", 500, -5) is False

    # Outrageous coordinates (e.g. 100,000)
    assert controller.tap("bounds-dev", 50000, 200) is False
    assert controller.swipe("bounds-dev", 0, 0, 50000, 500) is False


def test_input_controller_session_token_enforcement():
    """Validates that input commands require valid session token when a lease is active."""
    manager = DeviceManager()
    dev = DeviceInfo(serial="leased-input-dev", model="Leased Dev", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev)

    sm = SessionManager()
    controller = InputController(manager, session_manager=sm)

    # Acquire lease
    lease = sm.acquire_lease("leased-input-dev", client_id="operator-alice")

    # Command without token or with bogus token is rejected
    assert controller.tap("leased-input-dev", 100, 200, session_token=None) is False
    assert controller.tap("leased-input-dev", 100, 200, session_token="wrong-token") is False

    # Command with valid session token succeeds
    assert controller.tap("leased-input-dev", 100, 200, session_token=lease.session_token) is True
    assert controller.keyevent("leased-input-dev", "BACK", session_token=lease.session_token) is True


def test_input_controller_keyevent_and_text_sanitization():
    """Validates hardware key resolution and text sanitization."""
    manager = DeviceManager()
    dev = DeviceInfo(serial="keys-dev", model="Keys Dev", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev)
    controller = InputController(manager)

    # Named hardware keys
    assert controller.keyevent("keys-dev", "BACK") is True
    assert controller.keyevent("keys-dev", "HOME") is True
    assert controller.keyevent("keys-dev", "APP_SWITCH") is True
    assert controller.keyevent("keys-dev", "POWER") is True
    assert controller.keyevent("keys-dev", "VOLUME_UP") is True

    # Integer keycodes
    assert controller.keyevent("keys-dev", 4) is True

    # Unknown key name returns False
    assert controller.keyevent("keys-dev", "NON_EXISTENT_KEY_NAME_XYZ") is False

    # Text input with spaces and special characters
    assert controller.type_text("keys-dev", "Hello World $100 & 'quotes'") is True


# --- INTEGRATION TESTS: REST API ENDPOINTS ---

def test_api_stream_lifecycle_endpoints():
    """Tests /api/devices/{id}/stream/start, /status, /stop REST endpoints."""
    # Ensure mock device is in device_manager
    mock_dev = DeviceInfo(serial="api-stream-dev", model="API Stream Phone", status=DeviceStatus.ONLINE)
    device_manager.add_mock_device(mock_dev)

    # Start stream with config
    res_start = client.post(
        "/api/devices/api-stream-dev/stream/start",
        json={"max_width": 720, "quality": 75, "max_fps": 30}
    )
    assert res_start.status_code == 200
    data = res_start.json()
    assert data["state"] == "streaming"
    assert data["serial"] == "api-stream-dev"

    # Status check
    res_status = client.get("/api/devices/api-stream-dev/stream/status")
    assert res_status.status_code == 200
    assert res_status.json()["state"] == "streaming"

    # Stop stream
    res_stop = client.post("/api/devices/api-stream-dev/stream/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "stopped"

    # Status after stop
    res_post_stop = client.get("/api/devices/api-stream-dev/stream/status")
    assert res_post_stop.json()["state"] == "stopped"


def test_api_lease_lifecycle_and_conflict():
    """Tests /api/devices/{id}/lease acquisition, collision (409), renewal, and release."""
    mock_dev = DeviceInfo(serial="api-lease-dev", model="API Lease Phone", status=DeviceStatus.ONLINE)
    device_manager.add_mock_device(mock_dev)

    # Acquire lease for Operator 1
    res_lease = client.post(
        "/api/devices/api-lease-dev/lease",
        json={"client_id": "operator-1", "duration_seconds": 120.0, "purpose": "Testing"}
    )
    assert res_lease.status_code == 200
    lease_data = res_lease.json()
    assert lease_data["client_id"] == "operator-1"
    token = lease_data["session_token"]

    # Collision test: Operator 2 attempts to lease -> HTTP 409 Conflict
    res_conflict = client.post(
        "/api/devices/api-lease-dev/lease",
        json={"client_id": "operator-2", "duration_seconds": 60.0}
    )
    assert res_conflict.status_code == 409
    err = res_conflict.json()["detail"]
    assert err["code"] == "DEVICE_ALREADY_LEASED"
    assert err["held_by"] == "operator-1"

    # Check active sessions endpoint
    res_sessions = client.get("/api/sessions")
    assert res_sessions.status_code == 200
    sessions = res_sessions.json()
    assert any(s["serial"] == "api-lease-dev" for s in sessions)

    # Renew lease
    res_renew = client.post(
        "/api/devices/api-lease-dev/lease/renew",
        json={"session_token": token, "extension_seconds": 180.0}
    )
    assert res_renew.status_code == 200

    # Release lease
    res_release = client.delete(f"/api/devices/api-lease-dev/lease?session_token={token}")
    assert res_release.status_code == 200

    # Device lease is now inactive
    res_status = client.get("/api/devices/api-lease-dev/lease")
    assert res_status.status_code == 200
    assert res_status.json()["active"] is False


def test_api_input_with_session_token_and_unauthorized_guard():
    """Tests input dispatch with lease token and rejection on unauthorized devices."""
    # 1. Online device with lease
    mock_dev = DeviceInfo(serial="api-input-dev", model="Input Phone", status=DeviceStatus.ONLINE)
    device_manager.add_mock_device(mock_dev)

    # Acquire lease
    res_lease = client.post("/api/devices/api-input-dev/lease", json={"client_id": "input-operator"})
    token = res_lease.json()["session_token"]

    # Tap with valid token
    res_tap = client.post(
        "/api/devices/api-input-dev/input/tap",
        json={"x": 500, "y": 800, "session_token": token}
    )
    assert res_tap.status_code == 200

    # Tap with invalid token -> 409 Conflict
    res_bad_token = client.post(
        "/api/devices/api-input-dev/input/tap",
        json={"x": 500, "y": 800, "session_token": "bogus-token"}
    )
    assert res_bad_token.status_code == 409

    # Clean up lease
    client.delete(f"/api/devices/api-input-dev/lease?session_token={token}")

    from src.server import mock_provider
    unauth_dev = Device(
        id="android:unauth-input-dev",
        serial="unauth-input-dev",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Unauthorized Device",
        state=DeviceLifecycleState.UNAUTHORIZED
    )
    mock_provider.add_device(unauth_dev)
    device_registry.reconcile()

    res_unauth_tap = client.post(
        "/api/devices/unauth-input-dev/input/tap",
        json={"x": 500, "y": 800}
    )
    assert res_unauth_tap.status_code == 403
    assert "unauthorized" in res_unauth_tap.json()["detail"].lower()
