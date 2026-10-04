"""
Automated Test Suite for Phase 12: Apple Physical Device Integration & iOS/iPadOS Capability Investigation.
Tests cover environment detection, tooling discovery, model mapping, pairing/trust states,
capability matrices, registry integration, and REST endpoints.
Adheres strictly to Zero Emoji Prohibition.
"""

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.apple_provider import (
    AppleCapabilityItem,
    AppleDeviceModelMapper,
    AppleDeviceProvider,
    AppleEnvironmentDetector,
    AppleEnvironmentStatus,
    ApplePairingState,
    CapabilityStatus,
)
from src.device_registry import DeviceRegistry
from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.provider_base import ProviderStatus
from src.server import app, apple_provider as server_apple_provider, device_registry as server_device_registry


@pytest.fixture
def temp_lockdown_dir():
    d = tempfile.mkdtemp(prefix="kelvra_test_lockdown_")
    # Write a test pairing plist
    with open(os.path.join(d, "00008030-001144A83653C02E.plist"), "w") as f:
        f.write("<plist><dict></dict></plist>")
    with open(os.path.join(d, "SystemConfiguration.plist"), "w") as f:
        f.write("<plist><dict></dict></plist>")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def temp_tools_dir():
    d = tempfile.mkdtemp(prefix="kelvra_test_tools_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_apple_device():
    return Device(
        id="apple:00008030-001144A83653C02E",
        serial="00008030-001144A83653C02E",
        provider_id="apple_device_provider",
        platform=DevicePlatform.APPLE_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="iPhone 15 Pro",
        manufacturer="Apple",
        model="iPhone 15 Pro",
        os_name="iOS",
        os_version="17.5.1",
        abi="arm64",
        transport=ConnectionTransport.USB,
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[
            DeviceCapability.DISCOVERY,
            DeviceCapability.TELEMETRY_POLLING,
            DeviceCapability.LOGCAT_STREAMING,
            DeviceCapability.SCREENSHOT_CAPTURE,
        ],
        metadata={
            "udid": "00008030-001144A83653C02E",
            "product_type": "iPhone16,1",
            "form_factor": "iPhone",
            "pairing_state": "paired",
            "hardware_platform": "Apple Silicon",
        },
    )


# ==============================================================================
# 1. Environment Detector Tests
# ==============================================================================

def test_apple_environment_detector_default():
    """Verifies default environment detector runs without throwing exceptions."""
    detector = AppleEnvironmentDetector()
    status = detector.detect()
    assert isinstance(status, AppleEnvironmentStatus)
    assert status.host_os in ["Windows", "Darwin", "Linux"]
    assert isinstance(status.guidance, list)


def test_apple_environment_detector_with_overrides(temp_lockdown_dir, temp_tools_dir):
    """Verifies detector inspects custom lockdown and tools directories deterministically."""
    # Create dummy executable in tools dir
    dummy_exe = os.path.join(temp_tools_dir, "idevice_id.bat" if os.name == "nt" else "idevice_id")
    with open(dummy_exe, "w") as f:
        f.write("@echo off\n" if os.name == "nt" else "#!/bin/sh\n")
    os.chmod(dummy_exe, 0o755)

    detector = AppleEnvironmentDetector(
        custom_lockdown_dir=temp_lockdown_dir,
        custom_tools_dir=temp_tools_dir,
        override_os="Windows",
        override_usbmux_port=65432,  # Unused port to guarantee closed
    )
    status = detector.detect()
    assert status.host_os == "Windows"
    assert status.is_macos is False
    assert status.lockdown_dir_exists is True
    assert status.paired_records_count == 1  # 00008030...plist counted, SystemConfiguration skipped
    assert status.idevice_id_path is not None


def test_apple_environment_detector_darwin_guidance():
    """Verifies macOS host detection recognizes native platform."""
    detector = AppleEnvironmentDetector(override_os="Darwin")
    status = detector.detect()
    assert status.is_macos is True
    # Guidance should not include Windows-specific warnings
    for g in status.guidance:
        assert "Windows host limitation" not in g


# ==============================================================================
# 2. Model Mapper Tests
# ==============================================================================

def test_apple_model_mapper():
    """Verifies Apple ProductType mappings to commercial marketing names."""
    # Known iPhones
    name, form = AppleDeviceModelMapper.resolve_model("iPhone16,1")
    assert name == "iPhone 15 Pro"
    assert form == "iPhone"

    name, form = AppleDeviceModelMapper.resolve_model("iPhone15,2")
    assert name == "iPhone 14 Pro"
    assert form == "iPhone"

    # Known iPads
    name, form = AppleDeviceModelMapper.resolve_model("iPad13,16")
    assert name == "iPad Air (5th gen)"
    assert form == "iPad"

    name, form = AppleDeviceModelMapper.resolve_model("iPad14,5")
    assert name == "iPad Pro 12.9-inch (6th gen)"
    assert form == "iPad"

    # Unknown product type fallback
    name, form = AppleDeviceModelMapper.resolve_model("iPhone99,9")
    assert name == "Apple iPhone99,9"
    assert form == "iPhone"

    name, form = AppleDeviceModelMapper.resolve_model("iPad99,1")
    assert name == "Apple iPad99,1"
    assert form == "iPad"

    # None / Empty
    name, form = AppleDeviceModelMapper.resolve_model(None)
    assert name == "Apple Device"
    assert form == "iPhone"


# ==============================================================================
# 3. Apple Device Provider & Discovery Tests
# ==============================================================================

def test_apple_provider_initialization():
    """Verifies provider initializes and reports health without crashing."""
    detector = AppleEnvironmentDetector()
    provider = AppleDeviceProvider(detector=detector)
    assert provider.provider_id == "apple_device_provider"
    assert provider.platform == DevicePlatform.APPLE_PHYSICAL
    assert provider.initialize() is True

    health = provider.get_health()
    assert health.provider_id == "apple_device_provider"
    assert health.status in [ProviderStatus.READY, ProviderStatus.DEGRADED]


def test_apple_provider_mock_seeding(mock_apple_device):
    """Verifies mock devices can be seeded and enumerated by provider."""
    provider = AppleDeviceProvider(mock_devices=[mock_apple_device])
    devices = provider.discover_devices()
    assert len(devices) == 1
    assert devices[0].id == "apple:00008030-001144A83653C02E"
    assert devices[0].model == "iPhone 15 Pro"
    assert devices[0].os_name == "iOS"
    assert devices[0].platform == DevicePlatform.APPLE_PHYSICAL

    provider.clear_mock_devices()
    assert len(provider.discover_devices()) == 0


def test_apple_provider_discovery_subprocess_mock():
    """Simulates idevice_id and ideviceinfo subprocess discovery."""
    detector = MagicMock(spec=AppleEnvironmentDetector)
    status = AppleEnvironmentStatus(
        host_os="Windows",
        is_macos=False,
        usbmuxd_available=True,
        usbmuxd_port_active=True,
        lockdown_dir_exists=True,
        paired_records_count=1,
        idevice_id_path="C:\\tools\\idevice_id.exe",
        ideviceinfo_path="C:\\tools\\ideviceinfo.exe",
        pymobiledevice3_available=False,
        toolchain_type="libimobiledevice",
        guidance=[],
    )
    detector.detect.return_value = status

    provider = AppleDeviceProvider(detector=detector)

    # Mock subprocess.run for idevice_id -l and ideviceinfo
    with patch("subprocess.run") as mock_run:
        # First call: idevice_id -l -> returns 1 UDID
        # Second call: ideviceinfo -u -> returns key-value properties
        mock_id_res = MagicMock(returncode=0, stdout="00008030-001144A83653C02E\n", stderr="")
        mock_info_res = MagicMock(
            returncode=0,
            stdout="ProductType: iPhone16,1\nDeviceName: Athul's iPhone\nProductVersion: 17.5.1\nCPUArchitecture: arm64\nWiFiAddress: 00:11:22:33:44:55\n",
            stderr="",
        )
        mock_run.side_effect = [mock_id_res, mock_info_res]

        devices = provider.discover_devices()
        assert len(devices) == 1
        dev = devices[0]
        assert dev.id == "apple:00008030-001144A83653C02E"
        assert dev.display_name == "Athul's iPhone"
        assert dev.model == "iPhone 15 Pro"
        assert dev.os_name == "iOS"
        assert dev.os_version == "17.5.1"
        assert dev.state == DeviceLifecycleState.AVAILABLE


def test_apple_device_passcode_locked_state():
    """Verifies passcode-locked device transitions to UNAUTHORIZED with actionable error."""
    detector = MagicMock(spec=AppleEnvironmentDetector)
    status = AppleEnvironmentStatus(
        host_os="Windows",
        is_macos=False,
        usbmuxd_available=True,
        usbmuxd_port_active=True,
        lockdown_dir_exists=True,
        toolchain_type="libimobiledevice",
        idevice_id_path="C:\\tools\\idevice_id.exe",
        ideviceinfo_path="C:\\tools\\ideviceinfo.exe",
    )
    detector.detect.return_value = status
    provider = AppleDeviceProvider(detector=detector)

    with patch("subprocess.run") as mock_run:
        mock_id_res = MagicMock(returncode=0, stdout="00008030-001144A83653C02E\n", stderr="")
        mock_info_res = MagicMock(
            returncode=1,
            stdout="",
            stderr="ERROR: Could not connect to lockdownd: PasswordProtected",
        )
        mock_run.side_effect = [mock_id_res, mock_info_res]

        devices = provider.discover_devices()
        assert len(devices) == 1
        dev = devices[0]
        assert dev.state == DeviceLifecycleState.UNAUTHORIZED
        assert dev.error is not None
        assert dev.error.code == "APPLE_PASSCODE_LOCKED"
        assert "passcode" in dev.error.recovery_hint.lower()


def test_apple_device_trust_required_state():
    """Verifies unverified pairing trust transitions to UNAUTHORIZED with trust recovery hint."""
    detector = MagicMock(spec=AppleEnvironmentDetector)
    status = AppleEnvironmentStatus(
        host_os="Windows",
        is_macos=False,
        usbmuxd_available=True,
        usbmuxd_port_active=True,
        lockdown_dir_exists=True,
        toolchain_type="libimobiledevice",
        idevice_id_path="C:\\tools\\idevice_id.exe",
        ideviceinfo_path="C:\\tools\\ideviceinfo.exe",
    )
    detector.detect.return_value = status
    provider = AppleDeviceProvider(detector=detector)

    with patch("subprocess.run") as mock_run:
        mock_id_res = MagicMock(returncode=0, stdout="00008030-001144A83653C02E\n", stderr="")
        mock_info_res = MagicMock(
            returncode=1,
            stdout="",
            stderr="ERROR: Could not connect to lockdownd: PairingDialogResponsePending (Trust dialog on screen)",
        )
        mock_run.side_effect = [mock_id_res, mock_info_res]

        devices = provider.discover_devices()
        assert len(devices) == 1
        dev = devices[0]
        assert dev.state == DeviceLifecycleState.UNAUTHORIZED
        assert dev.error is not None
        assert dev.error.code == "APPLE_TRUST_REQUIRED"
        assert "Trust This Computer" in dev.error.recovery_hint


# ==============================================================================
# 4. Capability Model Tests
# ==============================================================================

def test_apple_capabilities_matrix():
    """Verifies Apple device exposes only verified capabilities; streaming and touch are excluded."""
    provider = AppleDeviceProvider()
    caps = provider.get_capabilities("apple:00008030-001144A83653C02E")

    # Verified capabilities
    assert DeviceCapability.DISCOVERY in caps
    assert DeviceCapability.TELEMETRY_POLLING in caps
    assert DeviceCapability.LOGCAT_STREAMING in caps
    assert DeviceCapability.SCREENSHOT_CAPTURE in caps

    # Prohibited / Unsupported capabilities on Apple in MVP
    assert DeviceCapability.SCREEN_STREAM_JPEG not in caps
    assert DeviceCapability.SCREEN_STREAM_H264 not in caps
    assert DeviceCapability.TOUCH_INTERACTION not in caps
    assert DeviceCapability.KEYBOARD_INJECTION not in caps
    assert DeviceCapability.TEST_AUTOMATION not in caps


def test_apple_detailed_capabilities_reporting():
    """Verifies detailed capabilities report contains all 11 audited capabilities with statuses."""
    provider = AppleDeviceProvider()
    detailed = provider.get_detailed_capabilities()
    assert len(detailed) == 11

    caps_map = {item.capability: item for item in detailed}
    assert caps_map["Device Discovery"].status == CapabilityStatus.SUPPORTED
    assert caps_map["Hardware Metadata & Identity"].status == CapabilityStatus.SUPPORTED
    assert caps_map["Touch Interaction & Gestures"].status == CapabilityStatus.UNAVAILABLE
    assert caps_map["Live Screen Viewing (Baseline JPEG)"].status == CapabilityStatus.UNAVAILABLE
    assert caps_map["UI Test Automation"].status == CapabilityStatus.DEFERRED


# ==============================================================================
# 5. Connection & Session Tests
# ==============================================================================

def test_apple_connect_authorized(mock_apple_device):
    """Verifies connecting an authorized Apple device establishes session."""
    provider = AppleDeviceProvider(mock_devices=[mock_apple_device])
    assert provider.connect(mock_apple_device.id) is True
    assert provider.disconnect(mock_apple_device.id) is True
    assert provider.disconnect(mock_apple_device.id) is False


def test_apple_connect_unauthorized_blocked(mock_apple_device):
    """Verifies connecting an unauthorized/unpaired Apple device is rejected."""
    mock_apple_device.state = DeviceLifecycleState.UNAUTHORIZED
    mock_apple_device.error = DeviceError(code="APPLE_TRUST_REQUIRED", message="Trust prompt pending")
    provider = AppleDeviceProvider(mock_devices=[mock_apple_device])

    assert provider.connect(mock_apple_device.id) is False


# ==============================================================================
# 6. Device Registry Integration Tests
# ==============================================================================

def test_apple_device_registry_integration(mock_apple_device):
    """Verifies Apple device integrates cleanly into DeviceRegistry."""
    registry = DeviceRegistry()
    provider = AppleDeviceProvider(mock_devices=[mock_apple_device])
    registry.register_provider(provider)

    devices = registry.reconcile()
    assert len(devices) == 1
    stored = registry.get_device(mock_apple_device.id)
    assert stored is not None
    assert stored.platform == DevicePlatform.APPLE_PHYSICAL
    assert stored.display_name == "iPhone 15 Pro"

    # Verify stats
    stats = registry.get_stats()
    assert stats["total"] == 1
    assert stats["online"] == 1


# ==============================================================================
# 7. REST API Endpoints Tests
# ==============================================================================

def test_api_apple_health():
    """Tests GET /api/providers/apple/health."""
    client = TestClient(app)
    res = client.get("/api/providers/apple/health")
    assert res.status_code == 200
    data = res.json()
    assert data["provider_id"] == "apple_device_provider"
    assert data["status"] in ["ready", "degraded"]
    assert "usbmuxd_port_active" in data["details"]


def test_api_apple_capabilities():
    """Tests GET /api/providers/apple/capabilities."""
    client = TestClient(app)
    res = client.get("/api/providers/apple/capabilities")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) == 11
    # Check that touch interaction is reported as unavailable on Windows host
    touch = next((item for item in items if item["capability"] == "Touch Interaction & Gestures"), None)
    assert touch is not None
    assert touch["status"] == "unavailable"


def test_api_apple_trust_and_pair_endpoints(mock_apple_device):
    """Tests GET /api/devices/{id}/apple/trust and POST /api/devices/{id}/apple/pair."""
    server_apple_provider.seed_mock_device(mock_apple_device)
    server_device_registry.reconcile()

    client = TestClient(app)
    try:
        # 1. Trust endpoint
        res = client.get(f"/api/devices/{mock_apple_device.id}/apple/trust")
        assert res.status_code == 200
        data = res.json()
        assert data["device_id"] == mock_apple_device.id
        assert data["is_authorized"] is True
        assert data["pairing_state"] == "paired"

        # 2. Pair endpoint
        res = client.post(f"/api/devices/{mock_apple_device.id}/apple/pair")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "paired"

        # 3. Test unauthorized rejection
        unauth_device = mock_apple_device.model_copy()
        unauth_device.id = "apple:00008030-UNAUTHORIZED"
        unauth_device.state = DeviceLifecycleState.UNAUTHORIZED
        unauth_device.metadata["pairing_state"] = "unpaired"
        server_apple_provider.seed_mock_device(unauth_device)
        server_device_registry.reconcile()

        res_fail = client.post(f"/api/devices/{unauth_device.id}/apple/pair")
        assert res_fail.status_code == 403
    finally:
        server_apple_provider.clear_mock_devices()
        server_device_registry.reconcile()
