"""
Unit tests for BenchBridge and TestRunner in KELVRA Device Lab.
"""

import pytest
from src.bench_bridge import BenchBridge
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus
from src.input_controller import InputController
from src.test_runner import TestRunner


@pytest.fixture
def lab_setup():
    manager = DeviceManager()
    dev = DeviceInfo(serial="mock-bench-dev", model="Companion", status=DeviceStatus.ONLINE)
    manager.add_mock_device(dev)
    controller = InputController(manager)
    bridge = BenchBridge(manager, bench_url="http://127.0.0.1:8099")
    runner = TestRunner(manager, controller)
    return manager, controller, bridge, runner, dev.serial


@pytest.mark.asyncio
async def test_bench_event_publishing(lab_setup):
    manager, controller, bridge, runner, serial = lab_setup
    bridge.sync_enabled = False  # Local queue only

    dev = manager.get_device(serial)
    evt = await bridge.broadcast_device_connected(dev)
    assert evt is not None
    assert evt.event_type == "DEVICE_LAB_DEVICE_CONNECTED"
    assert evt.payload["serial"] == serial
    assert len(bridge._published_events) == 1


@pytest.mark.asyncio
async def test_smoke_test_runner(lab_setup):
    manager, controller, bridge, runner, serial = lab_setup
    report = await runner.run_smoke_test(serial, "com.kelvra.mobile")
    assert report.serial == serial
    assert report.package_name == "com.kelvra.mobile"
    assert report.overall_status == "PASSED"
    assert len(report.steps) == 3
