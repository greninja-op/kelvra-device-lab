"""
KELVRA Bench Integration Bridge for KELVRA Device Lab.
Coordinates fleet status with KELVRA Bench EventBus and paired devices registry.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from src.device_manager import DeviceInfo, DeviceManager

logger = logging.getLogger("kelvra.device_lab.bench_bridge")


class BenchEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "kelvra-device-lab"
    payload: Dict[str, Any]


class BenchBridge:
    """Bridges Device Lab operations with KELVRA Bench Control Room."""

    def __init__(self, device_manager: DeviceManager, bench_url: str = "http://127.0.0.1:8099"):
        self.device_manager = device_manager
        self.bench_url = os.environ.get("KELVRA_BENCH_URL", bench_url)
        self.sync_enabled = os.environ.get("KELVRA_BENCH_SYNC_ENABLED", "true").lower() in ("true", "1")
        self._published_events: List[BenchEvent] = []

    def check_pairing(self, serial: str) -> bool:
        """
        Safely check if a device is recognized in KELVRA Bench paired_devices.json (READ-ONLY).
        Does NOT modify the Bench file.
        """
        bench_paired_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "kelvra-bench", "data", "paired_devices.json"
        )
        if not os.path.exists(bench_paired_path):
            return False

        try:
            with open(bench_paired_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Check serial directly or in device records
                if serial in data and not data[serial].get("revoked", False):
                    return True
                for dev_id, record in data.items():
                    if record.get("device_id") == serial and not record.get("revoked", False):
                        return True
        except Exception as exc:
            logger.debug(f"Unable to read Bench paired_devices.json: {exc}")
        return False

    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> Optional[BenchEvent]:
        """Publish device event to KELVRA Bench EventBus."""
        event = BenchEvent(
            event_id=f"devlab-evt-{int(datetime.now(timezone.utc).timestamp()*1000)}",
            event_type=event_type,
            payload=payload
        )
        self._published_events.append(event)
        logger.info(f"Published Bench event: {event_type} [{event.event_id}]")

        if not self.sync_enabled:
            return event

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.post(
                    f"{self.bench_url}/api/events",
                    json=event.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                if res.status_code in (200, 201):
                    logger.debug(f"Bench accepted event {event.event_id}")
        except Exception as exc:
            # Bench might not be running in isolated dev; keep event logged locally
            logger.debug(f"Bench EventBus unreachable: {exc}")

        return event

    async def broadcast_device_connected(self, device: DeviceInfo):
        return await self.publish_event(
            "DEVICE_LAB_DEVICE_CONNECTED",
            {
                "serial": device.serial,
                "model": device.model,
                "manufacturer": device.manufacturer,
                "android_version": device.android_version,
                "battery_level": device.battery_level,
                "paired": self.check_pairing(device.serial)
            }
        )

    async def broadcast_device_disconnected(self, serial: str):
        return await self.publish_event(
            "DEVICE_LAB_DEVICE_DISCONNECTED",
            {"serial": serial}
        )

    async def broadcast_telemetry(self, telemetry_data: Dict[str, Any]):
        return await self.publish_event(
            "DEVICE_LAB_TELEMETRY_UPDATE",
            telemetry_data
        )
