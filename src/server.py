"""
FastAPI Server & Control Room for KELVRA Device Lab.
Provides REST and WebSocket endpoints for device teleoperation, streaming, and testing.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.bench_bridge import BenchBridge
from src.device_manager import DeviceInfo, DeviceManager
from src.device_telemetry import DeviceTelemetry, TelemetryCollector
from src.input_controller import InputController
from src.logcat_service import LogcatService
from src.screen_streamer import ScreenStreamer
from src.test_runner import TestRunReport, TestRunner

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


# Request Models
class TapRequest(BaseModel):
    x: int
    y: int


class SwipeRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    duration_ms: int = 300


class KeyRequest(BaseModel):
    key: str


class TextRequest(BaseModel):
    text: str


class AppLaunchRequest(BaseModel):
    package: str
    activity: Optional[str] = None


class AppStopRequest(BaseModel):
    package: str


class SmokeTestRequest(BaseModel):
    package: str
    activity: Optional[str] = None


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


# --- REST ENDPOINTS ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "kelvra-device-lab",
        "port": int(os.environ.get("KELVRA_DEVICE_LAB_PORT", 8098)),
        "active_devices": len(device_manager._cached_devices)
    }


@app.get("/api/devices", response_model=List[DeviceInfo])
async def list_devices():
    devices = device_manager.scan_devices()
    for dev in devices:
        dev.paired = bench_bridge.check_pairing(dev.serial)
    return devices


@app.get("/api/devices/{serial}", response_model=DeviceInfo)
async def get_device(serial: str):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    dev.paired = bench_bridge.check_pairing(serial)
    return dev


@app.get("/api/devices/{serial}/telemetry", response_model=DeviceTelemetry)
async def get_telemetry(serial: str):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    telemetry = telemetry_collector.collect(serial)
    await bench_bridge.broadcast_telemetry(telemetry.model_dump())
    return telemetry


@app.get("/api/devices/{serial}/screenshot")
async def get_screenshot(serial: str, max_width: int = 1080, quality: int = 75):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    
    img_bytes = await asyncio.to_thread(input_controller.take_screenshot, serial, max_width, quality)
    if not img_bytes:
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")
    
    return Response(content=img_bytes, media_type="image/jpeg")


@app.post("/api/devices/{serial}/input/tap")
async def tap_device(serial: str, req: TapRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.tap(serial, req.x, req.y)
    return {"status": "ok" if ok else "failed", "action": "tap", "x": req.x, "y": req.y}


@app.post("/api/devices/{serial}/input/swipe")
async def swipe_device(serial: str, req: SwipeRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.swipe(serial, req.x1, req.y1, req.x2, req.y2, req.duration_ms)
    return {"status": "ok" if ok else "failed", "action": "swipe"}


@app.post("/api/devices/{serial}/input/key")
async def key_event(serial: str, req: KeyRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.keyevent(serial, req.key)
    return {"status": "ok" if ok else "failed", "action": "keyevent", "key": req.key}


@app.post("/api/devices/{serial}/input/text")
async def type_text(serial: str, req: TextRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.type_text(serial, req.text)
    return {"status": "ok" if ok else "failed", "action": "type_text"}


@app.post("/api/devices/{serial}/apps/launch")
async def launch_app(serial: str, req: AppLaunchRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.launch_app(serial, req.package, req.activity)
    return {"status": "ok" if ok else "failed", "package": req.package}


@app.post("/api/devices/{serial}/apps/stop")
async def stop_app(serial: str, req: AppStopRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    ok = input_controller.stop_app(serial, req.package)
    return {"status": "ok" if ok else "failed", "package": req.package}


@app.post("/api/devices/{serial}/tests/smoke", response_model=TestRunReport)
async def run_smoke(serial: str, req: SmokeTestRequest):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    report = await test_runner.run_smoke_test(serial, req.package, req.activity)
    return report


@app.get("/api/devices/{serial}/logcat")
async def get_logcat_history(serial: str, limit: int = 100, level: Optional[str] = None):
    dev = device_manager.get_device(serial)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {serial} not found")
    return logcat_service.get_history(serial, limit, level)


# --- WEBSOCKET ENDPOINTS ---

@app.websocket("/ws/devices/{serial}/screen")
async def ws_screen_stream(websocket: WebSocket, serial: str):
    await screen_streamer.connect(serial, websocket)
    try:
        while True:
            # Keep connection open and receive potential client interactions
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await screen_streamer.disconnect(serial, websocket)
    except Exception:
        await screen_streamer.disconnect(serial, websocket)


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


# --- STATIC ASSETS ---
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
