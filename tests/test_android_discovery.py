"""
Unit tests for Android ADB Device Discovery and Property Introspection.
Adheres strictly to docs/ANDROID_DISCOVERY.md and Zero Emoji Prohibition.
"""

from unittest.mock import MagicMock, patch
import subprocess
import pytest
from src.domain_model import (
    ConnectionTransport,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.android_provider import AndroidDeviceProvider
from src.provider_base import ProviderStatus


def test_android_provider_health_missing_adb():
    provider = AndroidDeviceProvider(adb_path="/non/existent/path/to/adb")
    health = provider.get_health()
    assert health.status == ProviderStatus.UNAVAILABLE
    assert "executable was not found" in health.message


def test_android_provider_discovery_parsing_authorized_device():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_adb_devices_output = (
        "List of devices attached\n"
        "8TCABAIFWOZTDICI       device usb:1-1 product:oriole model:Pixel_6 device:oriole\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["mock_adb", "devices", "-l"],
            returncode=0,
            stdout=mock_adb_devices_output,
            stderr=""
        )
        with patch.object(provider, "_get_device_prop") as mock_prop:
            def prop_side_effect(serial, prop):
                props = {
                    "ro.product.manufacturer": "Google",
                    "ro.product.model": "Pixel 6",
                    "ro.build.version.release": "14",
                    "ro.build.version.sdk": "34",
                    "ro.product.cpu.abi": "arm64-v8a",
                }
                return props.get(prop)
            mock_prop.side_effect = prop_side_effect

            devices = provider.discover_devices()

    assert len(devices) == 1
    dev = devices[0]
    assert dev.id == "android:8TCABAIFWOZTDICI"
    assert dev.serial == "8TCABAIFWOZTDICI"
    assert dev.manufacturer == "Google"
    assert dev.model == "Pixel 6"
    assert dev.sdk_level == 34
    assert dev.state == DeviceLifecycleState.AVAILABLE
    assert dev.transport == ConnectionTransport.USB
    assert dev.device_type == DeviceType.PHYSICAL


def test_android_provider_discovery_parsing_unauthorized_device():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_adb_output = (
        "List of devices attached\n"
        "UNAUTH12345            unauthorized usb:2-1\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["mock_adb", "devices", "-l"],
            returncode=0,
            stdout=mock_adb_output,
            stderr=""
        )
        devices = provider.discover_devices()

    assert len(devices) == 1
    dev = devices[0]
    assert dev.id == "android:UNAUTH12345"
    assert dev.state == DeviceLifecycleState.UNAUTHORIZED
    assert dev.error is not None
    assert dev.error.code == "ADB_UNAUTHORIZED"
    assert "Unlock the device" in dev.error.recovery_hint


def test_android_provider_discovery_parsing_offline_device():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_adb_output = (
        "List of devices attached\n"
        "OFFLINE999             offline usb:3-1\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["mock_adb", "devices", "-l"],
            returncode=0,
            stdout=mock_adb_output,
            stderr=""
        )
        devices = provider.discover_devices()

    assert len(devices) == 1
    dev = devices[0]
    assert dev.id == "android:OFFLINE999"
    assert dev.state == DeviceLifecycleState.UNAVAILABLE
    assert dev.error is not None
    assert dev.error.code == "DEVICE_OFFLINE"


def test_android_provider_discovery_network_and_emulator():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_adb_output = (
        "List of devices attached\n"
        "192.168.1.105:5555     device product:coral\n"
        "emulator-5554          device product:sdk_gphone64_x86_64\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["mock_adb", "devices", "-l"],
            returncode=0,
            stdout=mock_adb_output,
            stderr=""
        )
        with patch.object(provider, "_get_device_prop", return_value="Test"):
            devices = provider.discover_devices()

    assert len(devices) == 2
    wifi_dev = next(d for d in devices if d.serial == "192.168.1.105:5555")
    assert wifi_dev.transport == ConnectionTransport.WIFI
    assert wifi_dev.device_type == DeviceType.PHYSICAL

    emu_dev = next(d for d in devices if d.serial == "emulator-5554")
    assert emu_dev.transport == ConnectionTransport.EMULATOR_PIPE
    assert emu_dev.device_type == DeviceType.VIRTUAL
    assert emu_dev.platform == DevicePlatform.ANDROID_VIRTUAL
