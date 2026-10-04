"""
Android Physical & Virtual Device Provider for KELVRA Device Lab.
Provides safe, read-only hardware discovery, property introspection,
ADB runtime management, and connection lifecycle tracking over platform-tools.
Adheres strictly to docs/DEVICE_PROVIDER_CONTRACT.md and Zero Emoji Prohibition.
"""

import logging
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.provider_base import BaseDeviceProvider, ProviderHealth, ProviderStatus

logger = logging.getLogger("kelvra.device_lab.android_provider")


class CommandResult:
    """Encapsulates execution result of a bounded subprocess execution."""
    def __init__(self, returncode: int, stdout: str, stderr: str, timed_out: bool = False, duration_ms: float = 0.0):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.duration_ms = duration_ms

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class AndroidDeviceProvider(BaseDeviceProvider):
    """
    Production-grade Android Device Provider utilizing local Android Debug Bridge (ADB).
    Enforces safe subprocess execution (shell=False), timeouts, output bounding,
    read-only property caching, and structured unauthorized error handling.
    """

    def __init__(self, adb_path: Optional[str] = None):
        self._custom_adb_path = adb_path
        self._resolved_adb: Optional[str] = None
        self._adb_version: Optional[str] = None
        self._initialized = False
        self._property_cache: Dict[str, Dict[str, Any]] = {}
        self._active_connections: Set[str] = set()
        self._discovery_lock = threading.Lock()

    @property
    def provider_id(self) -> str:
        return "android_adb"

    @property
    def platform(self) -> DevicePlatform:
        return DevicePlatform.ANDROID_PHYSICAL

    def _resolve_adb_executable(self) -> Optional[str]:
        """
        Locates the adb executable deterministically in the following priority:
        1. Explicitly configured path in constructor or settings.
        2. ADB_PATH environment variable.
        3. System PATH lookup via shutil.which.
        4. Standard Windows Android SDK path (%LOCALAPPDATA%/Android/Sdk/platform-tools/adb.exe).
        5. Standard Unix Android SDK path (~/Android/Sdk/platform-tools/adb).
        """
        if self._custom_adb_path and os.path.isfile(self._custom_adb_path):
            return self._custom_adb_path

        env_adb = os.environ.get("ADB_PATH")
        if env_adb and os.path.isfile(env_adb):
            return env_adb

        which_adb = shutil.which("adb")
        if which_adb:
            return which_adb

        # Standard Windows Android SDK location
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidate = os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe")
            if os.path.isfile(candidate):
                return candidate

        # Standard Unix Android SDK location
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
        if home:
            unix_candidate = os.path.join(home, "Android", "Sdk", "platform-tools", "adb")
            if os.path.isfile(unix_candidate):
                return unix_candidate

        return None

    def initialize(self) -> bool:
        """
        Initializes the provider runtime and verifies platform tools availability.
        Executes 'adb version' probe without shell expansion.
        """
        self._resolved_adb = self._resolve_adb_executable()
        if not self._resolved_adb:
            logger.warning("Android platform-tools 'adb' executable not found on host system.")
            self._initialized = False
            return False

        res = self._run_adb_cmd(["version"], timeout=3.0)
        is_success = getattr(res, "success", getattr(res, "returncode", -1) == 0)
        if is_success:
            self._initialized = True
            # Parse version string (e.g. "Android Debug Bridge version 1.0.41")
            first_line = res.stdout.strip().splitlines()[0] if res.stdout else "ADB Operational"
            self._adb_version = first_line
            logger.info(f"AndroidDeviceProvider initialized successfully: {self._adb_version} at {self._resolved_adb}")
        else:
            self._initialized = False
            logger.warning(f"ADB version probe failed with return code {res.returncode}: {res.stderr}")

        return self._initialized

    def configure_adb_path(self, custom_path: str) -> Tuple[bool, str]:
        """
        Configures and validates a user-provided custom ADB executable path.
        Returns (success, message).
        """
        stripped_path = custom_path.strip()
        if not os.path.isfile(stripped_path):
            return False, f"File does not exist: {stripped_path}"

        self._custom_adb_path = stripped_path
        ok = self.initialize()
        if ok:
            return True, f"ADB validated successfully: {self._adb_version}"
        return False, "Executable found but failed 'adb version' validation probe."

    def _run_adb_cmd(
        self,
        args: List[str],
        timeout: float = 5.0,
        max_bytes: int = 65536
    ) -> CommandResult:
        """
        Executes an ADB command safely using subprocess.Popen.
        Guarantees shell=False, bounded output reading, and process cleanup on timeout.
        """
        if not self._resolved_adb:
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr="ADB executable not resolved",
                timed_out=False
            )

        cmd = [self._resolved_adb] + args
        start_time = time.time()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout)
                duration_ms = (time.time() - start_time) * 1000.0

                stdout_str = stdout_bytes[:max_bytes].decode("utf-8", errors="replace")
                stderr_str = stderr_bytes[:max_bytes].decode("utf-8", errors="replace")
                return CommandResult(
                    returncode=proc.returncode,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    timed_out=False,
                    duration_ms=duration_ms
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                duration_ms = (time.time() - start_time) * 1000.0
                logger.warning(f"ADB command '{' '.join(args[:2])}' timed out after {timeout}s")
                return CommandResult(
                    returncode=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    timed_out=True,
                    duration_ms=duration_ms
                )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            duration_ms = (time.time() - start_time) * 1000.0
            logger.warning(f"Failed to execute ADB command: {exc}")
            return CommandResult(
                returncode=-1,
                stdout="",
                stderr=f"Execution error: {str(exc)}",
                timed_out=False,
                duration_ms=duration_ms
            )

    @staticmethod
    def _is_cmd_ok(res: Any) -> bool:
        if not res:
            return False
        if hasattr(res, "timed_out") and res.timed_out:
            return False
        return getattr(res, "returncode", -1) == 0

    def _get_device_prop(self, serial: str, prop_name: str) -> Optional[str]:
        """Reads a single Android system property safely via 'getprop'."""
        res = self._run_adb_cmd(["-s", serial, "shell", "getprop", prop_name], timeout=3.0)
        if self._is_cmd_ok(res) and res.stdout:
            val = res.stdout.strip()
            return val if val else None
        return None

    def _get_display_resolution(self, serial: str) -> Tuple[int, int]:
        """Reads physical display dimensions via 'wm size'."""
        res = self._run_adb_cmd(["-s", serial, "shell", "wm", "size"], timeout=3.0)
        if self._is_cmd_ok(res) and res.stdout:
            m = re.search(r"(\d{3,5})x(\d{3,5})", res.stdout)
            if m:
                try:
                    return int(m.group(1)), int(m.group(2))
                except ValueError:
                    pass
        return 1080, 2400

    def _get_display_density(self, serial: str) -> int:
        """Reads physical display pixel density via 'wm density'."""
        res = self._run_adb_cmd(["-s", serial, "shell", "wm", "density"], timeout=3.0)
        if self._is_cmd_ok(res) and res.stdout:
            m = re.search(r"(\d{2,4})", res.stdout)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass
        return 440

    def _introspect_device(self, serial: str) -> Dict[str, Any]:
        """
        Gathers safe hardware metadata for an authorized device.
        Results are cached per hardware serial to avoid repeated subshell overhead.
        """
        if serial in self._property_cache:
            return self._property_cache[serial]

        mfr = self._get_device_prop(serial, "ro.product.manufacturer") or "Unknown"
        model = self._get_device_prop(serial, "ro.product.model") or "Android Device"
        os_ver = self._get_device_prop(serial, "ro.build.version.release") or "Unknown"
        sdk_str = self._get_device_prop(serial, "ro.build.version.sdk") or "0"
        abi = self._get_device_prop(serial, "ro.product.cpu.abi") or "arm64-v8a"

        try:
            sdk_level = int(sdk_str)
        except ValueError:
            sdk_level = 0

        width, height = self._get_display_resolution(serial)
        density = self._get_display_density(serial)

        props: Dict[str, Any] = {
            "manufacturer": mfr,
            "model": model,
            "os_version": os_ver,
            "sdk_level": sdk_level,
            "abi": abi,
            "screen_width": width,
            "screen_height": height,
            "screen_density": density,
        }
        self._property_cache[serial] = props
        return props

    def invalidate_cache(self, serial: Optional[str] = None) -> None:
        """Invalidates cached properties for a specific device or all devices."""
        if serial:
            self._property_cache.pop(serial, None)
        else:
            self._property_cache.clear()

    def discover_devices(self) -> List[Device]:
        """
        Polls attached devices via 'adb devices -l'.
        Safe against daemon crashes, malformed outputs, and timeouts.
        Re-entrancy guarded to prevent overlapping subprocess cascades.
        """
        with self._discovery_lock:
            if not self._initialized and not self.initialize():
                return []

            res = self._run_adb_cmd(["devices", "-l"], timeout=5.0)
            if not self._is_cmd_ok(res):
                logger.debug("ADB devices query failed or timed out.")
                return []

            discovered: List[Device] = []
            lines = res.stdout.strip().splitlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Ignore daemon startup notices and header line
                if line.startswith("*") or line.startswith("List of devices"):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                serial = parts[0]
                raw_status = parts[1].lower()

                # Determine transport and platform
                is_emulator = serial.startswith("emulator-")
                is_wifi = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$", serial))

                transport = ConnectionTransport.WIFI if is_wifi else (
                    ConnectionTransport.EMULATOR_PIPE if is_emulator else ConnectionTransport.USB
                )
                device_type = DeviceType.VIRTUAL if is_emulator else DeviceType.PHYSICAL
                platform = DevicePlatform.ANDROID_VIRTUAL if is_emulator else DevicePlatform.ANDROID_PHYSICAL
                device_id = f"android:{serial}"

                capabilities = [
                    DeviceCapability.DISCOVERY,
                    DeviceCapability.SCREEN_STREAM_JPEG,
                    DeviceCapability.SCREENSHOT_CAPTURE,
                    DeviceCapability.TELEMETRY_POLLING,
                    DeviceCapability.LOGCAT_STREAMING,
                    DeviceCapability.TOUCH_INTERACTION,
                    DeviceCapability.KEYBOARD_INJECTION,
                    DeviceCapability.HARDWARE_BUTTONS,
                ]

                if raw_status == "device":
                    props = self._introspect_device(serial)
                    is_active = device_id in self._active_connections
                    state = DeviceLifecycleState.CONNECTED if is_active else DeviceLifecycleState.AVAILABLE

                    device = Device(
                        id=device_id,
                        serial=serial,
                        provider_id=self.provider_id,
                        platform=platform,
                        device_type=device_type,
                        display_name=f"{props['manufacturer']} {props['model']}".strip(),
                        manufacturer=props["manufacturer"],
                        model=props["model"],
                        os_name="Android",
                        os_version=props["os_version"],
                        sdk_level=props["sdk_level"],
                        abi=props["abi"],
                        transport=transport,
                        state=state,
                        capabilities=capabilities,
                        metadata={
                            "screen_width": props.get("screen_width", 1080),
                            "screen_height": props.get("screen_height", 2400),
                            "screen_density": props.get("screen_density", 440)
                        },
                        error=None
                    )
                    discovered.append(device)

                elif raw_status == "unauthorized":
                    device = Device(
                        id=device_id,
                        serial=serial,
                        provider_id=self.provider_id,
                        platform=platform,
                        device_type=device_type,
                        display_name=f"Android Device ({serial})",
                        os_name="Android",
                        transport=transport,
                        state=DeviceLifecycleState.UNAUTHORIZED,
                        capabilities=[DeviceCapability.DISCOVERY],
                        error=DeviceError(
                            code="ADB_UNAUTHORIZED",
                            message="Device is attached but USB debugging authorization has not been granted.",
                            recovery_hint="Unlock the device and accept the 'Allow USB debugging' prompt."
                        )
                    )
                    discovered.append(device)

                elif raw_status == "offline":
                    device = Device(
                        id=device_id,
                        serial=serial,
                        provider_id=self.provider_id,
                        platform=platform,
                        device_type=device_type,
                        display_name=f"Android Device ({serial})",
                        os_name="Android",
                        transport=transport,
                        state=DeviceLifecycleState.UNAVAILABLE,
                        capabilities=[DeviceCapability.DISCOVERY],
                        error=DeviceError(
                            code="DEVICE_OFFLINE",
                            message="Device is recognized by ADB but currently offline.",
                            recovery_hint="Re-insert the USB cable or toggle USB debugging in developer options."
                        )
                    )
                    discovered.append(device)

                else:
                    # Traps recovery, sideload, bootloader, or unknown states
                    device = Device(
                        id=device_id,
                        serial=serial,
                        provider_id=self.provider_id,
                        platform=platform,
                        device_type=device_type,
                        display_name=f"Android Device ({serial})",
                        os_name="Android",
                        transport=transport,
                        state=DeviceLifecycleState.UNAVAILABLE,
                        capabilities=[DeviceCapability.DISCOVERY],
                        error=DeviceError(
                            code=f"ADB_STATE_{raw_status.upper()}",
                            message=f"Device is in non-operational state: '{raw_status}'.",
                            recovery_hint="Reboot device to standard Android system mode."
                        )
                    )
                    discovered.append(device)

            return discovered

    def get_capabilities(self, device_id: str) -> List[DeviceCapability]:
        return [
            DeviceCapability.DISCOVERY,
            DeviceCapability.SCREEN_STREAM_JPEG,
            DeviceCapability.SCREENSHOT_CAPTURE,
            DeviceCapability.TELEMETRY_POLLING,
            DeviceCapability.LOGCAT_STREAMING,
            DeviceCapability.TOUCH_INTERACTION,
            DeviceCapability.KEYBOARD_INJECTION,
            DeviceCapability.HARDWARE_BUTTONS,
        ]

    def connect(self, device_id: str) -> bool:
        """Tracks an active connection lease for device_id."""
        if not self._initialized:
            return False
        self._active_connections.add(device_id)
        return True

    def disconnect(self, device_id: str) -> bool:
        """Releases the connection lease for device_id."""
        if device_id in self._active_connections:
            self._active_connections.remove(device_id)
        return True

    def get_health(self) -> ProviderHealth:
        """Returns safe provider health and diagnostics."""
        if not self._resolved_adb:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNAVAILABLE,
                message="Android ADB platform-tools executable was not found on PATH or Android SDK root."
            )
        if not self._initialized:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.ERROR,
                message="ADB executable is present but failed version probe."
            )
        return ProviderHealth(
            provider_id=self.provider_id,
            status=ProviderStatus.READY,
            message="Android ADB platform-tools operational",
            details={
                "adb_path": self._resolved_adb,
                "adb_version": self._adb_version or "Unknown",
                "active_sessions": len(self._active_connections),
                "cached_devices": len(self._property_cache)
            }
        )

    # --- Safe Read-Only Device Operations (Phase 9) ---

    def get_device_properties(self, serial: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached or freshly introspected hardware properties for an authorized serial."""
        if not self._initialized:
            return None
        return self._introspect_device(serial)

    def get_display_info(self, serial: str) -> Dict[str, int]:
        """Retrieves display width, height, and density safely."""
        width, height = self._get_display_resolution(serial)
        density = self._get_display_density(serial)
        return {"width": width, "height": height, "density": density}

    def check_device_health(self, serial: str) -> Dict[str, Any]:
        """Checks responsiveness and boot status of an attached device."""
        res = self._run_adb_cmd(["-s", serial, "shell", "getprop", "sys.boot_completed"], timeout=2.0)
        is_ok = self._is_cmd_ok(res)
        boot_completed = (is_ok and res.stdout.strip() == "1")
        latency = round(getattr(res, "duration_ms", 0.0), 2)
        return {
            "serial": serial,
            "responsive": is_ok,
            "boot_completed": boot_completed,
            "latency_ms": latency
        }

    def cleanup(self) -> None:
        """Releases all active connections and clears property caches."""
        self._active_connections.clear()
        self._property_cache.clear()
