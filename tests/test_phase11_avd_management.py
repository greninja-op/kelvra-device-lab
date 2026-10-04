"""
Automated Test Suite for Phase 11: Android Virtual Device Management & Emulator Lifecycle.
Covers SDK environment detection, AVD inventory parsing, creation validation,
emulator launch & shutdown, duplicate launch prevention, boot sequence monitoring,
Device Registry integration, process safety, and REST endpoints.
Adheres strictly to Zero Emoji Prohibition.
"""

import asyncio
import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.avd_manager import (
    AvdConfig,
    AvdManager,
    AvdStatus,
    CreateAvdRequest,
    EmulatorLaunchOptions,
    EmulatorSession,
    SdkEnvironmentDetector,
    SdkEnvironmentStatus,
)
from src.device_registry import DeviceRegistry
from src.domain_model import (
    Device,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.server import app, avd_manager as server_avd_manager


@pytest.fixture
def temp_avd_dir():
    d = tempfile.mkdtemp(prefix="kelvra_test_avd_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_sdk_dir():
    d = tempfile.mkdtemp(prefix="kelvra_test_sdk_")
    # Setup dummy directory structure
    os.makedirs(os.path.join(d, "platform-tools"), exist_ok=True)
    os.makedirs(os.path.join(d, "emulator"), exist_ok=True)
    os.makedirs(os.path.join(d, "cmdline-tools", "latest", "bin"), exist_ok=True)
    os.makedirs(os.path.join(d, "system-images", "android-34", "google_apis", "x86_64"), exist_ok=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def registry():
    return DeviceRegistry()


# --- 1. ENVIRONMENT DETECTION TESTS ---

def test_sdk_unavailable_handling():
    """Confirms clean handling when Android SDK root is not found."""
    detector = SdkEnvironmentDetector(custom_sdk_root="/non/existent/path/to/sdk")
    status = detector.detect_environment()
    assert not status.sdk_detected
    assert not status.emulator_available
    assert "Android SDK root not found" in (status.setup_guidance or "")


def test_sdk_detected_with_tools(mock_sdk_dir, temp_avd_dir):
    """Confirms discovery of SDK paths, system images, and tools when present."""
    # Create dummy emulator and adb binaries
    adb_file = os.path.join(mock_sdk_dir, "platform-tools", "adb.exe" if os.name == "nt" else "adb")
    with open(adb_file, "w") as f:
        f.write("#!/bin/sh\nexit 0")
    emu_file = os.path.join(mock_sdk_dir, "emulator", "emulator.exe" if os.name == "nt" else "emulator")
    with open(emu_file, "w") as f:
        f.write("#!/bin/sh\nexit 0")

    detector = SdkEnvironmentDetector(
        custom_sdk_root=mock_sdk_dir,
        custom_avd_home=temp_avd_dir,
        custom_adb_path=adb_file,
        custom_emulator_path=emu_file,
    )
    status = detector.detect_environment()
    assert status.sdk_detected
    assert status.adb_available
    assert status.emulator_available
    assert "android-34;google_apis;x86_64" in status.system_images
    assert status.avd_home == temp_avd_dir


def test_emulator_executable_unavailable(mock_sdk_dir):
    """Confirms reporting when SDK is detected but emulator binary is missing."""
    detector = SdkEnvironmentDetector(custom_sdk_root=mock_sdk_dir)
    status = detector.detect_environment()
    assert status.sdk_detected
    assert not status.emulator_available
    assert "Android Emulator binary missing" in (status.setup_guidance or "")


# --- 2. INVENTORY & CONFIGURATION PARSING TESTS ---

def test_empty_avd_inventory(temp_avd_dir):
    """Confirms honest empty list returned when no AVDs exist."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    avds = mgr.list_avds()
    assert avds == []


def test_avd_inventory_parsing(temp_avd_dir):
    """Parses .ini and config.ini into strongly typed AvdConfig."""
    # Write test Pixel_7.ini
    ini_path = os.path.join(temp_avd_dir, "Pixel_7.ini")
    avd_folder = os.path.join(temp_avd_dir, "Pixel_7.avd")
    os.makedirs(avd_folder, exist_ok=True)
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write(f"path={avd_folder}\ntarget=android-34\n")

    # Write config.ini inside Pixel_7.avd
    config_ini = os.path.join(avd_folder, "config.ini")
    with open(config_ini, "w", encoding="utf-8") as f:
        f.write("image.sysdir.1=system-images/android-34/google_apis/x86_64/\n")
        f.write("abi.type=x86_64\n")
        f.write("hw.device.name=pixel_7\n")
        f.write("hw.ramSize=4096\n")

    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    avds = mgr.list_avds()
    assert len(avds) == 1
    avd = avds[0]
    assert avd.name == "Pixel_7"
    assert avd.abi == "x86_64"
    assert avd.device_profile == "pixel_7"
    assert avd.ram_size == "4096MB"
    assert avd.status == AvdStatus.STOPPED


def test_invalid_avd_configuration(temp_avd_dir):
    """Gracefully handles corrupt or malformed .ini files."""
    ini_path = os.path.join(temp_avd_dir, "Corrupt_Avd.ini")
    with open(ini_path, "w", encoding="utf-8") as f:
        f.write("corrupted content without key-value delimiters\n")

    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    # Does not crash; skips corrupt entry
    avds = mgr.list_avds()
    assert len(avds) == 0


# --- 3. CREATION VALIDATION & ERROR HANDLING ---

def test_create_avd_name_validation():
    """Validates AVD name rejects path traversal and illegal characters."""
    mgr = AvdManager()
    # Path traversal attempt
    with pytest.raises(ValueError, match="path separators"):
        mgr.create_avd(CreateAvdRequest(name="../hacked", system_image="img"))

    # Illegal symbols
    with pytest.raises(ValueError, match="Invalid AVD name"):
        mgr.create_avd(CreateAvdRequest(name="bad name with spaces!", system_image="img"))


def test_create_avd_duplicate_prevention(temp_avd_dir):
    """Rejects duplicate AVD name when force=False."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    mgr.add_mock_avd(AvdConfig(name="Existing_AVD", path=temp_avd_dir))

    with pytest.raises(ValueError, match="already exists"):
        mgr.create_avd(CreateAvdRequest(name="Existing_AVD", system_image="img", force=False))


def test_create_avd_missing_system_image():
    """Fails with descriptive error when required system image is not downloaded."""
    detector = SdkEnvironmentDetector(custom_sdk_root="/empty")
    mgr = AvdManager(sdk_detector=detector)
    with pytest.raises(RuntimeError, match="avdmanager' tool is missing"):
        mgr.create_avd(CreateAvdRequest(name="New_AVD", system_image="system-images;android-34;google_apis;x86_64"))


# --- 4. EMULATOR LIFECYCLE & PROCESS ORCHESTRATION ---

@pytest.mark.asyncio
async def test_emulator_launch_missing_binary(temp_avd_dir):
    """Rejects launch if emulator executable is not present on host."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    mgr.add_mock_avd(AvdConfig(name="Pixel_7", path=temp_avd_dir))

    with pytest.raises(RuntimeError, match="Emulator executable missing"):
        await mgr.launch_emulator("Pixel_7")


@pytest.mark.asyncio
async def test_emulator_duplicate_launch_prevention(temp_avd_dir):
    """Rejects secondary launch if an AVD emulator process is already active."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    mgr.add_mock_avd(AvdConfig(name="Pixel_7", path=temp_avd_dir))

    # Pre-register an active session
    fake_session = EmulatorSession("Pixel_7", EmulatorLaunchOptions(), pid=9999)
    fake_session.state = AvdStatus.READY
    mgr._sessions["Pixel_7"] = fake_session

    with pytest.raises(ValueError, match="already running"):
        await mgr.launch_emulator("Pixel_7")


@pytest.mark.asyncio
async def test_boot_sequence_and_registry_integration(temp_avd_dir, registry):
    """Simulates background boot sequence, verifying transition to READY and registry registration."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)

    # Mock ADB query outputs
    def fake_adb_runner(args, timeout):
        if args == ["devices"]:
            return 0, "List of devices attached\nemulator-5554\tdevice\n", ""
        if "-s" in args and "ro.boot.qemu.avd_name" in args:
            return 0, "Test_Pixel\n", ""
        if "-s" in args and "sys.boot_completed" in args:
            return 0, "1\n", ""
        return 0, "", ""

    mgr = AvdManager(sdk_detector=detector, device_registry=registry, adb_runner=fake_adb_runner)
    mgr.add_mock_avd(AvdConfig(name="Test_Pixel", path=temp_avd_dir))

    # Create mock session
    fake_proc = MagicMock()
    fake_proc.pid = 1234
    fake_proc.poll.return_value = None

    session = EmulatorSession("Test_Pixel", EmulatorLaunchOptions(), pid=1234, process=fake_proc)
    mgr._sessions["Test_Pixel"] = session

    # Run boot tracking loop
    await mgr._track_boot_sequence(session)

    assert session.state == AvdStatus.READY
    assert session.serial == "emulator-5554"
    assert session.boot_completed_at is not None

    # Check Device Registry integration
    dev = registry.get_device("android:emulator-5554")
    assert dev is not None
    assert dev.serial == "emulator-5554"
    assert dev.platform == DevicePlatform.ANDROID_VIRTUAL
    assert dev.device_type == DeviceType.VIRTUAL
    assert dev.state == DeviceLifecycleState.AVAILABLE


@pytest.mark.asyncio
async def test_emulator_process_crash_handling(temp_avd_dir, registry):
    """Detects early emulator process termination and records failure details."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector, device_registry=registry)

    # Process that immediately exits with returncode 1
    fake_proc = MagicMock()
    fake_proc.poll.return_value = 1
    fake_proc.stderr.read.return_value = b"PANIC: Cannot find AVD system path"

    session = EmulatorSession("Crash_AVD", EmulatorLaunchOptions(), pid=5555, process=fake_proc)
    mgr._sessions["Crash_AVD"] = session

    await mgr._track_boot_sequence(session)

    assert session.state == AvdStatus.FAILED
    assert "exit code 1" in session.error_message
    assert "PANIC" in session.error_message


@pytest.mark.asyncio
async def test_emulator_shutdown(temp_avd_dir, registry):
    """Gracefully terminates emulator session and cleans up registry state."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)

    def fake_adb_runner(args, timeout):
        return 0, "OK\n", ""

    mgr = AvdManager(sdk_detector=detector, device_registry=registry, adb_runner=fake_adb_runner)

    fake_proc = MagicMock()
    fake_proc.poll.return_value = None

    session = EmulatorSession("Pixel_Stop", EmulatorLaunchOptions(), pid=7777, process=fake_proc)
    session.serial = "emulator-5554"
    session.state = AvdStatus.READY
    mgr._sessions["Pixel_Stop"] = session

    # Pre-register device in registry
    dev = Device(
        id="android:emulator-5554",
        serial="emulator-5554",
        display_name="Pixel_Stop",
        provider_id="android_avd",
        platform=DevicePlatform.ANDROID_VIRTUAL,
        device_type=DeviceType.VIRTUAL,
        state=DeviceLifecycleState.AVAILABLE,
    )
    registry.register_device(dev)

    # Stop emulator
    ok = await mgr.stop_emulator("Pixel_Stop")
    assert ok
    assert "Pixel_Stop" not in mgr._sessions

    # Device in registry transitioned to UNAVAILABLE
    updated_dev = registry.get_device("android:emulator-5554")
    assert updated_dev.state == DeviceLifecycleState.UNAVAILABLE


def test_delete_avd_confirmation_required(temp_avd_dir):
    """Refuses deletion unless confirm=True is explicitly supplied."""
    detector = SdkEnvironmentDetector(custom_avd_home=temp_avd_dir)
    mgr = AvdManager(sdk_detector=detector)
    mgr.add_mock_avd(AvdConfig(name="Protected_AVD", path=temp_avd_dir))

    with pytest.raises(ValueError, match="Explicit confirmation required"):
        mgr.delete_avd("Protected_AVD", confirm=False)

    # Deletes cleanly when confirm=True
    deleted = mgr.delete_avd("Protected_AVD", confirm=True)
    assert deleted
    assert mgr.get_avd("Protected_AVD") is None


# --- 5. REST API ENDPOINTS VERIFICATION ---

client = TestClient(app)


def test_api_avd_environment():
    """Validates GET /api/avd/environment endpoint."""
    res = client.get("/api/avd/environment")
    assert res.status_code == 200
    data = res.json()
    assert "sdk_detected" in data
    assert "adb_available" in data
    assert "emulator_available" in data
    assert "setup_guidance" in data


def test_api_avd_list_and_get():
    """Validates GET /api/avd/list and GET /api/avd/{name}."""
    server_avd_manager.clear_mock_avds()
    server_avd_manager.add_mock_avd(
        AvdConfig(
            name="Mock_Pixel_8",
            path="/tmp/mock_pixel_8",
            target="Android 14.0",
            abi="arm64-v8a",
            device_profile="pixel_8",
            status=AvdStatus.STOPPED,
        )
    )

    res = client.get("/api/avd/list")
    assert res.status_code == 200
    avds = res.json()
    assert any(a["name"] == "Mock_Pixel_8" for a in avds)

    res_single = client.get("/api/avd/Mock_Pixel_8")
    assert res_single.status_code == 200
    single_avd = res_single.json()
    assert single_avd["name"] == "Mock_Pixel_8"
    assert single_avd["device_profile"] == "pixel_8"

    res_404 = client.get("/api/avd/NonExistentAvd")
    assert res_404.status_code == 404


def test_api_avd_delete_requires_confirmation():
    """Validates DELETE /api/avd/{name} requires confirm=true."""
    server_avd_manager.add_mock_avd(
        AvdConfig(name="To_Delete", path="/tmp/to_delete", status=AvdStatus.STOPPED)
    )

    # Without confirmation
    res_no_confirm = client.delete("/api/avd/To_Delete")
    assert res_no_confirm.status_code == 400

    # With confirmation
    res_confirm = client.delete("/api/avd/To_Delete?confirm=true")
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "deleted"
