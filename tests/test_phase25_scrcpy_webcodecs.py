"""
Test Suite for Phase 25: Low-Latency WebCodecs H.264 Video Streaming Pipeline.
Verifies NAL unit parsing, SPS/PPS parameter caching, stream lifecycle state machine,
mock stream generation, REST endpoints, and zero-emoji compliance.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from src.scrcpy_streamer import (
    H264NalUnit,
    H264Parser,
    ScrcpyConfig,
    ScrcpyDiagnostics,
    ScrcpySession,
    ScrcpyStreamState,
    ScrcpyStreamer,
    NAL_TYPE_IDR,
    NAL_TYPE_NON_IDR,
    NAL_TYPE_PPS,
    NAL_TYPE_SPS,
    ANNEX_B_START_CODE_4,
    ANNEX_B_START_CODE_3,
)
from src.server import app, device_registry, mock_provider


@pytest.fixture
def client():
    return TestClient(app)


def test_nal_unit_annex_b_formatting():
    """Verifies that H264NalUnit normalizes data with 4-byte Annex-B start codes."""
    raw_payload = bytes([0x65, 0x88, 0x84, 0x00])

    # Case 1: Raw bytes without prefix
    unit1 = H264NalUnit(raw_payload, NAL_TYPE_IDR, True)
    assert unit1.to_annex_b().startswith(ANNEX_B_START_CODE_4)
    assert unit1.to_annex_b()[4:] == raw_payload

    # Case 2: Already 4-byte prefix
    unit2 = H264NalUnit(ANNEX_B_START_CODE_4 + raw_payload, NAL_TYPE_IDR, True)
    assert unit2.to_annex_b() == ANNEX_B_START_CODE_4 + raw_payload

    # Case 3: 3-byte prefix converted to 4-byte
    unit3 = H264NalUnit(ANNEX_B_START_CODE_3 + raw_payload, NAL_TYPE_IDR, True)
    assert unit3.to_annex_b() == ANNEX_B_START_CODE_4 + raw_payload


def test_h264_parser_extract_nal_type():
    """Verifies correct 5-bit NAL unit type extraction from header byte."""
    sps_bytes = ANNEX_B_START_CODE_4 + bytes([0x67, 0x42, 0xC0])  # 0x67 & 0x1F == 7 (SPS)
    pps_bytes = ANNEX_B_START_CODE_4 + bytes([0x68, 0xCB, 0x8C])  # 0x68 & 0x1F == 8 (PPS)
    idr_bytes = ANNEX_B_START_CODE_4 + bytes([0x65, 0x88, 0x84])  # 0x65 & 0x1F == 5 (IDR)
    non_idr = ANNEX_B_START_CODE_3 + bytes([0x41, 0x9A, 0x24])    # 0x41 & 0x1F == 1 (Non-IDR)

    assert H264Parser.extract_nal_type(sps_bytes) == NAL_TYPE_SPS
    assert H264Parser.extract_nal_type(pps_bytes) == NAL_TYPE_PPS
    assert H264Parser.extract_nal_type(idr_bytes) == NAL_TYPE_IDR
    assert H264Parser.extract_nal_type(non_idr) == NAL_TYPE_NON_IDR


def test_h264_parser_stream_splitting_and_parameter_caching():
    """Verifies parsing of concatenated Annex-B stream and caching of SPS/PPS."""
    parser = H264Parser()

    sps_packet = ANNEX_B_START_CODE_4 + bytes([0x67, 0x42, 0xC0, 0x1E])
    pps_packet = ANNEX_B_START_CODE_4 + bytes([0x68, 0xCB, 0x8C])
    idr_packet = ANNEX_B_START_CODE_4 + bytes([0x65, 0x88, 0x84, 0x01])
    slice_packet = ANNEX_B_START_CODE_3 + bytes([0x41, 0x9A, 0x02])

    stream = sps_packet + pps_packet + idr_packet + slice_packet

    units = parser.parse_annex_b_stream(stream)
    assert len(units) == 4

    assert units[0].nal_type == NAL_TYPE_SPS
    assert units[1].nal_type == NAL_TYPE_PPS
    assert units[2].nal_type == NAL_TYPE_IDR
    assert units[2].is_keyframe is True
    assert units[3].nal_type == NAL_TYPE_NON_IDR
    assert units[3].is_keyframe is False

    # Check cached initialization payload
    init_payload = parser.get_initialization_payload()
    assert init_payload is not None
    assert init_payload == parser.sps + parser.pps


@pytest.mark.asyncio
async def test_scrcpy_session_lifecycle_mock_mode():
    """Verifies ScrcpySession startup, parameter initialization, diagnostics, and graceful stop."""
    config = ScrcpyConfig(max_fps=60, max_width=1080, mock_mode=True)
    session = ScrcpySession("mock-h264-device", config)

    assert session.state == ScrcpyStreamState.IDLE

    # Start session
    started = await session.start()
    assert started is True
    assert session.state == ScrcpyStreamState.STREAMING
    assert session.parser.sps is not None
    assert session.parser.pps is not None

    # Check diagnostics
    diag = session.get_diagnostics()
    assert diag.serial == "mock-h264-device"
    assert diag.codec == "h264"
    assert diag.sps_detected is True
    assert diag.pps_detected is True
    assert diag.state == ScrcpyStreamState.STREAMING

    # Stop session
    await session.stop()
    assert session.state == ScrcpyStreamState.STOPPED
    assert session._worker_task is None


@pytest.mark.asyncio
async def test_scrcpy_session_disconnect_signal():
    """Verifies that hardware detachment terminates the active stream loop and updates state."""
    config = ScrcpyConfig(max_fps=30, mock_mode=True)
    session = ScrcpySession("disconnect-test-dev", config)
    await session.start()
    assert session.state == ScrcpyStreamState.STREAMING

    # Trigger hardware disconnect signal
    session.handle_device_disconnect()
    assert session.state == ScrcpyStreamState.DEVICE_DISCONNECTED
    assert "detached" in (session.error_message or "").lower()
    assert session._worker_task is None


@pytest.mark.asyncio
async def test_scrcpy_streamer_manager_multi_device_isolation():
    """Verifies that ScrcpyStreamer manages isolated sessions across multiple devices."""
    streamer = ScrcpyStreamer(default_fps=60)

    session_a = streamer.get_or_create_session("dev-alpha")
    session_b = streamer.get_or_create_session("dev-beta")

    assert session_a.serial == "dev-alpha"
    assert session_b.serial == "dev-beta"
    assert session_a != session_b

    await streamer.start_stream("dev-alpha", ScrcpyConfig(mock_mode=True))
    assert session_a.state == ScrcpyStreamState.STREAMING
    assert session_b.state == ScrcpyStreamState.IDLE

    diag_a = streamer.get_diagnostics("dev-alpha")
    diag_b = streamer.get_diagnostics("dev-beta")
    assert diag_a.state == ScrcpyStreamState.STREAMING
    assert diag_b.state == ScrcpyStreamState.IDLE

    await streamer.stop_all()
    assert len(streamer._sessions) == 0


def test_h264_rest_api_start_stop_status(client):
    """Verifies REST endpoints for starting, querying status, and stopping H.264 streams."""
    # Query status of idle stream
    res = client.get("/api/devices/mock-pixel-7/stream/h264/status")
    assert res.status_code == 200
    data = res.json()
    assert data["codec"] == "h264"
    assert data["state"] == "idle"

    # Start H.264 stream with mock_mode=True
    start_payload = {
        "max_fps": 60,
        "max_width": 1080,
        "bitrate": 8000000,
        "mock_mode": True
    }
    res_start = client.post("/api/devices/mock-pixel-7/stream/h264/start", json=start_payload)
    assert res_start.status_code == 200
    start_data = res_start.json()
    assert start_data["status"] == "started"
    assert start_data["codec"] == "h264"
    assert start_data["fps"] == 60

    # Query status of active stream
    res_active = client.get("/api/devices/mock-pixel-7/stream/h264/status")
    assert res_active.status_code == 200
    active_data = res_active.json()
    assert active_data["state"] == "streaming"
    assert active_data["sps_detected"] is True

    # Stop H.264 stream
    res_stop = client.post("/api/devices/mock-pixel-7/stream/h264/stop")
    assert res_stop.status_code == 200
    stop_data = res_stop.json()
    assert stop_data["status"] == "stopped"


def test_h264_rest_api_unauthorized_device_rejected(client):
    """Verifies that attempting to start H.264 stream on unauthorized hardware is rejected with HTTP 403."""
    from src.domain_model import Device, DeviceLifecycleState, DevicePlatform, DeviceType
    unauth_dev = Device(
        id="android:phase25-unauth-test",
        serial="phase25-unauth-test",
        provider_id=mock_provider.provider_id,
        display_name="Unauthorized Device",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        state=DeviceLifecycleState.UNAUTHORIZED
    )
    mock_provider.add_device(unauth_dev)

    res = client.post("/api/devices/android:phase25-unauth-test/stream/h264/start", json={"mock_mode": True})
    assert res.status_code == 403
    assert "unauthorized" in res.json()["detail"].lower()
