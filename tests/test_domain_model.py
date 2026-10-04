"""
Unit tests for Device Domain Model in KELVRA Device Lab.
Adheres strictly to docs/DEVICE_DOMAIN_MODEL.md and Zero Emoji Prohibition.
"""

import pytest
from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)


def test_device_creation_valid():
    device = Device(
        id="android:8TCABAIFWOZTDICI",
        serial="8TCABAIFWOZTDICI",
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Google Pixel 8 Pro",
        manufacturer="Google",
        model="Pixel 8 Pro",
        os_name="Android",
        os_version="14",
        sdk_level=34,
        abi="arm64-v8a",
        transport=ConnectionTransport.USB,
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[DeviceCapability.DISCOVERY, DeviceCapability.SCREEN_STREAM_JPEG]
    )

    assert device.id == "android:8TCABAIFWOZTDICI"
    assert device.serial == "8TCABAIFWOZTDICI"
    assert device.platform == DevicePlatform.ANDROID_PHYSICAL
    assert device.state == DeviceLifecycleState.AVAILABLE
    assert device.has_capability(DeviceCapability.DISCOVERY)
    assert not device.has_capability(DeviceCapability.TOUCH_INTERACTION)


def test_device_id_validation_invalid_format():
    with pytest.raises(ValueError, match="Device ID must be in format"):
        Device(
            id="invalid_id_without_colon",
            serial="serial123",
            provider_id="mock_provider",
            platform=DevicePlatform.ANDROID_PHYSICAL,
            display_name="Test Device"
        )


def test_device_id_validation_empty_parts():
    with pytest.raises(ValueError, match="Device ID prefix and serial cannot be empty"):
        Device(
            id=":serial123",
            serial="serial123",
            provider_id="mock_provider",
            platform=DevicePlatform.ANDROID_PHYSICAL,
            display_name="Test Device"
        )


def test_device_serial_empty_rejection():
    with pytest.raises(ValueError):
        Device(
            id="android:   ",
            serial="   ",
            provider_id="mock_provider",
            platform=DevicePlatform.ANDROID_PHYSICAL,
            display_name="Test Device"
        )


def test_device_capabilities_manipulation():
    device = Device(
        id="android:test-1",
        serial="test-1",
        provider_id="mock_provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Test Device",
        capabilities=[DeviceCapability.DISCOVERY]
    )

    assert device.has_capability(DeviceCapability.DISCOVERY)
    assert not device.has_capability(DeviceCapability.SCREENSHOT_CAPTURE)

    device.add_capability(DeviceCapability.SCREENSHOT_CAPTURE)
    assert device.has_capability(DeviceCapability.SCREENSHOT_CAPTURE)

    # Adding duplicate should not duplicate
    device.add_capability(DeviceCapability.SCREENSHOT_CAPTURE)
    assert device.capabilities.count(DeviceCapability.SCREENSHOT_CAPTURE) == 1


def test_device_error_model():
    err = DeviceError(
        code="ADB_UNAUTHORIZED",
        message="USB debugging not authorized",
        recovery_hint="Unlock phone and tap Accept"
    )
    assert err.code == "ADB_UNAUTHORIZED"
    assert "Unlock" in err.recovery_hint
    assert err.timestamp is not None


def test_device_serialization_round_trip():
    device = Device(
        id="android:round-trip-01",
        serial="round-trip-01",
        provider_id="mock_provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Test Device",
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[DeviceCapability.DISCOVERY, DeviceCapability.TOUCH_INTERACTION]
    )
    data = device.model_dump()
    assert data["id"] == "android:round-trip-01"
    assert data["state"] == "available"

    restored = Device.model_validate(data)
    assert restored.id == device.id
    assert restored.state == device.state
    assert restored.capabilities == device.capabilities
