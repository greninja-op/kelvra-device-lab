"""
Logcat Service for KELVRA Device Lab.
Provides real-time logcat capture, buffer history, and WebSocket streaming.
"""

import asyncio
import collections
import logging
import re
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from pydantic import BaseModel

from src.device_manager import DeviceManager

logger = logging.getLogger("kelvra.device_lab.logcat")


class LogcatEntry(BaseModel):
    timestamp: str
    pid: int = 0
    tid: int = 0
    level: str = "I"
    tag: str = ""
    message: str = ""
    raw: str = ""


class LogcatService:
    """Manages real-time logcat processes and streaming to subscribers."""

    def __init__(self, device_manager: DeviceManager, buffer_size: int = 500):
        self.device_manager = device_manager
        self.buffer_size = buffer_size
        self._buffers: Dict[str, collections.deque] = {}
        self._subscribers: Dict[str, Set[WebSocket]] = {}
        self._logcat_tasks: Dict[str, asyncio.Task] = {}

    def get_history(self, serial: str, limit: int = 100, level: Optional[str] = None) -> List[dict]:
        """Fetch buffered log entries for a device."""
        if serial not in self._buffers:
            return []
        entries = list(self._buffers[serial])
        if level:
            level = level.upper()
            levels_order = ["V", "D", "I", "W", "E", "F"]
            if level in levels_order:
                min_idx = levels_order.index(level)
                entries = [e for e in entries if levels_order.index(e.get("level", "I")) >= min_idx]
        return entries[-limit:]

    async def connect(self, serial: str, websocket: WebSocket):
        await websocket.accept()
        if serial not in self._subscribers:
            self._subscribers[serial] = set()
            self._buffers[serial] = collections.deque(maxlen=self.buffer_size)

        self._subscribers[serial].add(websocket)
        logger.info(f"Client subscribed to logcat for {serial}")

        # Send existing history
        history = self.get_history(serial, limit=100)
        for item in history:
            await websocket.send_json(item)

        # Start logcat task if not running
        if serial not in self._logcat_tasks or self._logcat_tasks[serial].done():
            self._logcat_tasks[serial] = asyncio.create_task(self._logcat_reader(serial))

    async def disconnect(self, serial: str, websocket: WebSocket):
        if serial in self._subscribers:
            self._subscribers[serial].discard(websocket)
            logger.info(f"Client unsubscribed from logcat for {serial}")
            if not self._subscribers[serial]:
                del self._subscribers[serial]
                if serial in self._logcat_tasks:
                    self._logcat_tasks[serial].cancel()
                    del self._logcat_tasks[serial]

    async def _logcat_reader(self, serial: str):
        """Continuously reads logcat from device via asyncio subprocess."""
        if serial in self.device_manager._mock_devices:
            # Emit synthetic log messages for testing
            try:
                seq = 0
                while serial in self._subscribers:
                    seq += 1
                    entry = {
                        "timestamp": "12:00:00.000",
                        "pid": 1234,
                        "tid": 1234,
                        "level": "I",
                        "tag": "KelvraDeviceLab",
                        "message": f"Heartbeat telemetry tick #{seq}",
                        "raw": f"12:00:00.000  1234  1234 I KelvraDeviceLab: Heartbeat telemetry tick #{seq}"
                    }
                    await self._broadcast(serial, entry)
                    await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                pass
            return

        cmd = [self.device_manager.adb_path, "-s", serial, "logcat", "-v", "time"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Standard format: 10-03 14:15:22.123 D/Tag( 1234): message
            log_pattern = re.compile(r"^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+([VDIWEF])/([^\(]+)\(\s*(\d+)\):\s*(.*)$")

            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                raw_line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not raw_line:
                    continue

                match = log_pattern.match(raw_line)
                if match:
                    entry = {
                        "timestamp": match.group(1),
                        "level": match.group(2),
                        "tag": match.group(3).strip(),
                        "pid": int(match.group(4)),
                        "tid": 0,
                        "message": match.group(5),
                        "raw": raw_line
                    }
                else:
                    entry = {
                        "timestamp": "",
                        "level": "I",
                        "tag": "SYSTEM",
                        "pid": 0,
                        "tid": 0,
                        "message": raw_line,
                        "raw": raw_line
                    }

                await self._broadcast(serial, entry)

        except asyncio.CancelledError:
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
        except Exception as exc:
            logger.error(f"Logcat reader encountered error for {serial}: {exc}")

    async def _broadcast(self, serial: str, entry: dict):
        """Append to circular buffer and broadcast to subscribers."""
        if serial in self._buffers:
            self._buffers[serial].append(entry)

        dead_clients = set()
        for ws in list(self._subscribers.get(serial, [])):
            try:
                await ws.send_json(entry)
            except Exception:
                dead_clients.add(ws)

        for dead in dead_clients:
            await self.disconnect(serial, dead)
