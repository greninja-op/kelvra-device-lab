"""
Test Suite for Phase 27: Multi-Device Matrix Grid Streaming View & Thumbnail Preview Engine.
Validates single-device thumbnail retrieval, batch thumbnail generation, unauthorized handling,
matrix grid layout elements, and zero-emoji compliance.
"""

import io
import re
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.server import app, device_manager, device_registry
from src.device_manager import DeviceInfo, DeviceStatus
from src.domain_model import (
    Device,
    DevicePlatform,
    DeviceType,
    DeviceLifecycleState,
    DeviceCapability,
)


@pytest.fixture
def matrix_test_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_matrix_devices():
    """Setup a set of mock devices for multi-device matrix testing."""
    dev1 = DeviceInfo(
        serial="mock-matrix-pixel7",
        model="Pixel 7",
        status=DeviceStatus.ONLINE,
        battery_level=88,
        battery_temperature=28.0,
        screen_width=1080,
        screen_height=2400
    )
    dev2 = DeviceInfo(
        serial="mock-matrix-galaxy-s23",
        model="Galaxy S23",
        status=DeviceStatus.ONLINE,
        battery_level=94,
        battery_temperature=26.5,
        screen_width=1080,
        screen_height=2340
    )
    dev3 = DeviceInfo(
        serial="mock-matrix-unauthorized",
        model="Unauthorized Device",
        status=DeviceStatus.UNAUTHORIZED,
        battery_level=50,
        battery_temperature=25.0,
        screen_width=720,
        screen_height=1280
    )

    device_manager.add_mock_device(dev1)
    device_manager.add_mock_device(dev2)
    device_manager.add_mock_device(dev3)

    # Also register in domain model registry
    d1 = Device(
        id="android:mock-matrix-pixel7",
        serial="mock-matrix-pixel7",
        provider_id="mock-provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Pixel 7",
        model="Pixel 7",
        state=DeviceLifecycleState.AVAILABLE
    )
    d2 = Device(
        id="android:mock-matrix-galaxy-s23",
        serial="mock-matrix-galaxy-s23",
        provider_id="mock-provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Galaxy S23",
        model="Galaxy S23",
        state=DeviceLifecycleState.AVAILABLE
    )
    d3 = Device(
        id="android:mock-matrix-unauthorized",
        serial="mock-matrix-unauthorized",
        provider_id="mock-provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name="Unauthorized Device",
        model="Unauthorized Device",
        state=DeviceLifecycleState.UNAUTHORIZED
    )

    device_registry.register_device(d1)
    device_registry.register_device(d2)
    device_registry.register_device(d3)

    yield

    # Teardown
    device_manager._mock_devices.pop("mock-matrix-pixel7", None)
    device_manager._mock_devices.pop("mock-matrix-galaxy-s23", None)
    device_manager._mock_devices.pop("mock-matrix-unauthorized", None)
    device_registry._devices.pop("android:mock-matrix-pixel7", None)
    device_registry._devices.pop("android:mock-matrix-galaxy-s23", None)
    device_registry._devices.pop("android:mock-matrix-unauthorized", None)


def test_device_thumbnail_success(matrix_test_client):
    """Verify single device thumbnail endpoint returns JPEG binary payload."""
    res = matrix_test_client.get("/api/devices/mock-matrix-pixel7/thumbnail?max_width=320&quality=65")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert "public, max-age=1" in res.headers.get("cache-control", "")

    # Validate image data is valid JPEG and resized
    img = Image.open(io.BytesIO(res.content))
    assert img.format == "JPEG"
    assert img.width <= 720


def test_device_thumbnail_composite_id(matrix_test_client):
    """Verify thumbnail endpoint accepts composite id 'android:mock-matrix-pixel7'."""
    res = matrix_test_client.get("/api/devices/android:mock-matrix-pixel7/thumbnail")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"


def test_device_thumbnail_not_found(matrix_test_client):
    """Verify thumbnail returns 404 for unknown device."""
    res = matrix_test_client.get("/api/devices/non-existent-serial/thumbnail")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_device_thumbnail_unauthorized_rejected(matrix_test_client):
    """Verify thumbnail returns 403 for unauthorized device."""
    res = matrix_test_client.get("/api/devices/mock-matrix-unauthorized/thumbnail")
    assert res.status_code == 403
    assert "unauthorized" in res.json()["detail"].lower()


def test_batch_thumbnails_endpoint(matrix_test_client):
    """Verify batch thumbnails returns structured JSON with base64 images."""
    res = matrix_test_client.get("/api/devices/thumbnails/batch?max_width=320&quality=65")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "thumbnails" in data
    assert data["count"] >= 2

    # Check online device payload
    pixel = data["thumbnails"].get("mock-matrix-pixel7")
    assert pixel is not None
    assert pixel["status"] == "online"
    assert pixel["display_name"] == "Pixel 7"
    assert pixel["thumbnail"].startswith("data:image/jpeg;base64,")

    # Check unauthorized device payload
    unauth = data["thumbnails"].get("mock-matrix-unauthorized")
    assert unauth is not None
    assert unauth["status"] == "unauthorized"
    assert unauth["thumbnail"] is None


def test_html_contains_matrix_grid_elements(matrix_test_client):
    """Verify static index.html contains studio-layout-select and studio-matrix-viewport."""
    res = matrix_test_client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'id="studio-layout-select"' in html
    assert 'id="studio-matrix-viewport"' in html
    assert 'class="studio-matrix-viewport"' in html


def test_thumbnail_and_screenshot_bounds_clamping(matrix_test_client):
    """Verify that extreme quality and max_width values are safely clamped without errors."""
    res_thumb = matrix_test_client.get("/api/devices/mock-matrix-pixel7/thumbnail?max_width=-100&quality=999")
    assert res_thumb.status_code == 200
    assert res_thumb.headers["content-type"] == "image/jpeg"

    res_batch = matrix_test_client.get("/api/devices/thumbnails/batch?max_width=99999&quality=-50")
    assert res_batch.status_code == 200
    assert "thumbnails" in res_batch.json()

    res_screen = matrix_test_client.get("/api/devices/mock-matrix-pixel7/screenshot?max_width=0&quality=0")
    assert res_screen.status_code == 200
    assert res_screen.headers["content-type"] == "image/jpeg"


def test_zero_unicode_emojis_in_phase27():
    """Verify strict zero-emoji compliance in Phase 27 files."""
    pattern = re.compile(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]')
    files = [
        "src/server.py",
        "static/app.js",
        "static/index.html",
        "static/style.css",
        "tests/test_phase27_matrix_grid_thumbnails.py"
    ]
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            matches = pattern.findall(content)
            assert len(matches) == 0, f"Found emojis in {filepath}: {matches}"
