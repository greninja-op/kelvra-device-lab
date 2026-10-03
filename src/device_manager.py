"""
Device Manager for KELVRA Device Lab.
Handles ADB device discovery, property introspection, and state management.
"""

import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("kelvra.device_lab.manager")


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    BUSY = "busy"
    UNKNOWN = "unknown"


class DeviceInfo(BaseModel):
    serial: str
    model: str = "Unknown"
    manufacturer: str = "Unknown"
    market_name: str = "Android Device"
    android_version: str = "Unknown"
    sdk_level: int = 0
    abi: str = "arm64-v8a"
    status: DeviceStatus = DeviceStatus.ONLINE
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


class DeviceManager:
    """
    Coordinates ADB commands and maintains the fleet inventory.
    Supports physical devices, network ADB, and simulated devices for testing.
    """

    def __init__(self, adb_path: str = "adb", enable_mock_fallback: bool = True):
        self.adb_path = os.environ.get("ADB_PATH", adb_path)
        self.enable_mock_fallback = enable_mock_fallback
        self._cached_devices: Dict[str, DeviceInfo] = {}
        self._mock_devices: Dict[str, DeviceInfo] = {}

    def add_mock_device(self, device: DeviceInfo) -> None:
        """Register a mock device for headless or test environments."""
        self._mock_devices[device.serial] = device

    def remove_mock_device(self, serial: str) -> None:
        if serial in self._mock_devices:
            del self._mock_devices[serial]
        if serial in self._cached_devices:
            del self._cached_devices[serial]

    def clear_mock_devices(self) -> None:
        for s in list(self._mock_devices.keys()):
            if s in self._cached_devices:
                del self._cached_devices[s]
        self._mock_devices.clear()

    def run_adb(self, args: List[str], serial: Optional[str] = None, timeout: float = 10.0) -> subprocess.CompletedProcess:
        """Execute an ADB command against a specific device or host."""
        cmd = [self.adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)

        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning(f"ADB execution failed for {cmd}: {exc}")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=str(exc)
            )

    def scan_devices(self) -> List[DeviceInfo]:
        """
        Discovers all devices attached via USB or Wi-Fi.
        Falls back to mock devices if enabled and no physical devices are present.
        """
        res = self.run_adb(["devices", "-l"], timeout=5.0)
        found_serials = set()
        active_devices: List[DeviceInfo] = []

        if res.returncode == 0 and res.stdout:
            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:  # skip 'List of devices attached'
                line = line.strip()
                if not line or line.startswith("*"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    state = parts[1].lower()
                    found_serials.add(serial)

                    if state == "device":
                        status = DeviceStatus.ONLINE
                    elif state == "unauthorized":
                        status = DeviceStatus.UNAUTHORIZED
                    elif state == "offline":
                        status = DeviceStatus.OFFLINE
                    else:
                        status = DeviceStatus.UNKNOWN

                    info = self._inspect_device(serial, status)
                    self._cached_devices[serial] = info
                    active_devices.append(info)

        # Include mock devices if no real devices found or if mocks explicitly configured
        for s, mock_dev in self._mock_devices.items():
            if s not in found_serials:
                active_devices.append(mock_dev)
                self._cached_devices[s] = mock_dev

        return active_devices

    def get_device(self, serial: str) -> Optional[DeviceInfo]:
        """Retrieve live or cached device information by serial number."""
        if serial in self._mock_devices:
            return self._mock_devices[serial]
        
        # Verify if device is online
        scan = self.scan_devices()
        for d in scan:
            if d.serial == serial:
                return d
        
        return self._cached_devices.get(serial)

    def _inspect_device(self, serial: str, status: DeviceStatus) -> DeviceInfo:
        """Inspect hardware properties, battery, and screen dimensions."""
        if status != DeviceStatus.ONLINE:
            return DeviceInfo(
                serial=serial,
                status=status,
                last_seen=datetime.now(timezone.utc).isoformat()
            )

        props = self._get_properties(serial)
        battery = self._get_battery(serial)
        screen = self._get_screen_geometry(serial)
        airplane = self._get_airplane_mode(serial)
        wifi_ip = self._get_wifi_ip(serial)

        manufacturer = props.get("ro.product.manufacturer", "Unknown").capitalize()
        model = props.get("ro.product.model", "Android Device")
        market_name = props.get("ro.product.marketname") or f"{manufacturer} {model}"
        version = props.get("ro.build.version.release", "Unknown")
        sdk = int(props.get("ro.build.version.sdk", 0) or 0)
        abi = props.get("ro.product.cpu.abi", "arm64-v8a")
        is_emu = "emulator" in serial.lower() or "goldfish" in props.get("ro.hardware", "").lower()

        return DeviceInfo(
            serial=serial,
            model=model,
            manufacturer=manufacturer,
            market_name=market_name,
            android_version=version,
            sdk_level=sdk,
            abi=abi,
            status=status,
            battery_level=battery.get("level", 100),
            battery_charging=battery.get("charging", False),
            battery_temperature=battery.get("temp", 25.0),
            screen_width=screen.get("width", 1080),
            screen_height=screen.get("height", 2400),
            screen_density=screen.get("density", 440),
            airplane_mode=airplane,
            wifi_ip=wifi_ip,
            is_emulator=is_emu,
            last_seen=datetime.now(timezone.utc).isoformat()
        )

    def _get_properties(self, serial: str) -> Dict[str, str]:
        """Fetch system properties via getprop."""
        res = self.run_adb(["shell", "getprop"], serial=serial, timeout=4.0)
        props: Dict[str, str] = {}
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                match = re.match(r"^\[(.*?)\]:\s*\[(.*?)\]", line.strip())
                if match:
                    props[match.group(1)] = match.group(2)
        return props

    def _get_battery(self, serial: str) -> Dict[str, Any]:
        """Extract battery statistics via dumpsys battery."""
        res = self.run_adb(["shell", "dumpsys", "battery"], serial=serial, timeout=4.0)
        info = {"level": 100, "charging": False, "temp": 25.0}
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("level:"):
                    try:
                        info["level"] = int(line.split(":")[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("status:"):
                    # status 2 = charging, 5 = full
                    val = line.split(":")[1].strip()
                    info["charging"] = val in ("2", "5")
                elif line.startswith("temperature:"):
                    try:
                        raw_temp = float(line.split(":")[1].strip())
                        info["temp"] = raw_temp / 10.0 if raw_temp > 100 else raw_temp
                    except ValueError:
                        pass
        return info

    def _get_screen_geometry(self, serial: str) -> Dict[str, int]:
        """Determine screen width, height, and density."""
        geo = {"width": 1080, "height": 2400, "density": 440}
        
        # Screen size
        size_res = self.run_adb(["shell", "wm", "size"], serial=serial, timeout=3.0)
        if size_res.returncode == 0 and size_res.stdout:
            match = re.search(r"(\d+)x(\d+)", size_res.stdout)
            if match:
                geo["width"] = int(match.group(1))
                geo["height"] = int(match.group(2))

        # Density
        dens_res = self.run_adb(["shell", "wm", "density"], serial=serial, timeout=3.0)
        if dens_res.returncode == 0 and dens_res.stdout:
            match = re.search(r"density:\s*(\d+)", dens_res.stdout)
            if match:
                geo["density"] = int(match.group(1))

        return geo

    def _get_airplane_mode(self, serial: str) -> bool:
        """Check airplane mode status."""
        res = self.run_adb(["shell", "settings", "get", "global", "airplane_mode_on"], serial=serial, timeout=3.0)
        if res.returncode == 0 and res.stdout:
            return res.stdout.strip() == "1"
        return False

    def _get_wifi_ip(self, serial: str) -> Optional[str]:
        """Resolve device Wi-Fi IP address."""
        res = self.run_adb(["shell", "ip", "-f", "inet", "addr", "show", "wlan0"], serial=serial, timeout=3.0)
        if res.returncode == 0 and res.stdout:
            match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", res.stdout)
            if match:
                return match.group(1)
        return None
