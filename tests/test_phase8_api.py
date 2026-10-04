"""
Integration tests for Phase 8 FastAPI Device Inventory and Connection Management endpoints.
Adheres strictly to docs/DEVICE_INVENTORY_IMPLEMENTATION.md and Zero Emoji Prohibition.
"""

import pytest
from fastapi.testclient import TestClient
from src.domain_model import (
    Device,
    DeviceCapability,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.server import app, device_registry, mock_provider

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_phase8_test_devices():
    mock_provider.clear()
    
    # 1. Available physical device
    dev1 = Device(
        id="android:phase8-dev-01",
        serial="phase8-dev-01",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel 8 Pro Test",
        manufacturer="Google",
        model="Pixel 8 Pro",
        state=DeviceLifecycleState.AVAILABLE,
        capabilities=[DeviceCapability.DISCOVERY, DeviceCapability.SCREEN_STREAM_JPEG]
    )
    mock_provider.add_device(dev1)

    # 2. Unauthorized physical device
    dev2 = Device(
        id="android:phase8-unauth-02",
        serial="phase8-unauth-02",
        provider_id=mock_provider.provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Samsung S24 Ultra",
        manufacturer="Samsung",
        model="SM-S928B",
        state=DeviceLifecycleState.UNAUTHORIZED,
        capabilities=[DeviceCapability.DISCOVERY]
    )
    mock_provider.add_device(dev2)

    # Sync into registry
    device_registry.reconcile_discovered_devices(mock_provider.provider_id, mock_provider.discover_devices())

    yield

    mock_provider.clear()
    device_registry.reconcile_discovered_devices(mock_provider.provider_id, [])


def test_api_list_devices():
    res = client.get("/api/devices")
    assert res.status_code == 200
    devices = res.json()
    assert isinstance(devices, list)
    ids = [d["id"] for d in devices]
    assert "android:phase8-dev-01" in ids
    assert "android:phase8-unauth-02" in ids


def test_api_list_devices_filtering_by_state():
    res = client.get("/api/devices?state=unauthorized")
    assert res.status_code == 200
    devices = res.json()
    assert len(devices) >= 1
    for d in devices:
        assert d["state"] == "unauthorized"


def test_api_list_devices_filtering_by_search():
    res = client.get("/api/devices?search=Pixel")
    assert res.status_code == 200
    devices = res.json()
    assert any("Pixel" in d["model"] or "Pixel" in d["display_name"] for d in devices)


def test_api_get_device_by_composite_id_and_raw_serial():
    # Composite ID lookup
    res1 = client.get("/api/devices/android:phase8-dev-01")
    assert res1.status_code == 200
    assert res1.json()["id"] == "android:phase8-dev-01"

    # Raw serial lookup
    res2 = client.get("/api/devices/phase8-dev-01")
    assert res2.status_code == 200
    assert res2.json()["serial"] == "phase8-dev-01"


def test_api_connect_and_disconnect_lifecycle():
    # Connect
    res = client.post("/api/devices/android:phase8-dev-01/connect")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "connected"
    assert data["state"] == "connected"

    # Verify device state in registry
    dev_res = client.get("/api/devices/android:phase8-dev-01")
    assert dev_res.json()["state"] == "connected"

    # Disconnect
    disc_res = client.post("/api/devices/android:phase8-dev-01/disconnect")
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert disc_data["status"] == "disconnected"
    assert disc_data["state"] == "available"


def test_api_connect_unauthorized_device_fails_with_403():
    res = client.post("/api/devices/android:phase8-unauth-02/connect")
    assert res.status_code == 403
    assert "unauthorized" in res.json()["detail"]


def test_api_providers_health():
    res = client.get("/api/providers/health")
    assert res.status_code == 200
    providers = res.json()
    assert isinstance(providers, list)
    assert any(p["provider_id"] == "test_mock_provider" for p in providers)


def test_api_registry_stats():
    res = client.get("/api/registry/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total" in stats
    assert "online" in stats
    assert "unauthorized" in stats
    assert stats["total"] >= 2
    assert stats["unauthorized"] >= 1
