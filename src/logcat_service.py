"""
Device Logging Service for KELVRA Device Lab.
Provides real-time logcat and system log capture, bounded circular buffer history,
regular expression secret sanitization, multi-parameter filtering, and artifact export.
"""

import asyncio
import collections
import json
import logging
import re
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from pydantic import BaseModel

from src.device_manager import DeviceManager

logger = logging.getLogger("kelvra.device_lab.logcat")


# Sensitive data redaction patterns
REDACTION_PATTERNS = [
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), "Bearer [REDACTED_SECRET]"),
    (re.compile(r"password=([^\s&]+)", re.IGNORECASE), "password=[REDACTED]"),
    (re.compile(r"passwd=([^\s&]+)", re.IGNORECASE), "passwd=[REDACTED]"),
    (re.compile(r"api[_-]?key=([^\s&]+)", re.IGNORECASE), "api_key=[REDACTED]"),
    (re.compile(r"session[_-]?token=([^\s&]+)", re.IGNORECASE), "session_token=[REDACTED]"),
    (re.compile(r"access[_-]?token=([^\s&]+)", re.IGNORECASE), "access_token=[REDACTED]"),
]


def sanitize_log_message(msg: str) -> str:
    """Applies security regex scrubbing to redact credentials and tokens from logs."""
    sanitized = msg
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class LogcatEntry(BaseModel):
    timestamp: str
    pid: int = 0
    tid: int = 0
    level: str = "I"
    tag: str = ""
    message: str = ""
    raw: str = ""


class LogcatService:
    """Manages real-time logcat processes, history buffers, filtering, and streaming."""

    def __init__(self, device_manager: DeviceManager, buffer_size: int = 2000):
        self.device_manager = device_manager
        self.buffer_size = buffer_size
        self._buffers: Dict[str, collections.deque] = {}
        self._subscribers: Dict[str, Set[WebSocket]] = {}
        self._logcat_tasks: Dict[str, asyncio.Task] = {}

    def get_or_create_buffer(self, serial: str) -> collections.deque:
        if serial not in self._buffers:
            self._buffers[serial] = collections.deque(maxlen=self.buffer_size)
        return self._buffers[serial]

    def clear_buffer(self, serial: str) -> bool:
        """Clears all buffered log lines for a device."""
        if serial in self._buffers:
            self._buffers[serial].clear()
            logger.info(f"Cleared log buffer for device {serial}")
            return True
        return False

    def get_history(
        self,
        serial: str,
        limit: int = 100,
        level: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """Fetch buffered log entries for a device with optional filtering."""
        if serial not in self._buffers:
            # Seed mock buffer if mock device
            if serial in self.device_manager._mock_devices:
                buf = self.get_or_create_buffer(serial)
                for i in range(1, 11):
                    buf.append({
                        "timestamp": f"12:00:0{i}.000",
                        "pid": 1234,
                        "tid": 1234,
                        "level": "I" if i % 2 == 0 else "D",
                        "tag": "KelvraDeviceLab",
                        "message": f"Verified telemetry line #{i}",
                        "raw": f"12:00:0{i}.000 1234 1234 I KelvraDeviceLab: Verified telemetry line #{i}"
                    })
            else:
                return []

        entries = list(self._buffers[serial])

        # 1. Level filter
        if level:
            level = level.upper()
            levels_order = ["V", "D", "I", "W", "E", "F"]
            if level in levels_order:
                min_idx = levels_order.index(level)
                entries = [
                    e for e in entries
                    if e.get("level", "I") in levels_order and levels_order.index(e.get("level", "I")) >= min_idx
                ]

        # 2. Tag filter
        if tag:
            tag_lower = tag.lower()
            entries = [e for e in entries if tag_lower in e.get("tag", "").lower()]

        # 3. Search text filter
        if search:
            search_lower = search.lower()
            entries = [
                e for e in entries
                if search_lower in e.get("message", "").lower() or search_lower in e.get("tag", "").lower()
            ]

        return entries[-limit:]

    def export_logs(
        self,
        serial: str,
        format_type: str = "text",
        level: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None
    ) -> str:
        """Exports log history formatted as plain text or JSON lines."""
        entries = self.get_history(serial, limit=self.buffer_size, level=level, tag=tag, search=search)
        if format_type.lower() == "json":
            return "\n".join(json.dumps(e) for e in entries)
        else:
            lines = []
            for e in entries:
                ts = e.get("timestamp", "")
                lvl = e.get("level", "I")
                tg = e.get("tag", "")
                msg = e.get("message", "")
                lines.append(f"{ts} [{lvl}] {tg}: {msg}")
            return "\n".join(lines)

    async def connect(self, serial: str, websocket: WebSocket):
        await websocket.accept()
        if serial not in self._subscribers:
            self._subscribers[serial] = set()
            self._buffers[serial] = collections.deque(maxlen=self.buffer_size)

        self._subscribers[serial].add(websocket)
        logger.info(f"Client subscribed to logs for {serial}")

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
            logger.info(f"Client unsubscribed from logs for {serial}")
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
                    raw_msg = f"Heartbeat telemetry tick #{seq}"
                    entry = {
                        "timestamp": "12:00:00.000",
                        "pid": 1234,
                        "tid": 1234,
                        "level": "I",
                        "tag": "KelvraDeviceLab",
                        "message": sanitize_log_message(raw_msg),
                        "raw": f"12:00:00.000  1234  1234 I KelvraDeviceLab: {raw_msg}"
                    }
                    await self._broadcast(serial, entry)
                    await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                pass
            return

        cmd = [self.device_manager.adb_path, "-s", serial, "logcat", "-v", "time"]
        proc = None
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
                    clean_msg = sanitize_log_message(match.group(5))
                    entry = {
                        "timestamp": match.group(1),
                        "level": match.group(2),
                        "tag": match.group(3).strip(),
                        "pid": int(match.group(4)),
                        "tid": 0,
                        "message": clean_msg,
                        "raw": sanitize_log_message(raw_line)
                    }
                else:
                    clean_msg = sanitize_log_message(raw_line)
                    entry = {
                        "timestamp": "",
                        "level": "I",
                        "tag": "SYSTEM",
                        "pid": 0,
                        "tid": 0,
                        "message": clean_msg,
                        "raw": clean_msg
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
        buf = self.get_or_create_buffer(serial)
        buf.append(entry)

        dead_clients = set()
        for ws in list(self._subscribers.get(serial, [])):
            try:
                await ws.send_json(entry)
            except Exception:
                dead_clients.add(ws)

        for dead in dead_clients:
            await self.disconnect(serial, dead)
