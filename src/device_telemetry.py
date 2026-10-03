"""
Device Telemetry Collector for KELVRA Device Lab.
Collects live system performance, CPU, memory, storage, and thermal metrics.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from src.device_manager import DeviceManager

logger = logging.getLogger("kelvra.device_lab.telemetry")


class DeviceTelemetry(BaseModel):
    serial: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cpu_usage_percent: float = 0.0
    ram_used_mb: int = 0
    ram_total_mb: int = 0
    storage_used_gb: float = 0.0
    storage_total_gb: float = 0.0
    battery_level: int = 100
    battery_temp_c: float = 25.0
    battery_charging: bool = False
    thermal_status: str = "NORMAL"


class TelemetryCollector:
    """Collects real-time metrics from target Android devices."""

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager

    def collect(self, serial: str) -> DeviceTelemetry:
        """Fetch current hardware telemetry snapshot."""
        # Check if mock device
        if serial in self.device_manager._mock_devices:
            mock_dev = self.device_manager._mock_devices[serial]
            return DeviceTelemetry(
                serial=serial,
                cpu_usage_percent=14.2,
                ram_used_mb=3420,
                ram_total_mb=8192,
                storage_used_gb=48.5,
                storage_total_gb=256.0,
                battery_level=mock_dev.battery_level,
                battery_temp_c=mock_dev.battery_temperature,
                battery_charging=mock_dev.battery_charging,
                thermal_status="NORMAL"
            )

        cpu = self._get_cpu_usage(serial)
        ram = self._get_ram_info(serial)
        storage = self._get_storage_info(serial)
        battery = self.device_manager._get_battery(serial)

        temp = battery.get("temp", 25.0)
        thermal_status = "NORMAL"
        if temp >= 45.0:
            thermal_status = "CRITICAL"
        elif temp >= 38.0:
            thermal_status = "WARM"

        return DeviceTelemetry(
            serial=serial,
            cpu_usage_percent=cpu,
            ram_used_mb=ram.get("used_mb", 0),
            ram_total_mb=ram.get("total_mb", 0),
            storage_used_gb=storage.get("used_gb", 0.0),
            storage_total_gb=storage.get("total_gb", 0.0),
            battery_level=battery.get("level", 100),
            battery_temp_c=temp,
            battery_charging=battery.get("charging", False),
            thermal_status=thermal_status
        )

    def _get_cpu_usage(self, serial: str) -> float:
        """Estimate CPU utilization via top -n 1."""
        res = self.device_manager.run_adb(["shell", "top", "-n", "1", "-b"], serial=serial, timeout=3.0)
        if res.returncode == 0 and res.stdout:
            # Look for line: 400%cpu 22%user 0%nice 35%sys 343%idle
            match = re.search(r"(\d+)%idle", res.stdout)
            if match:
                idle = float(match.group(1))
                return max(0.0, min(100.0, 100.0 - (idle / 4.0 if idle > 100 else idle)))
        return 8.5

    def _get_ram_info(self, serial: str) -> dict:
        """Parse dumpsys meminfo."""
        res = self.device_manager.run_adb(["shell", "dumpsys", "meminfo"], serial=serial, timeout=4.0)
        data = {"used_mb": 0, "total_mb": 0}
        if res.returncode == 0 and res.stdout:
            total_match = re.search(r"Total RAM:\s*([\d,]+)\s*K", res.stdout)
            free_match = re.search(r"Free RAM:\s*([\d,]+)\s*K", res.stdout)
            if total_match:
                total_k = int(total_match.group(1).replace(",", ""))
                total_mb = total_k // 1024
                data["total_mb"] = total_mb
                if free_match:
                    free_k = int(free_match.group(1).replace(",", ""))
                    free_mb = free_k // 1024
                    data["used_mb"] = max(0, total_mb - free_mb)
        return data

    def _get_storage_info(self, serial: str) -> dict:
        """Parse df /data."""
        res = self.device_manager.run_adb(["shell", "df", "/data"], serial=serial, timeout=3.0)
        data = {"used_gb": 0.0, "total_gb": 0.0}
        if res.returncode == 0 and res.stdout:
            lines = res.stdout.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    try:
                        # Sizes in 1K blocks
                        total_k = float(parts[1])
                        used_k = float(parts[2])
                        data["total_gb"] = round(total_k / (1024 * 1024), 1)
                        data["used_gb"] = round(used_k / (1024 * 1024), 1)
                    except ValueError:
                        pass
        return data
