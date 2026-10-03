"""
Integration tests for FastAPI endpoints in KELVRA Device Lab.
"""

import pytest
from fastapi.testclient import TestClient
from src.device_manager import DeviceInfo, DeviceStatus
from src.server import app, device_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mock_device():
    mock_dev = DeviceInfo(
        serial="mock-server-dev",
        model="Test Device",
        status=DeviceStatus.ONLINE,
        battery_level=92,
        battery_temperature=27.4,
        screen_width=1080,
        screen_height=2400
    )
    device_manager.add_mock_device(mock_dev)
    yield
    device_manager.remove_mock_device("mock-server-dev")


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "kelvra-device-lab"


def test_list_devices_endpoint():
    res = client.get("/api/devices")
    assert res.status_code == 200
    devices = res.json()
    assert isinstance(devices, list)
    serials = [d["serial"] for d in devices]
    assert "mock-server-dev" in serials


def test_get_device_detail():
    res = client.get("/api/devices/mock-server-dev")
    assert res.status_code == 200
    dev = res.json()
    assert dev["serial"] == "mock-server-dev"
    assert dev["battery_level"] == 92


def test_device_telemetry_endpoint():
    res = client.get("/api/devices/mock-server-dev/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert data["serial"] == "mock-server-dev"
    assert "cpu_usage_percent" in data
    assert "ram_used_mb" in data


def test_device_screenshot_endpoint():
    res = client.get("/api/devices/mock-server-dev/screenshot")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert len(res.content) > 100


def test_input_tap_endpoint():
    res = client.post("/api/devices/mock-server-dev/input/tap", json={"x": 500, "y": 800})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_input_key_endpoint():
    res = client.post("/api/devices/mock-server-dev/input/key", json={"key": "BACK"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_input_text_endpoint():
    res = client.post("/api/devices/mock-server-dev/input/text", json={"text": "Test"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_smoke_test_endpoint():
    res = client.post(
        "/api/devices/mock-server-dev/tests/smoke",
        json={"package": "com.kelvra.mobile"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "PASSED"
    assert len(data["steps"]) == 3
