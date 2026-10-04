"""
FastAPI Server & Control Room for KELVRA Device Lab.
Provides REST and WebSocket endpoints for device teleoperation, streaming, and testing.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.bench_bridge import BenchBridge
from src.device_manager import DeviceInfo, DeviceManager, DeviceStatus
from src.device_telemetry import DeviceTelemetry, TelemetryCollector
from src.input_controller import InputController
from src.logcat_service import LogcatService
from src.screen_streamer import ScreenStreamer
from src.test_runner import TestRunReport, TestRunner
from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.provider_base import ProviderHealth
from src.device_registry import DeviceRegistry
from src.android_provider import AndroidDeviceProvider
from src.mock_provider import MockDeviceProvider
from src.session_manager import SessionManager, DeviceLease, LeaseConflictError
from src.screen_streamer import StreamConfig, StreamDiagnostics, StreamState
from src.avd_manager import (
    AvdConfig,
    AvdManager,
    AvdStatus,
    CreateAvdRequest,
    EmulatorLaunchOptions,
    SdkEnvironmentDetector,
    SdkEnvironmentStatus,
)
from src.apple_provider import (
    AppleCapabilityItem,
    AppleDeviceProvider,
    AppleEnvironmentDetector,
    AppleEnvironmentStatus,
    ApplePairingState,
)
from src.artifact_manager import ArtifactManager, ArtifactType, ArtifactRecord, StorageSummary
from src.recording_manager import RecordingManager, RecordingState, RecordingSession
from src.diagnostics_service import DiagnosticsService, DeviceDiagnosticReport
from src.automation_engine import (
    AutomationEngine,
    ActionType,
    ExecutionStatus,
    WorkflowStep,
    WorkflowDefinition,
    StepExecutionResult,
    WorkflowExecutionReport,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kelvra.device_lab.server")

# Subsystem initializations
device_manager = DeviceManager()
input_controller = InputController(device_manager)
telemetry_collector = TelemetryCollector(device_manager)
screen_streamer = ScreenStreamer(input_controller)
logcat_service = LogcatService(device_manager)
bench_bridge = BenchBridge(device_manager)
test_runner = TestRunner(device_manager, input_controller)

# Phase 8 & 9 Device Registry & Provider Layer
device_registry = DeviceRegistry()
android_provider = AndroidDeviceProvider()
android_provider.initialize()
device_registry.register_provider(android_provider)
mock_provider = MockDeviceProvider("test_mock_provider")
device_registry.register_provider(mock_provider)

# Phase 12 Physical Apple Provider Layer
apple_detector = AppleEnvironmentDetector()
apple_provider = AppleDeviceProvider(detector=apple_detector)
apple_provider.initialize()
device_registry.register_provider(apple_provider)

# Phase 10 Session & Lease Manager
session_manager = SessionManager()
session_manager.set_registry(device_registry)
input_controller.set_session_manager(session_manager)
input_controller.set_device_registry(device_registry)

# Phase 11 AVD & Emulator Manager
sdk_detector = SdkEnvironmentDetector()
avd_manager = AvdManager(sdk_detector=sdk_detector, device_registry=device_registry)

# Phase 13 Artifacts, Recording, Diagnostics, and Automation
artifact_manager = ArtifactManager()
recording_manager = RecordingManager(device_manager, artifact_manager, device_registry)
diagnostics_service = DiagnosticsService(
    device_registry=device_registry,
    screen_streamer=screen_streamer,
    session_manager=session_manager,
    avd_manager=avd_manager,
    device_manager=device_manager
)
automation_engine = AutomationEngine(
    device_registry=device_registry,
    input_controller=input_controller,
    artifact_manager=artifact_manager,
    session_manager=session_manager
)


class ConfigureAdbRequest(BaseModel):
    adb_path: str


_synced_manager_serials: Set[str] = set()


def _sync_mock_devices():
    """Bridges legacy device_manager mock devices into mock_provider for unified testing."""
    global _synced_manager_serials
    current_serials = set(device_manager._mock_devices.keys())

    # Remove any previously synced devices that are no longer in device_manager
    for s in list(_synced_manager_serials):
        if s not in current_serials:
            mock_provider.remove_device(f"android:{s}")
            _synced_manager_serials.remove(s)

    for s, mdev in device_manager._mock_devices.items():
        dev_id = f"android:{s}"
        state_val = DeviceLifecycleState.AVAILABLE if mdev.status.value == "online" else (
            DeviceLifecycleState.UNAUTHORIZED if mdev.status.value == "unauthorized" else DeviceLifecycleState.UNAVAILABLE
        )
        mock_device = Device(
            id=dev_id,
            serial=s,
            provider_id=mock_provider.provider_id,
            platform=DevicePlatform.ANDROID_VIRTUAL if mdev.is_emulator else DevicePlatform.ANDROID_PHYSICAL,
            device_type=DeviceType.VIRTUAL if mdev.is_emulator else DeviceType.PHYSICAL,
            display_name=mdev.market_name if mdev.market_name != "Android Device" else mdev.model,
            manufacturer=mdev.manufacturer,
            model=mdev.model,
            os_name="Android",
            os_version=mdev.android_version,
            sdk_level=mdev.sdk_level,
            abi=mdev.abi,
            state=state_val,
            capabilities=[
                DeviceCapability.DISCOVERY,
                DeviceCapability.SCREEN_STREAM_JPEG,
                DeviceCapability.SCREENSHOT_CAPTURE,
                DeviceCapability.TELEMETRY_POLLING,
                DeviceCapability.LOGCAT_STREAMING
            ]
        )
        mock_provider.add_device(mock_device)
        _synced_manager_serials.add(s)

    device_registry.reconcile()


# Request Models
class TapRequest(BaseModel):
    x: int
    y: int
    session_token: Optional[str] = None


class SwipeRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    duration_ms: int = 300
    session_token: Optional[str] = None


class KeyRequest(BaseModel):
    key: str
    session_token: Optional[str] = None


class TextRequest(BaseModel):
    text: str
    session_token: Optional[str] = None


class LeaseRequest(BaseModel):
    client_id: str
    duration_seconds: Optional[float] = 300.0
    purpose: str = "Manual Teleoperation"


class LeaseRenewRequest(BaseModel):
    session_token: str
    extension_seconds: Optional[float] = 300.0


class StreamConfigRequest(BaseModel):
    max_width: int = Field(default=720, ge=320, le=1920)
    quality: int = Field(default=75, ge=30, le=95)
    max_fps: int = Field(default=30, ge=5, le=60)


class AppLaunchRequest(BaseModel):
    package: str
    activity: Optional[str] = None
    session_token: Optional[str] = None


class AppStopRequest(BaseModel):
    package: str
    session_token: Optional[str] = None


class SmokeTestRequest(BaseModel):
    package: str
    activity: Optional[str] = None


class CaptureScreenshotRequest(BaseModel):
    name: Optional[str] = None
    max_width: int = Field(default=1080, ge=320, le=3840)
    quality: int = Field(default=80, ge=30, le=100)
    session_token: Optional[str] = None


class StartRecordingRequest(BaseModel):
    max_duration_seconds: int = Field(default=180, ge=5, le=600)
    bit_rate_bps: int = Field(default=4000000, ge=500000, le=20000000)


class CreateWorkflowRequest(BaseModel):
    name: str
    target_device: str
    steps: List[WorkflowStep]
    description: Optional[str] = ""
    timeout_seconds: float = Field(default=120.0, ge=5.0, le=600.0)


class ExecuteInlineWorkflowRequest(BaseModel):
    workflow: CreateWorkflowRequest
    session_token: Optional[str] = None


# Background fleet polling task
async def _background_fleet_monitor():
    """Periodically scan for attached devices and update pairing state."""
    while True:
        try:
            devices = device_manager.scan_devices()
            for dev in devices:
                dev.paired = bench_bridge.check_pairing(dev.serial)
            await asyncio.sleep(5.0)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.debug(f"Fleet monitor cycle error: {exc}")
            await asyncio.sleep(5.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run initial device scan
    logger.info("Starting KELVRA Device Lab Server on port 8098...")
    device_manager.scan_devices()
    monitor_task = asyncio.create_task(_background_fleet_monitor())
    yield
    # Shutdown
    monitor_task.cancel()
    await screen_streamer.stop_all()
    await avd_manager.shutdown_all()
    apple_provider.cleanup()
    for s in list(recording_manager._active_sessions.values()):
        if s.state == RecordingState.RECORDING:
            try:
                await recording_manager.stop_recording(s.serial)
            except Exception:
                pass
    logger.info("KELVRA Device Lab Server stopped.")


app = FastAPI(
    title="KELVRA Device Lab",
    description="Autonomous Device Testing, Teleoperation, and Fleet Orchestration Console",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DeviceResponse(BaseModel):
    id: str
    serial: str
    provider_id: str
    platform: DevicePlatform
    device_type: DeviceType
    display_name: str
    manufacturer: Optional[str] = "Unknown"
    model: Optional[str] = "Unknown"
    market_name: Optional[str] = "Android Device"
    os_name: str = "Android"
    os_version: Optional[str] = None
    android_version: Optional[str] = None
    sdk_level: Optional[int] = 0
    abi: Optional[str] = "arm64-v8a"
    transport: ConnectionTransport = ConnectionTransport.USB
    state: DeviceLifecycleState = DeviceLifecycleState.DISCOVERED
    status: DeviceStatus = DeviceStatus.ONLINE
    capabilities: List[DeviceCapability] = Field(default_factory=list)
    battery_level: int = 100
    battery_charging: bool = False
    battery_temperature: float = 25.0
    screen_width: int = 1080
    screen_height: int = 2400
    screen_density: int = 440
    airplane_mode: bool = False
    wifi_ip: Optional[str] = None
    is_emulator: bool = False
    paired: bool = False
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    connected_at: Optional[str] = None
    error: Optional[DeviceError] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _resolve_serial(serial_or_id: str) -> str:
    if ":" in serial_or_id:
        return serial_or_id.split(":", 1)[1]
    return serial_or_id


def _build_device_response(d: Device) -> DeviceResponse:
    mgr_dev = device_manager.get_device(d.serial)
    paired = bench_bridge.check_pairing(d.serial)
    
    if d.state in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.CONNECTED, DeviceLifecycleState.BUSY):
        status_val = DeviceStatus.ONLINE
    elif d.state == DeviceLifecycleState.UNAUTHORIZED:
        status_val = DeviceStatus.UNAUTHORIZED
    else:
        status_val = DeviceStatus.OFFLINE

    return DeviceResponse(
        id=d.id,
        serial=d.serial,
        provider_id=d.provider_id,
        platform=d.platform,
        device_type=d.device_type,
        display_name=d.display_name,
        manufacturer=d.manufacturer or (mgr_dev.manufacturer if mgr_dev else "Unknown"),
        model=d.model or (mgr_dev.model if mgr_dev else "Unknown"),
        market_name=mgr_dev.market_name if mgr_dev else d.display_name,
        os_name=d.os_name,
        os_version=d.os_version or (mgr_dev.android_version if mgr_dev else "Unknown"),
        android_version=d.os_version or (mgr_dev.android_version if mgr_dev else "Unknown"),
        sdk_level=d.sdk_level or (mgr_dev.sdk_level if mgr_dev else 0),
        abi=d.abi or (mgr_dev.abi if mgr_dev else "arm64-v8a"),
        transport=d.transport,
        state=d.state,
        status=status_val,
        capabilities=d.capabilities,
        battery_level=mgr_dev.battery_level if mgr_dev else 100,
        battery_charging=mgr_dev.battery_charging if mgr_dev else False,
        battery_temperature=mgr_dev.battery_temperature if mgr_dev else 25.0,
        screen_width=mgr_dev.screen_width if mgr_dev else 1080,
        screen_height=mgr_dev.screen_height if mgr_dev else 2400,
        screen_density=mgr_dev.screen_density if mgr_dev else 440,
        airplane_mode=mgr_dev.airplane_mode if mgr_dev else False,
        wifi_ip=mgr_dev.wifi_ip if mgr_dev else None,
        is_emulator=d.device_type == DeviceType.VIRTUAL,
        paired=paired,
        last_seen=d.last_seen,
        connected_at=d.connected_at,
        error=d.error,
        metadata=d.metadata
    )


# --- REST ENDPOINTS ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "kelvra-device-lab",
        "port": int(os.environ.get("KELVRA_DEVICE_LAB_PORT", 8098)),
        "active_devices": len(device_manager._cached_devices)
    }


@app.get("/api/providers/health", response_model=List[ProviderHealth])
async def get_providers_health():
    return device_registry.get_providers_health()


@app.get("/api/providers/android/health", response_model=ProviderHealth)
async def get_android_provider_health():
    return android_provider.get_health()


@app.post("/api/providers/android/configure")
async def configure_android_adb(req: ConfigureAdbRequest):
    ok, msg = android_provider.configure_adb_path(req.adb_path)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    device_registry.poll_all_providers()
    return {"status": "ok", "message": msg, "health": android_provider.get_health()}


@app.get("/api/registry/stats")
async def get_registry_stats():
    return device_registry.get_stats()


@app.get("/api/devices/{serial_or_id}/properties")
async def get_device_properties_endpoint(serial_or_id: str):
    raw_serial = _resolve_serial(serial_or_id)
    dev = device_registry.get_device(serial_or_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found")
    if dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Device is unauthorized. Cannot query properties.")

    props = android_provider.get_device_properties(raw_serial)
    if not props:
        return {
            "manufacturer": dev.manufacturer,
            "model": dev.model,
            "os_version": dev.os_version,
            "sdk_level": dev.sdk_level,
            "abi": dev.abi
        }
    return props


@app.get("/api/devices/{serial_or_id}/display")
async def get_device_display_endpoint(serial_or_id: str):
    raw_serial = _resolve_serial(serial_or_id)
    dev = device_registry.get_device(serial_or_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found")
    if dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Device is unauthorized. Cannot query display geometry.")

    return android_provider.get_display_info(raw_serial)


@app.get("/api/devices/{serial_or_id}/health")
async def get_device_health_endpoint(serial_or_id: str):
    raw_serial = _resolve_serial(serial_or_id)
    dev = device_registry.get_device(serial_or_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found")
    if dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail="Device is unauthorized. Cannot query health probe.")

    return android_provider.check_device_health(raw_serial)


@app.post("/api/devices/{serial_or_id}/refresh", response_model=DeviceResponse)
async def refresh_device_endpoint(serial_or_id: str):
    raw_serial = _resolve_serial(serial_or_id)
    android_provider.invalidate_cache(raw_serial)
    device_registry.poll_all_providers()
    updated = device_registry.get_device(serial_or_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' no longer present")
    return _build_device_response(updated)


@app.get("/api/devices", response_model=List[DeviceResponse])
async def list_devices(
    platform: Optional[DevicePlatform] = None,
    state: Optional[DeviceLifecycleState] = None,
    search: Optional[str] = None
):
    _sync_mock_devices()
    device_registry.poll_all_providers()
    devices = device_registry.list_devices(platform=platform, state=state)
    
    if search:
        search_lower = search.lower()
        devices = [
            d for d in devices
            if search_lower in d.serial.lower()
            or search_lower in (d.model or "").lower()
            or search_lower in (d.manufacturer or "").lower()
            or search_lower in (d.display_name or "").lower()
        ]

    return [_build_device_response(d) for d in devices]


@app.get("/api/devices/{serial_or_id}", response_model=DeviceResponse)
async def get_device(serial_or_id: str):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    if dev:
        return _build_device_response(dev)

    # Fallback to device_manager
    raw_serial = _resolve_serial(serial_or_id)
    mgr_dev = device_manager.get_device(raw_serial)
    if not mgr_dev:
        raise HTTPException(status_code=404, detail=f"Device {serial_or_id} not found")

    paired = bench_bridge.check_pairing(raw_serial)
    return DeviceResponse(
        id=f"android:{mgr_dev.serial}",
        serial=mgr_dev.serial,
        provider_id="android_adb",
        platform=DevicePlatform.ANDROID_VIRTUAL if mgr_dev.is_emulator else DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.VIRTUAL if mgr_dev.is_emulator else DeviceType.PHYSICAL,
        display_name=mgr_dev.model,
        manufacturer=mgr_dev.manufacturer,
        model=mgr_dev.model,
        market_name=mgr_dev.market_name,
        os_name="Android",
        os_version=mgr_dev.android_version,
        android_version=mgr_dev.android_version,
        sdk_level=mgr_dev.sdk_level,
        abi=mgr_dev.abi,
        transport=ConnectionTransport.EMULATOR_PIPE if mgr_dev.is_emulator else ConnectionTransport.USB,
        state=DeviceLifecycleState.AVAILABLE if mgr_dev.status == DeviceStatus.ONLINE else (
            DeviceLifecycleState.UNAUTHORIZED if mgr_dev.status == DeviceStatus.UNAUTHORIZED else DeviceLifecycleState.UNAVAILABLE
        ),
        status=mgr_dev.status,
        battery_level=mgr_dev.battery_level,
        battery_charging=mgr_dev.battery_charging,
        battery_temperature=mgr_dev.battery_temperature,
        screen_width=mgr_dev.screen_width,
        screen_height=mgr_dev.screen_height,
        screen_density=mgr_dev.screen_density,
        airplane_mode=mgr_dev.airplane_mode,
        wifi_ip=mgr_dev.wifi_ip,
        is_emulator=mgr_dev.is_emulator,
        paired=paired,
        last_seen=mgr_dev.last_seen
    )


@app.post("/api/devices/{serial_or_id}/connect")
async def connect_device_endpoint(serial_or_id: str):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found in registry")

    if dev.state == DeviceLifecycleState.UNAUTHORIZED:
        recovery = dev.error.recovery_hint if dev.error and dev.error.recovery_hint else "Unlock device and accept USB debugging prompt."
        raise HTTPException(
            status_code=403,
            detail=f"Device '{dev.id}' is unauthorized. Recovery hint: {recovery}"
        )

    if dev.state == DeviceLifecycleState.CONNECTED:
        return {
            "status": "already_connected",
            "device_id": dev.id,
            "serial": dev.serial,
            "state": dev.state.value
        }

    if dev.state not in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.DISCOVERED):
        raise HTTPException(
            status_code=409,
            detail=f"Device '{dev.id}' cannot be connected in state '{dev.state.value}'"
        )

    ok = device_registry.connect_device(dev.id)
    if not ok:
        raise HTTPException(status_code=500, detail=f"Provider failed to connect to device '{dev.id}'")

    updated = device_registry.get_device(dev.id)
    return {
        "status": "connected",
        "device_id": updated.id,
        "serial": updated.serial,
        "state": updated.state.value,
        "connected_at": updated.connected_at
    }


@app.post("/api/devices/{serial_or_id}/disconnect")
async def disconnect_device_endpoint(serial_or_id: str):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found in registry")

    session_manager.release_lease(dev.id, force=True)
    screen_streamer.notify_device_disconnected(dev.serial)
    recording_manager.handle_device_disconnected(dev.serial)

    if dev.state != DeviceLifecycleState.CONNECTED:
        return {
            "status": "not_connected",
            "device_id": dev.id,
            "serial": dev.serial,
            "state": dev.state.value
        }

    ok = device_registry.disconnect_device(dev.id)
    if not ok:
        raise HTTPException(status_code=500, detail=f"Provider failed to disconnect device '{dev.id}'")

    updated = device_registry.get_device(dev.id)
    return {
        "status": "disconnected",
        "device_id": updated.id,
        "serial": updated.serial,
        "state": updated.state.value
    }


# --- STREAMING & LEASE ENDPOINTS (PHASE 10) ---

@app.post("/api/devices/{serial_or_id}/stream/start")
async def start_device_stream(serial_or_id: str, req: Optional[StreamConfigRequest] = None):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    if dev and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(
            status_code=403,
            detail=f"Device '{dev.id}' is unauthorized. Confirm RSA key on physical screen."
        )
    cfg = StreamConfig(
        max_width=req.max_width if req else 720,
        quality=req.quality if req else 75,
        max_fps=req.max_fps if req else 30
    )
    ok = await screen_streamer.start_stream(raw_serial, cfg)
    diag = screen_streamer.get_diagnostics(raw_serial)
    if not ok:
        raise HTTPException(status_code=500, detail=diag.error_message or "Failed to start stream")
    return diag.model_dump()


@app.post("/api/devices/{serial_or_id}/stream/stop")
async def stop_device_stream(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    await screen_streamer.stop_stream(raw_serial)
    return {"status": "stopped", "serial": raw_serial}


@app.get("/api/devices/{serial_or_id}/stream/status")
async def get_stream_status(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    diag = screen_streamer.get_diagnostics(raw_serial)
    return diag.model_dump()


@app.post("/api/devices/{serial_or_id}/lease")
async def acquire_device_lease(serial_or_id: str, req: LeaseRequest):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    target_id = dev.id if dev else (f"android:{serial_or_id}" if not serial_or_id.startswith("android:") else serial_or_id)
    try:
        lease = session_manager.acquire_lease(
            target_id,
            client_id=req.client_id,
            duration_seconds=req.duration_seconds,
            purpose=req.purpose
        )
        return lease.model_dump()
    except LeaseConflictError as lce:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "DEVICE_ALREADY_LEASED",
                "message": str(lce),
                "held_by": lce.held_by,
                "expires_in_seconds": lce.expires_in_seconds
            }
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))


@app.post("/api/devices/{serial_or_id}/lease/renew")
async def renew_device_lease(serial_or_id: str, req: LeaseRenewRequest):
    dev = device_registry.get_device(serial_or_id)
    target_id = dev.id if dev else (f"android:{serial_or_id}" if not serial_or_id.startswith("android:") else serial_or_id)
    try:
        lease = session_manager.renew_lease(target_id, req.session_token, req.extension_seconds)
        return lease.model_dump()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.delete("/api/devices/{serial_or_id}/lease")
async def release_device_lease(serial_or_id: str, session_token: Optional[str] = None, force: bool = False):
    dev = device_registry.get_device(serial_or_id)
    target_id = dev.id if dev else (f"android:{serial_or_id}" if not serial_or_id.startswith("android:") else serial_or_id)
    try:
        session_manager.release_lease(target_id, session_token=session_token, force=force)
        return {"status": "released", "device_id": target_id}
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))


@app.get("/api/devices/{serial_or_id}/lease")
async def get_device_lease(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    target_id = dev.id if dev else (f"android:{serial_or_id}" if not serial_or_id.startswith("android:") else serial_or_id)
    lease = session_manager.get_active_lease(target_id)
    if not lease:
        return {"active": False, "device_id": target_id}
    return {"active": True, "lease": lease.model_dump()}


@app.get("/api/sessions")
async def list_active_sessions():
    leases = session_manager.list_active_leases()
    return [l.model_dump() for l in leases]


# --- TELEMETRY & INPUT ENDPOINTS ---

@app.get("/api/devices/{serial}/telemetry", response_model=DeviceTelemetry)
async def get_telemetry(serial: str):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    telemetry = telemetry_collector.collect(raw_serial)
    await bench_bridge.broadcast_telemetry(telemetry.model_dump())
    return telemetry


@app.get("/api/devices/{serial}/screenshot")
async def get_screenshot(serial: str, max_width: int = 1080, quality: int = 75):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    
    img_bytes = await asyncio.to_thread(input_controller.take_screenshot, raw_serial, max_width, quality)
    if not img_bytes:
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")
    
    return Response(content=img_bytes, media_type="image/jpeg")


@app.post("/api/devices/{serial}/input/tap")
async def tap_device(serial: str, req: TapRequest):
    _sync_mock_devices()
    raw_serial = _resolve_serial(serial)
    dev = device_registry.get_device(serial) or device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    if hasattr(dev, "state") and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail=f"Device {serial} is unauthorized.")

    ok = input_controller.tap(raw_serial, req.x, req.y, session_token=req.session_token)
    if not ok:
        lease = session_manager.get_active_lease(raw_serial)
        if lease and lease.session_token != req.session_token:
            raise HTTPException(
                status_code=409,
                detail=f"Device is exclusively locked by session '{lease.client_id}'."
            )
        raise HTTPException(status_code=400, detail="Tap action failed or coordinates out of bounds")
    return {"status": "ok", "action": "tap", "x": req.x, "y": req.y}


@app.post("/api/devices/{serial}/input/swipe")
async def swipe_device(serial: str, req: SwipeRequest):
    _sync_mock_devices()
    raw_serial = _resolve_serial(serial)
    dev = device_registry.get_device(serial) or device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    if hasattr(dev, "state") and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail=f"Device {serial} is unauthorized.")

    ok = input_controller.swipe(raw_serial, req.x1, req.y1, req.x2, req.y2, req.duration_ms, session_token=req.session_token)
    if not ok:
        lease = session_manager.get_active_lease(raw_serial)
        if lease and lease.session_token != req.session_token:
            raise HTTPException(
                status_code=409,
                detail=f"Device is exclusively locked by session '{lease.client_id}'."
            )
        raise HTTPException(status_code=400, detail="Swipe action failed or coordinates out of bounds")
    return {"status": "ok", "action": "swipe"}


@app.post("/api/devices/{serial}/input/key")
async def key_event(serial: str, req: KeyRequest):
    _sync_mock_devices()
    raw_serial = _resolve_serial(serial)
    dev = device_registry.get_device(serial) or device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    if hasattr(dev, "state") and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail=f"Device {serial} is unauthorized.")

    ok = input_controller.keyevent(raw_serial, req.key, session_token=req.session_token)
    if not ok:
        lease = session_manager.get_active_lease(raw_serial)
        if lease and lease.session_token != req.session_token:
            raise HTTPException(
                status_code=409,
                detail=f"Device is exclusively locked by session '{lease.client_id}'."
            )
        raise HTTPException(status_code=400, detail=f"Key event '{req.key}' failed")
    return {"status": "ok", "action": "keyevent", "key": req.key}


@app.post("/api/devices/{serial}/input/text")
async def type_text(serial: str, req: TextRequest):
    _sync_mock_devices()
    raw_serial = _resolve_serial(serial)
    dev = device_registry.get_device(serial) or device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    if hasattr(dev, "state") and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(status_code=403, detail=f"Device {serial} is unauthorized.")

    ok = input_controller.type_text(raw_serial, req.text, session_token=req.session_token)
    if not ok:
        lease = session_manager.get_active_lease(raw_serial)
        if lease and lease.session_token != req.session_token:
            raise HTTPException(
                status_code=409,
                detail=f"Device is exclusively locked by session '{lease.client_id}'."
            )
        raise HTTPException(status_code=400, detail="Type text action failed")
    return {"status": "ok", "action": "type_text"}


@app.post("/api/devices/{serial}/apps/launch")
async def launch_app(serial: str, req: AppLaunchRequest):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.launch_app(raw_serial, req.package, req.activity, session_token=req.session_token)
    return {"status": "ok" if ok else "failed", "package": req.package}


@app.post("/api/devices/{serial}/apps/stop")
async def stop_app(serial: str, req: AppStopRequest):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.stop_app(raw_serial, req.package, session_token=req.session_token)
    return {"status": "ok" if ok else "failed", "package": req.package}


@app.post("/api/devices/{serial}/tests/smoke", response_model=TestRunReport)
async def run_smoke(serial: str, req: SmokeTestRequest):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    report = await test_runner.run_smoke_test(raw_serial, req.package, req.activity)
    return report


@app.get("/api/devices/{serial}/logcat")
async def get_logcat_history(serial: str, limit: int = 100, level: Optional[str] = None):
    raw_serial = _resolve_serial(serial)
    dev = device_manager.get_device(raw_serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    return logcat_service.get_history(raw_serial, limit, level)


# --- WEBSOCKET ENDPOINTS ---

@app.websocket("/ws/devices/{serial}/stream")
@app.websocket("/ws/devices/{serial}/screen")
async def ws_screen_stream(websocket: WebSocket, serial: str):
    raw_serial = _resolve_serial(serial)
    await screen_streamer.connect(raw_serial, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("{"):
                try:
                    import json
                    cmd = json.loads(data)
                    if cmd.get("type") == "input":
                        action = cmd.get("action")
                        st = cmd.get("session_token")
                        if action == "tap":
                            input_controller.tap(raw_serial, cmd.get("x", 0), cmd.get("y", 0), session_token=st)
                        elif action == "key":
                            input_controller.keyevent(raw_serial, cmd.get("key"), session_token=st)
                        elif action == "swipe":
                            input_controller.swipe(raw_serial, cmd.get("x1", 0), cmd.get("y1", 0), cmd.get("x2", 0), cmd.get("y2", 0), duration_ms=cmd.get("duration_ms", 300), session_token=st)
                        elif action == "text":
                            input_controller.type_text(raw_serial, cmd.get("text", ""), session_token=st)
                except Exception:
                    pass
    except WebSocketDisconnect:
        await screen_streamer.disconnect(raw_serial, websocket)
    except Exception:
        await screen_streamer.disconnect(raw_serial, websocket)


@app.websocket("/ws/devices/{serial}/logcat")
async def ws_logcat_stream(websocket: WebSocket, serial: str):
    await logcat_service.connect(serial, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await logcat_service.disconnect(serial, websocket)
    except Exception:
        await logcat_service.disconnect(serial, websocket)


# --- PHASE 11: ANDROID VIRTUAL DEVICE (AVD) ENDPOINTS ---

@app.get("/api/avd/environment", response_model=SdkEnvironmentStatus)
async def get_avd_environment():
    return avd_manager.sdk_detector.detect_environment()


@app.get("/api/avd/list", response_model=List[AvdConfig])
async def list_avds():
    return avd_manager.list_avds()


@app.get("/api/avd/{name}", response_model=AvdConfig)
async def get_avd_config(name: str):
    avd = avd_manager.get_avd(name)
    if not avd:
        raise HTTPException(status_code=404, detail=f"AVD '{name}' not found.")
    return avd


@app.post("/api/avd/{name}/launch")
async def launch_avd(name: str, options: Optional[EmulatorLaunchOptions] = None):
    try:
        session = await avd_manager.launch_emulator(name, options=options)
        return {
            "status": "launching",
            "avd": name,
            "pid": session.pid,
            "state": session.state.value
        }
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=400, detail=str(re))


@app.post("/api/avd/{name}/stop")
async def stop_avd(name: str, force: bool = False):
    ok = await avd_manager.stop_emulator(name, force=force)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No running emulator session found for '{name}'.")
    return {"status": "stopped", "avd": name}


@app.post("/api/avd/create", response_model=AvdConfig)
async def create_avd_endpoint(req: CreateAvdRequest):
    try:
        created = avd_manager.create_avd(req)
        return created
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=412, detail=str(re))


@app.delete("/api/avd/{name}")
async def delete_avd_endpoint(name: str, confirm: bool = False):
    try:
        avd_manager.delete_avd(name, confirm=confirm)
        return {"status": "deleted", "avd": name}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=409, detail=str(re))


@app.get("/api/avd/{name}/status")
async def get_avd_status(name: str):
    avd = avd_manager.get_avd(name)
    if not avd:
        raise HTTPException(status_code=404, detail=f"AVD '{name}' not found.")
    return {
        "avd": name,
        "status": avd.status.value,
        "running_serial": avd.running_serial,
        "pid": avd.pid,
        "error_message": avd.error_message
    }


# ==============================================================================
# Phase 12: Apple Device Provider REST Endpoints
# ==============================================================================

@app.get("/api/providers/apple/health")
async def get_apple_provider_health():
    """Returns diagnostic health, usbmuxd status, and toolchain discovery for Apple provider."""
    return apple_provider.get_health()


@app.get("/api/providers/apple/capabilities")
async def get_apple_capabilities():
    """Returns comprehensive technical capability matrix and platform boundaries for Apple devices."""
    return apple_provider.get_detailed_capabilities()


@app.get("/api/devices/{device_id:path}/apple/trust")
async def get_apple_device_trust(device_id: str):
    """Inspects lockdown pairing and trust status for an Apple device."""
    device = device_registry.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found in registry.")
    if device.platform != DevicePlatform.APPLE_PHYSICAL:
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not an Apple physical device.")
    
    pairing_state = device.metadata.get("pairing_state", "unknown")
    return {
        "device_id": device.id,
        "serial": device.serial,
        "display_name": device.display_name,
        "pairing_state": pairing_state,
        "lifecycle_state": device.state.value,
        "is_authorized": device.state == DeviceLifecycleState.AVAILABLE,
        "error": device.error.model_dump() if device.error else None,
        "guidance": (
            "Unlock device and tap 'Trust This Computer' on the screen."
            if device.state == DeviceLifecycleState.UNAUTHORIZED
            else "Device is paired and ready for metadata inspection and telemetry."
        )
    }


@app.post("/api/devices/{device_id:path}/apple/pair")
async def pair_apple_device(device_id: str):
    """Validates or refreshes pairing handshake for an Apple device."""
    device = device_registry.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found.")
    if device.platform != DevicePlatform.APPLE_PHYSICAL:
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not an Apple physical device.")

    if device.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(
            status_code=403,
            detail="Cannot pair: device trust prompt pending. Please unlock device and tap 'Trust This Computer'."
        )

    return {
        "status": "paired",
        "device_id": device.id,
        "message": "Device pairing verified successfully."
    }


# ==============================================================================
# Phase 13: Screenshots, Recordings, Logs, Diagnostics & Automation
# ==============================================================================

# --- Screenshots ---

@app.post("/api/devices/{serial_or_id:path}/screenshots", response_model=ArtifactRecord)
async def capture_screenshot_endpoint(serial_or_id: str, req: Optional[CaptureScreenshotRequest] = None):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    target_id = dev.id if dev else f"android:{raw_serial}"

    if dev and dev.state == DeviceLifecycleState.UNAUTHORIZED:
        raise HTTPException(
            status_code=403,
            detail=f"Device '{dev.id}' is unauthorized. Physical trust authorization required."
        )

    if dev and dev.platform in (DevicePlatform.APPLE_PHYSICAL, DevicePlatform.APPLE_VIRTUAL):
        # Truthful reporting on Apple screenshot capability
        raise HTTPException(
            status_code=422,
            detail="iOS screenshot capture is experimental on Windows and requires an Apple Developer Disk Image (DDI) mounted via native Xcode tunnel."
        )

    quality = req.quality if req else 80
    max_w = req.max_width if req else 1080
    img_bytes = await asyncio.to_thread(input_controller.take_screenshot, raw_serial, max_w, quality)
    if not img_bytes:
        raise HTTPException(status_code=500, detail=f"Screenshot capture failed for device '{target_id}'")

    name = req.name if (req and req.name) else f"screenshot_{raw_serial}"
    session_token = req.session_token if req else None

    artifact = artifact_manager.save_artifact(
        name=name,
        artifact_type=ArtifactType.SCREENSHOT,
        file_format="jpeg",
        data=img_bytes,
        device_id=target_id,
        session_token=session_token,
        metadata={"max_width": str(max_w), "quality": str(quality)}
    )
    return artifact


@app.get("/api/devices/{serial_or_id:path}/screenshots", response_model=List[ArtifactRecord])
async def list_device_screenshots(serial_or_id: str, limit: int = 50):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    target_id = dev.id if dev else f"android:{raw_serial}"
    return artifact_manager.list_artifacts(
        artifact_type=ArtifactType.SCREENSHOT,
        device_id=target_id,
        limit=limit
    )


# --- Screen Recordings ---

@app.post("/api/devices/{serial_or_id:path}/recording/start", response_model=RecordingSession)
async def start_recording_endpoint(serial_or_id: str, req: Optional[StartRecordingRequest] = None):
    _sync_mock_devices()
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)

    max_sec = req.max_duration_seconds if req else 180
    bitrate = req.bit_rate_bps if req else 4000000

    try:
        session = await recording_manager.start_recording(
            raw_serial,
            max_duration_seconds=max_sec,
            bit_rate_bps=bitrate
        )
        return session
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=409 if "already actively recording" in str(ve) else 422, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))


@app.post("/api/devices/{serial_or_id:path}/recording/stop", response_model=RecordingSession)
async def stop_recording_endpoint(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    try:
        session = await recording_manager.stop_recording(raw_serial)
        return session
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.get("/api/devices/{serial_or_id:path}/recording/status", response_model=Optional[RecordingSession])
async def get_recording_status_endpoint(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    sess = recording_manager.get_session(raw_serial)
    if not sess:
        return RecordingSession(
            session_id="",
            serial=raw_serial,
            device_id=dev.id if dev else f"android:{raw_serial}",
            platform=dev.platform.value if dev else "android_physical",
            state=RecordingState.IDLE
        )
    return sess


@app.get("/api/devices/{serial_or_id:path}/recordings", response_model=List[ArtifactRecord])
async def list_device_recordings(serial_or_id: str, limit: int = 50):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    target_id = dev.id if dev else f"android:{raw_serial}"
    return artifact_manager.list_artifacts(
        artifact_type=ArtifactType.RECORDING,
        device_id=target_id,
        limit=limit
    )


# --- Device Logs ---

@app.get("/api/devices/{serial_or_id:path}/logs")
async def get_device_logs(
    serial_or_id: str,
    limit: int = 100,
    level: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)

    if dev and dev.platform in (DevicePlatform.APPLE_PHYSICAL, DevicePlatform.APPLE_VIRTUAL):
        # Apple device log status
        health = apple_provider.get_health()
        toolchain = health.get("toolchain", {}).get("detected_type")
        if not toolchain:
            return {
                "supported": False,
                "reason": "iOS syslog streaming requires idevicesyslog on host PATH or pymobiledevice3 tunnel.",
                "logs": []
            }

    entries = logcat_service.get_history(raw_serial, limit=limit, level=level, tag=tag, search=search)
    return {
        "supported": True,
        "device_id": dev.id if dev else f"android:{raw_serial}",
        "count": len(entries),
        "logs": entries
    }


@app.delete("/api/devices/{serial_or_id:path}/logs")
async def clear_device_logs(serial_or_id: str):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    ok = logcat_service.clear_buffer(raw_serial)
    return {"status": "cleared" if ok else "empty", "serial": raw_serial}


@app.get("/api/devices/{serial_or_id:path}/logs/export")
async def export_device_logs(
    serial_or_id: str,
    format: str = "text",
    level: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    save_artifact: bool = False
):
    dev = device_registry.get_device(serial_or_id)
    raw_serial = dev.serial if dev else _resolve_serial(serial_or_id)
    target_id = dev.id if dev else f"android:{raw_serial}"

    exported_content = logcat_service.export_logs(
        raw_serial, format_type=format, level=level, tag=tag, search=search
    )

    if save_artifact:
        file_ext = "json" if format.lower() == "json" else "log"
        art = artifact_manager.save_artifact(
            name=f"log_export_{raw_serial}_{int(datetime.now(timezone.utc).timestamp())}.{file_ext}",
            artifact_type=ArtifactType.LOG_EXPORT,
            file_format=file_ext,
            data=exported_content.encode("utf-8"),
            device_id=target_id,
            metadata={"format": format, "level": level or "ALL"}
        )
        return {
            "status": "exported",
            "artifact": art.model_dump(),
            "byte_count": len(exported_content)
        }

    media_type = "application/json" if format.lower() == "json" else "text/plain"
    return Response(
        content=exported_content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="logs_{raw_serial}.{format}"'}
    )


# --- Structured Device Diagnostics ---

@app.get("/api/devices/{serial_or_id:path}/diagnostics", response_model=DeviceDiagnosticReport)
async def get_device_diagnostics(serial_or_id: str):
    report = diagnostics_service.get_diagnostics(serial_or_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Device '{serial_or_id}' not found.")
    return report


# --- Automation Workflows & Executions ---

@app.post("/api/automation/workflows", response_model=WorkflowDefinition)
async def create_workflow_endpoint(req: CreateWorkflowRequest):
    wf = WorkflowDefinition(
        name=req.name,
        target_device=req.target_device,
        steps=req.steps,
        description=req.description or "",
        timeout_seconds=req.timeout_seconds
    )
    valid, err = automation_engine.validate_workflow(wf)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Workflow validation error: {err}")
    return automation_engine.register_workflow(wf)


@app.get("/api/automation/workflows", response_model=List[WorkflowDefinition])
async def list_workflows_endpoint():
    return automation_engine.list_workflows()


@app.get("/api/automation/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow_endpoint(workflow_id: str):
    wf = automation_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return wf


@app.post("/api/automation/workflows/{workflow_id}/execute", response_model=WorkflowExecutionReport)
async def execute_workflow_endpoint(workflow_id: str, session_token: Optional[str] = None):
    wf = automation_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    try:
        report = await automation_engine.execute_workflow(wf, session_token=session_token)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=409 if "busy" in str(ve) else 400, detail=str(ve))


@app.post("/api/automation/execute-inline", response_model=WorkflowExecutionReport)
async def execute_inline_workflow_endpoint(req: ExecuteInlineWorkflowRequest):
    wf = WorkflowDefinition(
        name=req.workflow.name,
        target_device=req.workflow.target_device,
        steps=req.workflow.steps,
        description=req.workflow.description or "",
        timeout_seconds=req.workflow.timeout_seconds
    )
    try:
        report = await automation_engine.execute_workflow(wf, session_token=req.session_token)
        return report
    except ValueError as ve:
        raise HTTPException(status_code=409 if "busy" in str(ve) else 400, detail=str(ve))


@app.get("/api/automation/executions", response_model=List[WorkflowExecutionReport])
async def list_executions_endpoint(device_id: Optional[str] = None, limit: int = 50):
    return automation_engine.list_executions(device_id=device_id, limit=limit)


@app.get("/api/automation/executions/{execution_id}", response_model=WorkflowExecutionReport)
async def get_execution_endpoint(execution_id: str):
    report = automation_engine.get_execution(execution_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return report


@app.post("/api/automation/executions/{execution_id}/cancel")
async def cancel_execution_endpoint(execution_id: str):
    ok = await automation_engine.cancel_execution(execution_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' is not currently running.")
    return {"status": "cancelled", "execution_id": execution_id}


# --- Artifact Management ---

@app.get("/api/artifacts", response_model=List[ArtifactRecord])
async def list_artifacts_endpoint(
    type: Optional[ArtifactType] = None,
    device_id: Optional[str] = None,
    limit: int = 100
):
    return artifact_manager.list_artifacts(artifact_type=type, device_id=device_id, limit=limit)


@app.get("/api/artifacts/storage/summary", response_model=StorageSummary)
async def get_storage_summary_endpoint():
    return artifact_manager.get_storage_summary()


@app.get("/api/artifacts/{artifact_id}", response_model=ArtifactRecord)
async def get_artifact_metadata_endpoint(artifact_id: str):
    rec = artifact_manager.get_artifact(artifact_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
    return rec


@app.get("/api/artifacts/{artifact_id}/download")
async def download_artifact_endpoint(artifact_id: str):
    rec = artifact_manager.get_artifact(artifact_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")

    path = artifact_manager.get_artifact_file_path(artifact_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact file for '{artifact_id}' not found on disk.")

    media_types = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "mp4": "video/mp4",
        "txt": "text/plain",
        "log": "text/plain",
        "json": "application/json"
    }
    mt = media_types.get(rec.file_format.lower(), "application/octet-stream")
    return FileResponse(path=str(path), media_type=mt, filename=rec.name)


@app.delete("/api/artifacts/{artifact_id}")
async def delete_artifact_endpoint(artifact_id: str, confirm: bool = False):
    try:
        ok = artifact_manager.delete_artifact(artifact_id, confirm=confirm)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found.")
        return {"status": "deleted", "artifact_id": artifact_id}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


# --- STATIC ASSETS & SPA ROUTING ---
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/overview", include_in_schema=False)
@app.get("/devices", include_in_schema=False)
@app.get("/virtual", include_in_schema=False)
@app.get("/sessions", include_in_schema=False)
@app.get("/automation", include_in_schema=False)
@app.get("/diagnostics", include_in_schema=False)
@app.get("/settings", include_in_schema=False)
async def serve_spa_page():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
