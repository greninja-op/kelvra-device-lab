"""
Unit and integration tests for Android Physical Device Provider in KELVRA Device Lab.
Adheres strictly to Phase 9 requirements, docs/DEVICE_PROVIDER_CONTRACT.md, and Zero Emoji Prohibition.
"""

import subprocess
import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.android_provider import AndroidDeviceProvider, CommandResult
from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.provider_base import ProviderStatus
from src.server import app, android_provider, device_registry

client = TestClient(app)


def test_adb_executable_resolution_and_validation(tmp_path):
    provider = AndroidDeviceProvider(adb_path=None)

    # Fake executable
    fake_adb = tmp_path / "fake_adb.exe"
    fake_adb.write_text("fake binary")

    ok, msg = provider.configure_adb_path(str(fake_adb))
    # It exists but fails 'adb version'
    assert ok is False
    assert "validation probe" in msg or "failed" in msg

    # Non-existent file
    ok_missing, msg_missing = provider.configure_adb_path(str(tmp_path / "nonexistent.exe"))
    assert ok_missing is False
    assert "does not exist" in msg_missing


def test_adb_command_timeout_and_process_cleanup():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["mock_adb"], timeout=1.0)
        mock_popen.return_value = mock_proc

        res = provider._run_adb_cmd(["shell", "sleep", "10"], timeout=1.0)

        assert res.timed_out is True
        assert res.returncode == -1
        assert "timed out after 1.0s" in res.stderr
        mock_proc.kill.assert_called_once()
        mock_proc.wait.assert_called_once()


def test_adb_bounded_output_reading():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    giant_output = b"A" * 100000  # 100KB output

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (giant_output, b"")
        mock_popen.return_value = mock_proc

        res = provider._run_adb_cmd(["logcat"], timeout=5.0, max_bytes=1024)

        assert res.success is True
        assert len(res.stdout) == 1024  # Truncated strictly at max_bytes


def test_discovery_empty_devices():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_output = (
        "* daemon not running; starting now at tcp:5037\n"
        "* daemon started successfully\n"
        "List of devices attached\n"
        "\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout=mock_output, stderr="")
        devices = provider.discover_devices()

    assert devices == []


def test_discovery_malformed_lines():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_output = (
        "List of devices attached\n"
        "CORRUPTED_LINE_WITHOUT_STATUS\n"
        "   \n"
        "VALID_SERIAL    device usb:1-1 product:panther model:Pixel_7\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout=mock_output, stderr="")
        with patch.object(provider, "_get_device_prop", return_value="Pixel 7"):
            devices = provider.discover_devices()

    assert len(devices) == 1
    assert devices[0].serial == "VALID_SERIAL"


def test_discovery_unauthorized_device_details_and_hint():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_output = (
        "List of devices attached\n"
        "UNAUTH_PHYSICAL_01    unauthorized usb:1-2\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout=mock_output, stderr="")
        devices = provider.discover_devices()

    assert len(devices) == 1
    dev = devices[0]
    assert dev.id == "android:UNAUTH_PHYSICAL_01"
    assert dev.state == DeviceLifecycleState.UNAUTHORIZED
    assert dev.platform == DevicePlatform.ANDROID_PHYSICAL
    assert dev.device_type == DeviceType.PHYSICAL
    assert dev.transport == ConnectionTransport.USB
    assert dev.error is not None
    assert dev.error.code == "ADB_UNAUTHORIZED"
    assert "Unlock the device" in dev.error.recovery_hint


def test_discovery_offline_and_bootloader_states():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_output = (
        "List of devices attached\n"
        "DEV_OFFLINE     offline usb:1-3\n"
        "DEV_FASTBOOT    bootloader usb:1-4\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout=mock_output, stderr="")
        devices = provider.discover_devices()

    assert len(devices) == 2
    d_offline = next(d for d in devices if d.serial == "DEV_OFFLINE")
    assert d_offline.state == DeviceLifecycleState.UNAVAILABLE
    assert d_offline.error.code == "DEVICE_OFFLINE"

    d_bootloader = next(d for d in devices if d.serial == "DEV_FASTBOOT")
    assert d_bootloader.state == DeviceLifecycleState.UNAVAILABLE
    assert d_bootloader.error.code == "ADB_STATE_BOOTLOADER"


def test_metadata_introspection_success_and_caching():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    def mock_prop_fn(serial, prop):
        props = {
            "ro.product.manufacturer": "Motorola",
            "ro.product.model": "Edge 50 Pro",
            "ro.build.version.release": "14",
            "ro.build.version.sdk": "34",
            "ro.product.cpu.abi": "arm64-v8a",
        }
        return props.get(prop)

    with patch.object(provider, "_get_device_prop", side_effect=mock_prop_fn):
        with patch.object(provider, "_get_display_resolution", return_value=(1220, 2712)):
            with patch.object(provider, "_get_display_density", return_value=(446)):
                meta1 = provider._introspect_device("moto-serial-1")
                assert meta1["manufacturer"] == "Motorola"
                assert meta1["model"] == "Edge 50 Pro"
                assert meta1["sdk_level"] == 34
                assert meta1["screen_width"] == 1220
                assert meta1["screen_density"] == 446

                # Second call should read from cache (mock_prop_fn should not be called again)
                with patch.object(provider, "_get_device_prop", side_effect=Exception("Should not be called")):
                    meta2 = provider._introspect_device("moto-serial-1")
                    assert meta2 == meta1

                # Invalidate cache
                provider.invalidate_cache("moto-serial-1")
                assert "moto-serial-1" not in provider._property_cache


def test_metadata_missing_fields_graceful_fallbacks():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    # Property queries return None (e.g. restricted permissions)
    with patch.object(provider, "_get_device_prop", return_value=None):
        with patch.object(provider, "_get_display_resolution", return_value=(1080, 2400)):
            with patch.object(provider, "_get_display_density", return_value=440):
                meta = provider._introspect_device("restricted-dev")
                assert meta["manufacturer"] == "Unknown"
                assert meta["model"] == "Android Device"
                assert meta["sdk_level"] == 0
                assert meta["screen_width"] == 1080


def test_repeated_discovery_duplicate_prevention():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    mock_output = (
        "List of devices attached\n"
        "SERIAL_X    device usb:1-1\n"
        "SERIAL_Y    device usb:1-2\n"
    )

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout=mock_output, stderr="")
        with patch.object(provider, "_introspect_device", return_value={"manufacturer": "Google", "model": "Pixel", "os_version": "14", "sdk_level": 34, "abi": "arm64-v8a"}):
            list1 = provider.discover_devices()
            list2 = provider.discover_devices()

    assert len(list1) == 2
    assert len(list2) == 2
    ids1 = [d.id for d in list1]
    ids2 = [d.id for d in list2]
    assert ids1 == ids2
    assert len(set(ids1)) == 2


def test_safe_read_only_operations():
    provider = AndroidDeviceProvider(adb_path="mock_adb")
    provider._resolved_adb = "mock_adb"
    provider._initialized = True

    with patch.object(provider, "_introspect_device", return_value={"model": "TestModel"}):
        props = provider.get_device_properties("test-serial")
        assert props["model"] == "TestModel"

    with patch.object(provider, "_get_display_resolution", return_value=(1080, 1920)):
        with patch.object(provider, "_get_display_density", return_value=420):
            disp = provider.get_display_info("test-serial")
            assert disp["width"] == 1080
            assert disp["height"] == 1920
            assert disp["density"] == 420

    with patch.object(provider, "_run_adb_cmd") as mock_cmd:
        mock_cmd.return_value = CommandResult(returncode=0, stdout="1\n", stderr="", duration_ms=4.5)
        health = provider.check_device_health("test-serial")
        assert health["responsive"] is True
        assert health["boot_completed"] is True
        assert health["latency_ms"] == 4.5


def test_server_phase9_read_only_endpoints():
    # Setup test device in registry
    test_device = Device(
        id="android:phase9-auth-dev",
        serial="phase9-auth-dev",
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Pixel 8 Pro",
        manufacturer="Google",
        model="Pixel 8 Pro",
        state=DeviceLifecycleState.AVAILABLE
    )
    device_registry.reconcile_discovered_devices("android_adb", [test_device])

    # 1. Properties
    res_props = client.get("/api/devices/android:phase9-auth-dev/properties")
    assert res_props.status_code == 200
    assert "model" in res_props.json()

    # 2. Display
    res_disp = client.get("/api/devices/android:phase9-auth-dev/display")
    assert res_disp.status_code == 200
    assert "width" in res_disp.json()

    # 3. Health
    res_health = client.get("/api/devices/android:phase9-auth-dev/health")
    assert res_health.status_code == 200
    assert "responsive" in res_health.json()

    # 4. Android Provider Health
    res_prov = client.get("/api/providers/android/health")
    assert res_prov.status_code == 200
    assert res_prov.json()["provider_id"] == "android_adb"

    # 5. Unauthorized device 403 protection
    unauth_dev = Device(
        id="android:phase9-unauth-dev",
        serial="phase9-unauth-dev",
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Locked Device",
        state=DeviceLifecycleState.UNAUTHORIZED
    )
    device_registry.reconcile_discovered_devices("android_adb", [test_device, unauth_dev])

    res_unauth_props = client.get("/api/devices/android:phase9-unauth-dev/properties")
    assert res_unauth_props.status_code == 403
    assert "unauthorized" in res_unauth_props.json()["detail"].lower()
