"""
Unit and integration tests for KELVRA Device Lab standalone application shell and navigation.
Validates Phase 7 foundational shell, design token integration, and SPA page routing.
Zero Unicode Emoji Prohibition strictly enforced.
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)

EMOJI_REGEX = re.compile(r'[\U0001F300-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]')


def test_root_serves_index_html():
    """Verify root / serves the application shell index.html with HTTP 200."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "KELVRA Device Lab" in res.text
    assert 'class="app-shell"' in res.text
    assert 'id="app-sidebar"' in res.text
    assert 'class="page-container"' in res.text


@pytest.mark.parametrize("route", [
    "/overview",
    "/devices",
    "/virtual",
    "/sessions",
    "/automation",
    "/diagnostics",
    "/settings"
])
def test_spa_direct_routes(route):
    """Verify that all approved SPA page routes resolve to index.html with HTTP 200."""
    res = client.get(route)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert 'class="app-shell"' in res.text


def test_static_stylesheet_served():
    """Verify style.css is served with correct mime-type and contains verified tokens."""
    res = client.get("/style.css")
    assert res.status_code == 200
    assert "text/css" in res.headers["content-type"]
    css_content = res.text

    # Verified KELVRA Bench design tokens
    assert "--bg-canvas: #262624" in css_content
    assert "--bg-sidebar: #1E1E1C" in css_content
    assert "--bg-panel: #1A1918" in css_content
    assert "--bg-elevated: #2E2D2A" in css_content
    assert "--accent-coral: #D97757" in css_content
    assert "'Lora'" in css_content
    assert "'Inter'" in css_content
    assert "'JetBrains Mono'" in css_content
    assert "--dot-idle: #8A867E" in css_content
    assert "--dot-complete: #10B981" in css_content
    assert "--dot-error: #EF4444" in css_content


def test_static_javascript_served():
    """Verify app.js is served with correct mime-type and contains shell router."""
    res = client.get("/app.js")
    assert res.status_code == 200
    js_content = res.text
    assert "DeviceLabApp" in js_content
    assert "initRouting" in js_content
    assert "navigateTo" in js_content
    assert "showToast" in js_content


def test_shell_html_contains_all_seven_page_views():
    """Verify index.html contains all 7 approved page shell sections."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'id="view-overview"' in html
    assert 'id="view-devices"' in html
    assert 'id="view-virtual"' in html
    assert 'id="view-sessions"' in html
    assert 'id="view-automation"' in html
    assert 'id="view-diagnostics"' in html
    assert 'id="view-settings"' in html


def test_shell_html_contains_required_shell_components():
    """Verify index.html contains essential shell components (Header, Sidebar, Toast, Modal)."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'class="app-header"' in html
    assert 'id="btn-toggle-sidebar"' in html
    assert 'id="toast-container"' in html
    assert 'id="modal-backdrop"' in html
    assert 'id="service-status-dot"' in html


def test_zero_unicode_emojis_in_shell_and_assets():
    """Verify zero raw Unicode emojis exist across static HTML, CSS, and JS."""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    for fname in ["index.html", "style.css", "app.js"]:
        fpath = os.path.join(static_dir, fname)
        assert os.path.exists(fpath), f"File {fname} must exist in static/"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            matches = EMOJI_REGEX.findall(content)
            assert len(matches) == 0, f"Found {len(matches)} emoji violations in {fname}: {set(matches)}"
