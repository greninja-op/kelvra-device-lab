"""
Unit tests for InputController and Telemetry in KELVRA Device Lab.
"""

import pytest
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus
from src.device_telemetry import TelemetryCollector
from src.input_controller import InputController


@pytest.fixture
def mock_device_env():
    manager = DeviceManager()
    dev = DeviceInfo(
        serial="mock-device-input",
        model="POCO X6 Pro 5G",
        manufacturer="Xiaomi",
        android_version="14",
        sdk_level=34,
        battery_level=75,
        battery_temperature=31.2
    )
    manager.add_mock_device(dev)
    controller = InputController(manager)
    telemetry = TelemetryCollector(manager)
    return manager, controller, telemetry, dev.serial


def test_input_actions(mock_device_env):
    manager, controller, telemetry, serial = mock_device_env

    # Tap
    assert controller.tap(serial, 540, 960) is True

    # Swipe
    assert controller.swipe(serial, 540, 1500, 540, 300, 250) is True

    # Keyevents
    assert controller.keyevent(serial, "BACK") is True
    assert controller.keyevent(serial, "HOME") is True
    assert controller.keyevent(serial, 26) is True

    # Text typing
    assert controller.type_text(serial, "Hello Kelvra Device Lab") is True

    # App lifecycle
    assert controller.launch_app(serial, "com.kelvra.mobile") is True
    assert controller.stop_app(serial, "com.kelvra.mobile") is True


def test_screenshot_generation(mock_device_env):
    manager, controller, telemetry, serial = mock_device_env
    screenshot_bytes = controller.take_screenshot(serial, max_width=480, quality=60)
    assert screenshot_bytes is not None
    assert len(screenshot_bytes) > 100


def test_telemetry_collection(mock_device_env):
    manager, controller, telemetry, serial = mock_device_env
    data = telemetry.collect(serial)
    assert data.serial == serial
    assert data.battery_level == 75
    assert data.thermal_status == "NORMAL"
    assert data.storage_total_gb > 0
