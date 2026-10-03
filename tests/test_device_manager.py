"""
Unit tests for DeviceManager in KELVRA Device Lab.
"""

import pytest
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus


def test_device_manager_mock_fleet():
    manager = DeviceManager(enable_mock_fallback=True)
    mock_dev = DeviceInfo(
        serial="mock-pixel-8",
        model="Pixel 8 Pro",
        manufacturer="Google",
        market_name="Google Pixel 8 Pro",
        android_version="14",
        sdk_level=34,
        abi="arm64-v8a",
        status=DeviceStatus.ONLINE,
        battery_level=88,
        battery_temperature=28.5,
        screen_width=1344,
        screen_height=2992,
        screen_density=480
    )
    manager.add_mock_device(mock_dev)

    devices = manager.scan_devices()
    assert len(devices) >= 1
    found = [d for d in devices if d.serial == "mock-pixel-8"]
    assert len(found) == 1
    assert found[0].model == "Pixel 8 Pro"
    assert found[0].sdk_level == 34
    assert found[0].battery_level == 88

    fetched = manager.get_device("mock-pixel-8")
    assert fetched is not None
    assert fetched.serial == "mock-pixel-8"

    manager.remove_mock_device("mock-pixel-8")
    assert manager.get_device("mock-pixel-8") is None


def test_device_status_serialization():
    dev = DeviceInfo(serial="test-dev-01", status=DeviceStatus.UNAUTHORIZED)
    data = dev.model_dump()
    assert data["serial"] == "test-dev-01"
    assert data["status"] == "unauthorized"
