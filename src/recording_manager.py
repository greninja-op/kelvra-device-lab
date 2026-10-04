"""
Recording Manager for KELVRA Device Lab.
Orchestrates on-device and stream recording sessions for supported Android physical and virtual devices.
Enforces provider capability checks, platform boundaries (iOS recording is explicitly unavailable on Windows),
session lifecycle supervision, graceful cancellation on disconnect, and artifact archiving.
"""

import asyncio
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field

from src.artifact_manager import ArtifactManager, ArtifactType
from src.device_manager import DeviceManager
from src.domain_model import DevicePlatform, DeviceLifecycleState

logger = logging.getLogger("kelvra.device_lab.recording")


class RecordingState(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RECORDING = "RECORDING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class RecordingSession(BaseModel):
    session_id: str
    serial: str
    device_id: str
    platform: str
    state: RecordingState = RecordingState.IDLE
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    artifact_id: Optional[str] = None
    error_message: Optional[str] = None
    remote_tmp_path: Optional[str] = None


class RecordingManager:
    """Manages active screen recording sessions on mobile hardware."""

    def __init__(
        self,
        device_manager: DeviceManager,
        artifact_manager: ArtifactManager,
        device_registry=None
    ):
        self.device_manager = device_manager
        self.artifact_manager = artifact_manager
        self.device_registry = device_registry
        self._active_sessions: Dict[str, RecordingSession] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._start_times: Dict[str, float] = {}

    def set_device_registry(self, device_registry):
        self.device_registry = device_registry

    def _resolve_device(self, serial_or_id: str):
        if self.device_registry:
            dev = self.device_registry.get_device(serial_or_id)
            if dev:
                return dev
        raw_serial = serial_or_id.split(":", 1)[1] if ":" in serial_or_id else serial_or_id
        if self.device_registry:
            dev = self.device_registry.get_device(f"android:{raw_serial}")
            if dev:
                return dev
        return None

    def get_session(self, serial_or_id: str) -> Optional[RecordingSession]:
        raw_serial = serial_or_id.split(":", 1)[1] if ":" in serial_or_id else serial_or_id
        session = self._active_sessions.get(raw_serial)
        if session and session.state == RecordingState.RECORDING:
            # Update elapsed duration
            start_t = self._start_times.get(raw_serial, 0.0)
            if start_t > 0:
                session.duration_seconds = round(time.time() - start_t, 1)
        return session

    async def start_recording(
        self,
        serial_or_id: str,
        max_duration_seconds: int = 180,
        bit_rate_bps: int = 4000000
    ) -> RecordingSession:
        """Initiates screen recording session after validating platform and state."""
        dev = self._resolve_device(serial_or_id)
        raw_serial = dev.serial if dev else (serial_or_id.split(":", 1)[1] if ":" in serial_or_id else serial_or_id)

        # 1. Capability & Platform boundary check
        if dev:
            if dev.platform in (DevicePlatform.APPLE_PHYSICAL, DevicePlatform.APPLE_VIRTUAL):
                raise ValueError(
                    "Screen recording is not supported for iOS/iPadOS devices on Windows host workstations. "
                    "Apple display buffers are protected by OS-level sandbox constraints."
                )
            if dev.state == DeviceLifecycleState.UNAUTHORIZED:
                raise PermissionError(f"Cannot record unauthorized device '{dev.id}'. Unlock device and accept RSA trust.")
            if dev.state in (DeviceLifecycleState.UNAVAILABLE, DeviceLifecycleState.DISCONNECTED):
                raise ValueError(f"Cannot record offline or disconnected device '{dev.id}'.")

        # 2. Prevent conflicting concurrent recordings on same device
        existing = self.get_session(raw_serial)
        if existing and existing.state == RecordingState.RECORDING:
            raise ValueError(f"Device '{raw_serial}' is already actively recording (session {existing.session_id}).")

        # 3. Initialize session model
        session_id = f"rec-{uuid.uuid4().hex[:10]}"
        remote_tmp = f"/sdcard/kelvra_rec_{session_id}.mp4"
        now_iso = datetime.now(timezone.utc).isoformat()

        session = RecordingSession(
            session_id=session_id,
            serial=raw_serial,
            device_id=dev.id if dev else f"android:{raw_serial}",
            platform=dev.platform.value if dev else "android_physical",
            state=RecordingState.RECORDING,
            started_at=now_iso,
            remote_tmp_path=remote_tmp
        )
        self._active_sessions[raw_serial] = session
        self._start_times[raw_serial] = time.time()

        # 4. Launch recording worker
        if raw_serial in self.device_manager._mock_devices:
            # Deterministic mock recording for tests
            logger.info(f"Mock recording started on {raw_serial} (session {session_id})")
            return session

        # Real Android device: spawn `adb shell screenrecord`
        cmd = [
            self.device_manager.adb_path,
            "-s", raw_serial,
            "shell",
            "screenrecord",
            "--time-limit", str(min(180, max_duration_seconds)),
            "--bit-rate", str(bit_rate_bps),
            remote_tmp
        ]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            self._processes[raw_serial] = proc
            logger.info(f"Launched screenrecord process PID={proc.pid} on {raw_serial}")
        except Exception as exc:
            session.state = RecordingState.FAILED
            session.error_message = f"Failed to spawn screenrecord process: {exc}"
            logger.error(session.error_message)
            raise RuntimeError(session.error_message)

        return session

    async def stop_recording(self, serial_or_id: str) -> RecordingSession:
        """Gracefully stops recording, pulls output file, and stores as an artifact."""
        raw_serial = serial_or_id.split(":", 1)[1] if ":" in serial_or_id else serial_or_id
        session = self.get_session(raw_serial)
        if not session or session.state != RecordingState.RECORDING:
            raise ValueError(f"No active screen recording found for device '{raw_serial}'.")

        session.state = RecordingState.STOPPING
        start_t = self._start_times.get(raw_serial, time.time())
        duration = max(0.1, round(time.time() - start_t, 1))
        session.duration_seconds = duration
        session.stopped_at = datetime.now(timezone.utc).isoformat()

        # 1. Terminate recording process if active
        proc = self._processes.pop(raw_serial, None)
        if proc:
            try:
                # Send SIGINT / CTRL_C_EVENT to allow screenrecord to finalize MP4 container headers
                proc.terminate()
                try:
                    proc.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1.0)
            except Exception as e:
                logger.warning(f"Error terminating recording process: {e}")

        # 2. Extract recording bytes
        recording_bytes = b""
        if raw_serial in self.device_manager._mock_devices:
            # Minimal synthetic MP4 container header (ftyp isom)
            recording_bytes = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free" + b"\x00" * 1024
        else:
            # Pull file from device
            if session.remote_tmp_path:
                local_tmp = Path(self.artifact_manager.base_dir) / f"temp_{session.session_id}.mp4"
                try:
                    # Allow device a moment to finalize mp4 box
                    await asyncio.sleep(0.5)
                    pull_res = self.device_manager.run_adb(
                        ["pull", session.remote_tmp_path, str(local_tmp)],
                        serial=raw_serial,
                        timeout=15.0
                    )
                    if local_tmp.exists():
                        recording_bytes = local_tmp.read_bytes()
                        local_tmp.unlink(missing_ok=True)
                    # Clean up on device
                    self.device_manager.run_adb(["shell", "rm", "-f", session.remote_tmp_path], serial=raw_serial, timeout=5.0)
                except Exception as pull_err:
                    logger.error(f"Failed to pull recording from device: {pull_err}")

        # 3. Store as artifact if bytes retrieved
        if recording_bytes:
            session.file_size_bytes = len(recording_bytes)
            artifact = self.artifact_manager.save_artifact(
                name=f"recording_{session.session_id}.mp4",
                artifact_type=ArtifactType.RECORDING,
                file_format="mp4",
                data=recording_bytes,
                device_id=session.device_id,
                metadata={
                    "session_id": session.session_id,
                    "duration_seconds": str(session.duration_seconds),
                    "recorded_at": session.started_at or ""
                }
            )
            session.artifact_id = artifact.artifact_id
            session.state = RecordingState.STOPPED
            logger.info(f"Finalized recording {session.session_id} ({session.file_size_bytes} bytes, artifact {artifact.artifact_id})")
        else:
            session.state = RecordingState.FAILED
            session.error_message = "No recording data captured or file transfer failed."
            logger.warning(f"Recording {session.session_id} produced no data.")

        return session

    def handle_device_disconnected(self, raw_serial: str):
        """Called by registry or streamer when a device disconnects during recording."""
        session = self._active_sessions.get(raw_serial)
        if session and session.state == RecordingState.RECORDING:
            logger.warning(f"Device {raw_serial} disconnected during active recording. Aborting session {session.session_id}.")
            proc = self._processes.pop(raw_serial, None)
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            session.state = RecordingState.FAILED
            session.error_message = "Device disconnected while recording was in progress."
            session.stopped_at = datetime.now(timezone.utc).isoformat()
