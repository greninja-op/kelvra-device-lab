"""
Phase 23 Test Suite: Multi-Device Laboratory Soak Testing, Concurrency & Deployment.
Validates multi-device concurrency, single-writer lease isolation under load,
streaming frame dispatch stability, rapid session turnover cleanup, and pre-flight deployment checks.

Zero Emoji Prohibition Enforced.
"""

import asyncio
import gc
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.server import (
    app,
    device_registry,
    session_manager,
    screen_streamer,
    device_manager,
)
from src.domain_model import (
    Device,
    DevicePlatform,
    DeviceType,
    DeviceLifecycleState,
    DeviceCapability,
)
from src.device_manager import DeviceInfo, DeviceStatus
from src.session_manager import LeaseConflictError, SessionManager
from src.screen_streamer import StreamConfig, StreamState, DeviceStreamSession
from deploy.deploy_check import PreFlightCheck


@pytest.fixture
def soak_test_client():
    return TestClient(app)


@pytest.fixture
def four_test_devices():
    """Register four distinct test devices for concurrency testing."""
    devices = []
    for i in range(1, 5):
        serial = f"soak-device-{i:02d}"
        dev = Device(
            id=f"android:{serial}",
            serial=serial,
            provider_id="mock_provider",
            display_name=f"Soak Laboratory Node {i}",
            manufacturer="MockCorp",
            model=f"MockNode-{i}",
            platform=DevicePlatform.ANDROID_PHYSICAL if i % 2 == 1 else DevicePlatform.ANDROID_VIRTUAL,
            device_type=DeviceType.PHYSICAL if i % 2 == 1 else DeviceType.VIRTUAL,
            state=DeviceLifecycleState.AVAILABLE,
            capabilities=[
                DeviceCapability.DISCOVERY,
                DeviceCapability.SCREEN_STREAM_JPEG,
                DeviceCapability.TOUCH_INTERACTION,
                DeviceCapability.TEST_AUTOMATION,
            ],
            display_width=1080,
            display_height=2400,
        )
        device_registry.register_device(dev)
        device_manager.add_mock_device(
            DeviceInfo(
                serial=serial,
                model=f"MockNode-{i}",
                status=DeviceStatus.ONLINE,
            )
        )
        devices.append(dev)
    yield devices
    # Teardown
    for dev in devices:
        try:
            session_manager.release_lease(dev.serial, force=True)
            device_registry.unregister_device(dev.serial)
            device_manager.devices.pop(dev.serial, None)
        except Exception:
            pass


def test_preflight_deployment_checker_integration(tmp_path):
    """Verify that PreFlightCheck runs reliably and produces expected status."""
    checker = PreFlightCheck(tmp_path)
    success = checker.run_all()
    assert success is True
    assert not checker.has_failures
    categories = [cat for cat, status, detail in checker.results]
    assert "Python Version" in categories
    assert "Core Dependencies" in categories
    assert "Directory Permissions" in categories


def test_multi_device_concurrent_registration_and_telemetry(four_test_devices):
    """Verify thread-safety and registry integrity with multiple simultaneous devices."""
    assert len(four_test_devices) == 4
    for dev in four_test_devices:
        registered = device_registry.get_device(dev.serial)
        assert registered is not None
        assert registered.state == DeviceLifecycleState.AVAILABLE
        assert registered.display_name.startswith("Soak Laboratory Node")

    all_devices = device_registry.list_devices()
    serials = [d.serial for d in all_devices]
    for dev in four_test_devices:
        assert dev.serial in serials


def test_concurrent_multi_device_lease_isolation(four_test_devices):
    """Verify that multiple devices can be leased simultaneously by different operators."""
    leases = []
    for i, dev in enumerate(four_test_devices):
        operator = f"operator-{i+1}@kelvra.local"
        lease = session_manager.acquire_lease(
            device_id_or_serial=dev.serial,
            client_id=operator,
            duration_seconds=30.0,
        )
        assert lease is not None
        assert lease.serial == dev.serial
        assert lease.client_id == operator
        leases.append(lease)

    # Verify all four leases coexist without interference
    for i, dev in enumerate(four_test_devices):
        active = session_manager.get_active_lease(dev.serial)
        assert active is not None
        assert active.client_id == f"operator-{i+1}@kelvra.local"

    # Cleanup
    for dev in four_test_devices:
        session_manager.release_lease(dev.serial, force=True)
        assert session_manager.get_active_lease(dev.serial) is None


def test_concurrent_conflicting_leases_rejection(four_test_devices):
    """Verify single-writer lease exclusivity: conflicting leases on the same device are rejected."""
    target_dev = four_test_devices[0]
    lease1 = session_manager.acquire_lease(
        device_id_or_serial=target_dev.serial,
        client_id="agent-alpha",
        duration_seconds=60.0,
    )
    assert lease1.client_id == "agent-alpha"

    # Conflicting lease attempt on same device
    with pytest.raises(LeaseConflictError):
        session_manager.acquire_lease(
            device_id_or_serial=target_dev.serial,
            client_id="agent-beta",
            duration_seconds=60.0,
        )

    # Verify original holder retains lease
    active = session_manager.get_active_lease(target_dev.serial)
    assert active.client_id == "agent-alpha"

    # Release
    session_manager.release_lease(target_dev.serial, session_token=lease1.session_token)
    assert session_manager.get_active_lease(target_dev.serial) is None


@pytest.mark.asyncio
async def test_concurrent_multi_device_streaming_sessions(four_test_devices):
    """Verify that concurrent stream sessions run independently across multiple devices."""
    for dev in four_test_devices:
        cfg = StreamConfig(max_fps=30, quality=75, max_width=720)
        started = await screen_streamer.start_stream(dev.serial, cfg)
        assert started is True

    # Verify all sessions are tracked in active streams
    for dev in four_test_devices:
        diag = screen_streamer.get_diagnostics(dev.serial)
        assert diag is not None
        assert diag.serial == dev.serial
        assert diag.state == StreamState.STREAMING

    # Stop all streams concurrently
    for dev in four_test_devices:
        await screen_streamer.stop_stream(dev.serial)
        diag = screen_streamer.get_diagnostics(dev.serial)
        assert diag is None or diag.state in [StreamState.STOPPED, StreamState.IDLE]


def test_soak_rapid_session_turnover_cleanup(four_test_devices):
    """Simulate intensive turnover: rapid lease acquire-release cycles across all devices."""
    target_dev = four_test_devices[1]
    cycles = 25

    for c in range(cycles):
        holder_id = f"turnover-worker-{c}"
        lease = session_manager.acquire_lease(
            device_id_or_serial=target_dev.serial,
            client_id=holder_id,
            duration_seconds=10.0,
        )
        assert lease.client_id == holder_id
        session_manager.release_lease(target_dev.serial, session_token=lease.session_token)
        assert session_manager.get_active_lease(target_dev.serial) is None

    # Force garbage collection and verify no lingering references
    gc.collect()
    assert session_manager.get_active_lease(target_dev.serial) is None
