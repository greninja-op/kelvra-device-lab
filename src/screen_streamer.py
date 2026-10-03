"""
Screen Streamer for KELVRA Device Lab.
Provides real-time frame streaming over WebSockets.
"""

import asyncio
import base64
import logging
from typing import Dict, Set
from fastapi import WebSocket

from src.input_controller import InputController

logger = logging.getLogger("kelvra.device_lab.screen_streamer")


class ScreenStreamer:
    """Manages continuous screen streaming to connected WebSocket clients."""

    def __init__(self, input_controller: InputController, fps: int = 15):
        self.input_controller = input_controller
        self.target_fps = fps
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._streaming_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, serial: str, websocket: WebSocket):
        await websocket.accept()
        if serial not in self._active_connections:
            self._active_connections[serial] = set()
        self._active_connections[serial].add(websocket)
        logger.info(f"Client connected to screen stream for {serial} (total: {len(self._active_connections[serial])})")

        # Start streaming task if not already running
        if serial not in self._streaming_tasks or self._streaming_tasks[serial].done():
            self._streaming_tasks[serial] = asyncio.create_task(self._stream_loop(serial))

    async def disconnect(self, serial: str, websocket: WebSocket):
        if serial in self._active_connections:
            self._active_connections[serial].discard(websocket)
            logger.info(f"Client disconnected from screen stream for {serial}")
            if not self._active_connections[serial]:
                del self._active_connections[serial]
                # Stop streaming task
                if serial in self._streaming_tasks:
                    self._streaming_tasks[serial].cancel()
                    del self._streaming_tasks[serial]

    async def _stream_loop(self, serial: str):
        """Streaming loop capturing frames and broadcasting to clients."""
        interval = 1.0 / self.target_fps
        try:
            while serial in self._active_connections and self._active_connections[serial]:
                loop_start = asyncio.get_event_loop().time()
                
                # Run screenshot in thread pool to prevent blocking event loop
                frame_bytes = await asyncio.to_thread(
                    self.input_controller.take_screenshot,
                    serial,
                    max_width=720,
                    quality=65
                )

                if frame_bytes:
                    b64_frame = base64.b64encode(frame_bytes).decode("ascii")
                    msg = {"type": "frame", "serial": serial, "data": b64_frame}
                    
                    dead_clients = set()
                    for ws in list(self._active_connections.get(serial, [])):
                        try:
                            await ws.send_json(msg)
                        except Exception:
                            dead_clients.add(ws)

                    for dead in dead_clients:
                        await self.disconnect(serial, dead)

                elapsed = asyncio.get_event_loop().time() - loop_start
                sleep_time = max(0.01, interval - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info(f"Screen stream task cancelled for {serial}")
        except Exception as exc:
            logger.error(f"Error in stream loop for {serial}: {exc}")
