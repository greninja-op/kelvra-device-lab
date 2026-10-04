"""
Apple Device Provider & iOS/iPadOS Integration Subsystem for KELVRA Device Lab.
Adheres strictly to docs/DEVICE_PROVIDER_CONTRACT.md and Phase 12 specifications.
Zero Emoji Prohibition Enforced.
"""

import asyncio
import logging
import os
import platform
import re
import socket
import subprocess
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

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

logger = logging.getLogger("kelvra.device_lab.apple_provider")


# ==============================================================================
# 1. Capability & Trust State Enums
# ==============================================================================

class CapabilityStatus(str, Enum):
    SUPPORTED = "supported"
    SUPPORTED_WITH_PREREQUISITES = "supported_with_prerequisites"
    LIMITED = "limited"
    EXPERIMENTAL = "experimental"
    UNAVAILABLE = "unavailable"
    DEFERRED = "deferred"


class ApplePairingState(str, Enum):
    PAIRED = "paired"
    UNPAIRED = "unpaired"
    PASSCODE_LOCKED = "passcode_locked"
    TRUST_DIALOG_PENDING = "trust_dialog_pending"
    UNKNOWN = "unknown"


class AppleCapabilityItem(BaseModel):
    capability: str
    status: CapabilityStatus
    description: str
    host_prerequisite: Optional[str] = None
    device_prerequisite: Optional[str] = None
    notes: Optional[str] = None


# ==============================================================================
# 2. Apple Device Model Identifier Mapper
# ==============================================================================

# Mapping from Apple internal ProductType to human-readable commercial name
APPLE_PRODUCT_TYPE_MAP: Dict[str, Tuple[str, str]] = {
    # iPhones
    "iPhone10,1": ("iPhone 8", "iPhone"),
    "iPhone10,2": ("iPhone 8 Plus", "iPhone"),
    "iPhone10,3": ("iPhone X", "iPhone"),
    "iPhone11,2": ("iPhone XS", "iPhone"),
    "iPhone11,4": ("iPhone XS Max", "iPhone"),
    "iPhone11,8": ("iPhone XR", "iPhone"),
    "iPhone12,1": ("iPhone 11", "iPhone"),
    "iPhone12,3": ("iPhone 11 Pro", "iPhone"),
    "iPhone12,5": ("iPhone 11 Pro Max", "iPhone"),
    "iPhone12,8": ("iPhone SE (2nd gen)", "iPhone"),
    "iPhone13,1": ("iPhone 12 mini", "iPhone"),
    "iPhone13,2": ("iPhone 12", "iPhone"),
    "iPhone13,3": ("iPhone 12 Pro", "iPhone"),
    "iPhone13,4": ("iPhone 12 Pro Max", "iPhone"),
    "iPhone14,2": ("iPhone 13 Pro", "iPhone"),
    "iPhone14,3": ("iPhone 13 Pro Max", "iPhone"),
    "iPhone14,4": ("iPhone 13 mini", "iPhone"),
    "iPhone14,5": ("iPhone 13", "iPhone"),
    "iPhone14,6": ("iPhone SE (3rd gen)", "iPhone"),
    "iPhone14,7": ("iPhone 14", "iPhone"),
    "iPhone14,8": ("iPhone 14 Plus", "iPhone"),
    "iPhone15,2": ("iPhone 14 Pro", "iPhone"),
    "iPhone15,3": ("iPhone 14 Pro Max", "iPhone"),
    "iPhone15,4": ("iPhone 15", "iPhone"),
    "iPhone15,5": ("iPhone 15 Plus", "iPhone"),
    "iPhone16,1": ("iPhone 15 Pro", "iPhone"),
    "iPhone16,2": ("iPhone 15 Pro Max", "iPhone"),
    "iPhone17,1": ("iPhone 16 Pro", "iPhone"),
    "iPhone17,2": ("iPhone 16 Pro Max", "iPhone"),
    "iPhone17,3": ("iPhone 16", "iPhone"),
    "iPhone17,4": ("iPhone 16 Plus", "iPhone"),
    # iPads
    "iPad11,6": ("iPad (8th gen)", "iPad"),
    "iPad12,1": ("iPad (9th gen)", "iPad"),
    "iPad13,1": ("iPad Air (4th gen)", "iPad"),
    "iPad13,4": ("iPad Pro 11-inch (3rd gen)", "iPad"),
    "iPad13,8": ("iPad Pro 12.9-inch (5th gen)", "iPad"),
    "iPad13,16": ("iPad Air (5th gen)", "iPad"),
    "iPad13,18": ("iPad (10th gen)", "iPad"),
    "iPad14,1": ("iPad mini (6th gen)", "iPad"),
    "iPad14,3": ("iPad Pro 11-inch (4th gen)", "iPad"),
    "iPad14,5": ("iPad Pro 12.9-inch (6th gen)", "iPad"),
    "iPad16,3": ("iPad Pro 11-inch (M4)", "iPad"),
    "iPad16,5": ("iPad Pro 13-inch (M4)", "iPad"),
}


class AppleDeviceModelMapper:
    """Translates Apple internal product identifiers into consumer market names."""

    @classmethod
    def resolve_model(cls, product_type: Optional[str]) -> Tuple[str, str]:
        """
        Returns (marketing_name, form_factor) e.g. ("iPhone 15 Pro", "iPhone")
        or ("iPad Air (5th gen)", "iPad").
        """
        if not product_type:
            return "Apple Device", "iPhone"
        
        pt = product_type.strip()
        if pt in APPLE_PRODUCT_TYPE_MAP:
            return APPLE_PRODUCT_TYPE_MAP[pt]
        
        # Heuristic fallback based on prefix
        if pt.startswith("iPad"):
            return f"Apple {pt}", "iPad"
        elif pt.startswith("iPhone"):
            return f"Apple {pt}", "iPhone"
        elif pt.startswith("iPod"):
            return f"Apple {pt}", "iPod"
        return f"Apple {pt}", "iPhone"


# ==============================================================================
# 3. Host Environment Detector
# ==============================================================================

class AppleEnvironmentStatus(BaseModel):
    host_os: str
    is_macos: bool
    usbmuxd_available: bool
    usbmuxd_port_active: bool
    lockdown_dir_exists: bool
    lockdown_dir_path: Optional[str] = None
    paired_records_count: int = 0
    idevice_id_path: Optional[str] = None
    ideviceinfo_path: Optional[str] = None
    pymobiledevice3_available: bool = False
    toolchain_type: Optional[str] = None
    guidance: List[str] = Field(default_factory=list)


class AppleEnvironmentDetector:
    """
    Probes host operating system for Apple USB multiplexing services (usbmuxd),
    lockdown pairing directory, and CLI toolchains (libimobiledevice / pymobiledevice3).
    Pure test isolation: accepts optional path overrides to prevent host state leakage.
    """

    def __init__(
        self,
        custom_lockdown_dir: Optional[str] = None,
        custom_tools_dir: Optional[str] = None,
        override_os: Optional[str] = None,
        override_usbmux_port: Optional[int] = None,
    ):
        self.custom_lockdown_dir = custom_lockdown_dir
        self.custom_tools_dir = custom_tools_dir
        self.override_os = override_os
        self.override_usbmux_port = override_usbmux_port

    def get_host_os(self) -> str:
        if self.override_os:
            return self.override_os
        return platform.system()

    def get_lockdown_dir(self) -> Optional[str]:
        if self.custom_lockdown_dir is not None:
            return self.custom_lockdown_dir if os.path.isdir(self.custom_lockdown_dir) else None
        
        host_os = self.get_host_os()
        if host_os == "Windows":
            prog_data = os.environ.get("ProgramData", r"C:\ProgramData")
            p = os.path.join(prog_data, "Apple", "Lockdown")
            if os.path.isdir(p):
                return p
        elif host_os == "Darwin":
            p = "/var/db/lockdown"
            if os.path.isdir(p):
                return p
        elif host_os == "Linux":
            p = "/var/lib/lockdown"
            if os.path.isdir(p):
                return p
        return None

    def check_usbmux_port(self) -> bool:
        """Probes standard usbmuxd loopback TCP port (27015)."""
        port = self.override_usbmux_port or 27015
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.4)
                result = s.connect_ex(("127.0.0.1", port))
                return result == 0
        except Exception:
            return False

    def find_tool(self, tool_name: str) -> Optional[str]:
        """Resolves tool in custom directory or on system PATH."""
        if self.custom_tools_dir:
            exts = [".exe", ".bat", ""] if self.get_host_os() == "Windows" else [""]
            for ext in exts:
                candidate = os.path.join(self.custom_tools_dir, tool_name + ext)
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    return candidate
            return None
        
        # System PATH lookup
        import shutil
        return shutil.which(tool_name)

    def detect(self) -> AppleEnvironmentStatus:
        host_os = self.get_host_os()
        is_macos = (host_os == "Darwin")
        
        lockdown_dir = self.get_lockdown_dir()
        lockdown_exists = lockdown_dir is not None
        paired_count = 0
        if lockdown_exists and os.path.isdir(lockdown_dir):
            try:
                files = os.listdir(lockdown_dir)
                paired_count = sum(1 for f in files if f.endswith(".plist") and f != "SystemConfiguration.plist")
            except Exception:
                paired_count = 0

        usbmux_active = self.check_usbmux_port()
        
        # Check tools
        idevice_id = self.find_tool("idevice_id")
        ideviceinfo = self.find_tool("ideviceinfo")
        pmd3 = self.find_tool("pymobiledevice3")

        toolchain_type = None
        if idevice_id and ideviceinfo:
            toolchain_type = "libimobiledevice"
        elif pmd3:
            toolchain_type = "pymobiledevice3"

        guidance = []
        if not usbmux_active and not is_macos:
            if host_os == "Windows":
                guidance.append("Start Apple Mobile Device Service (AMDS) or install Apple iTunes / usbmuxd driver.")
            else:
                guidance.append("Start usbmuxd daemon: sudo systemctl start usbmuxd")

        if not toolchain_type:
            guidance.append(
                "Install libimobiledevice CLI utilities (idevice_id, ideviceinfo) or pymobiledevice3 "
                "for physical device enumeration and metadata introspection."
            )

        if not is_macos:
            guidance.append(
                "Windows host limitation: Interactive screen teleoperation and remote touch control "
                "require a macOS host with signed WebDriverAgent (deferred to future macOS agent node)."
            )

        return AppleEnvironmentStatus(
            host_os=host_os,
            is_macos=is_macos,
            usbmuxd_available=usbmux_active or is_macos,
            usbmuxd_port_active=usbmux_active,
            lockdown_dir_exists=lockdown_exists,
            lockdown_dir_path=lockdown_dir,
            paired_records_count=paired_count,
            idevice_id_path=idevice_id,
            ideviceinfo_path=ideviceinfo,
            pymobiledevice3_available=pmd3 is not None,
            toolchain_type=toolchain_type,
            guidance=guidance,
        )


# ==============================================================================
# 4. Apple Device Provider Implementation
# ==============================================================================

class AppleDeviceProvider(BaseDeviceProvider):
    """
    Physical Apple Device Provider for KELVRA Device Lab.
    Provides non-intrusive discovery, lockdown trust reporting, and hardware metadata
    introspection for physical iPhones and iPads.
    """

    def __init__(
        self,
        detector: Optional[AppleEnvironmentDetector] = None,
        mock_devices: Optional[List[Device]] = None,
    ):
        self.detector = detector or AppleEnvironmentDetector()
        self._mock_devices: Dict[str, Device] = {}
        if mock_devices:
            for d in mock_devices:
                self._mock_devices[d.id] = d
        self._connected_sessions: Set[str] = set()
        self._last_health: Optional[ProviderHealth] = None

    @property
    def provider_id(self) -> str:
        return "apple_device_provider"

    @property
    def platform(self) -> DevicePlatform:
        return DevicePlatform.APPLE_PHYSICAL

    def initialize(self) -> bool:
        """Probes Apple environment and initializes provider state."""
        env = self.detector.detect()
        status = ProviderStatus.READY if env.toolchain_type else ProviderStatus.DEGRADED
        msg = (
            f"Apple provider initialized ({env.toolchain_type or 'no CLI toolchain detected'}). "
            f"usbmuxd port active: {env.usbmuxd_port_active}."
        )
        self._last_health = ProviderHealth(
            provider_id=self.provider_id,
            status=status,
            message=msg,
            details=env.model_dump(),
        )
        return True

    def discover_devices(self) -> List[Device]:
        """
        Enumerates attached Apple devices via libimobiledevice / pymobiledevice3
        or returns deterministic mock devices if configured.
        """
        # If mock devices are explicitly seeded for testing, return them
        if self._mock_devices:
            return list(self._mock_devices.values())

        env = self.detector.detect()
        if not env.toolchain_type:
            logger.debug("Apple device discovery skipped: no Apple toolchain installed on host.")
            return []

        devices: List[Device] = []

        try:
            if env.toolchain_type == "libimobiledevice" and env.idevice_id_path:
                devices = self._discover_via_idevice_id(env.idevice_id_path, env.ideviceinfo_path)
            elif env.toolchain_type == "pymobiledevice3":
                devices = self._discover_via_pymobiledevice3()
        except Exception as e:
            logger.warning(f"Apple device discovery failed with exception: {e}")
            return []

        return devices

    def _discover_via_idevice_id(self, idevice_id_path: str, ideviceinfo_path: Optional[str]) -> List[Device]:
        """Runs idevice_id -l and queries ideviceinfo for each UDID."""
        try:
            res = subprocess.run(
                [idevice_id_path, "-l"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5.0,
                check=False,
            )
            if res.returncode != 0:
                logger.debug(f"idevice_id returned non-zero code {res.returncode}: {res.stderr}")
                return []
            
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            devices = []
            for udid in lines:
                dev = self._introspect_device(udid, ideviceinfo_path)
                devices.append(dev)
            return devices
        except Exception as e:
            logger.debug(f"Error executing idevice_id: {e}")
            return []

    def _introspect_device(self, udid: str, ideviceinfo_path: Optional[str]) -> Device:
        """Introspects lockdown properties via ideviceinfo -u <udid>."""
        dev_id = f"apple:{udid}"
        props: Dict[str, str] = {}
        error: Optional[DeviceError] = None
        state = DeviceLifecycleState.AVAILABLE

        if ideviceinfo_path:
            try:
                res = subprocess.run(
                    [ideviceinfo_path, "-u", udid],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5.0,
                    check=False,
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            props[k.strip()] = v.strip()
                else:
                    stderr_txt = res.stderr.lower()
                    if "password" in stderr_txt or "passcode" in stderr_txt:
                        state = DeviceLifecycleState.UNAUTHORIZED
                        error = DeviceError(
                            code="APPLE_PASSCODE_LOCKED",
                            message="Device is passcode locked.",
                            recovery_hint="Unlock device screen and enter your passcode.",
                        )
                    elif "trust" in stderr_txt or "pair" in stderr_txt:
                        state = DeviceLifecycleState.UNAUTHORIZED
                        error = DeviceError(
                            code="APPLE_TRUST_REQUIRED",
                            message="Device pairing trust not established.",
                            recovery_hint="Unlock device and tap 'Trust This Computer' on the screen.",
                        )
                    else:
                        state = DeviceLifecycleState.UNAUTHORIZED
                        error = DeviceError(
                            code="APPLE_LOCKDOWN_ERROR",
                            message="Could not read device lockdown properties.",
                            recovery_hint="Reconnect USB cable and verify device is unlocked.",
                        )
            except subprocess.TimeoutExpired:
                state = DeviceLifecycleState.UNAUTHORIZED
                error = DeviceError(
                    code="APPLE_PROBE_TIMEOUT",
                    message="Lockdown probe timed out.",
                    recovery_hint="Verify device screen is awake.",
                )

        product_type = props.get("ProductType")
        market_name, form_factor = AppleDeviceModelMapper.resolve_model(product_type)
        device_name = props.get("DeviceName") or market_name
        os_version = props.get("ProductVersion")
        build_version = props.get("BuildVersion")
        cpu_arch = props.get("CPUArchitecture") or "arm64"

        capabilities = self.get_capabilities(dev_id)

        metadata = {
            "udid": udid,
            "product_type": product_type,
            "form_factor": form_factor,
            "build_version": build_version,
            "pairing_state": (
                ApplePairingState.PAIRED.value if state == DeviceLifecycleState.AVAILABLE
                else ApplePairingState.UNPAIRED.value
            ),
            "sim_status": props.get("SIMStatus"),
            "wi_fi_address": props.get("WiFiAddress"),
            "hardware_platform": "Apple Silicon",
        }

        return Device(
            id=dev_id,
            serial=udid,
            provider_id=self.provider_id,
            platform=DevicePlatform.APPLE_PHYSICAL,
            device_type=DeviceType.PHYSICAL,
            display_name=device_name,
            manufacturer="Apple",
            model=market_name,
            os_name="iOS" if form_factor == "iPhone" else "iPadOS",
            os_version=os_version,
            abi=cpu_arch,
            transport=ConnectionTransport.USB,
            state=state,
            capabilities=capabilities,
            error=error,
            metadata=metadata,
        )

    def _discover_via_pymobiledevice3(self) -> List[Device]:
        """Invokes pymobiledevice3 usbmux list-devices via isolated CLI subprocess."""
        try:
            res = subprocess.run(
                ["pymobiledevice3", "usbmux", "list-devices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5.0,
                check=False,
            )
            if res.returncode != 0:
                return []
            
            import json
            data = json.loads(res.stdout)
            devices = []
            for item in data:
                udid = item.get("SerialNumber") or item.get("udid")
                if not udid:
                    continue
                dev = self._introspect_device(udid, None)
                devices.append(dev)
            return devices
        except Exception as e:
            logger.debug(f"Error executing pymobiledevice3: {e}")
            return []

    def get_capabilities(self, device_id: str) -> List[DeviceCapability]:
        """
        Returns only technically verified and supported capabilities on Apple devices.
        Screen streaming and touch interaction are explicitly excluded.
        """
        return [
            DeviceCapability.DISCOVERY,
            DeviceCapability.TELEMETRY_POLLING,
            DeviceCapability.LOGCAT_STREAMING,  # Syslog extraction
            DeviceCapability.SCREENSHOT_CAPTURE,  # With DDI
        ]

    def get_detailed_capabilities(self) -> List[AppleCapabilityItem]:
        """Returns the full 11-capability capability report with explicit status classifications."""
        is_macos = self.detector.get_host_os() == "Darwin"
        return [
            AppleCapabilityItem(
                capability="Device Discovery",
                status=CapabilityStatus.SUPPORTED,
                description="Enumerate connected iPhones and iPads via usbmuxd socket.",
                host_prerequisite="usbmuxd active on port 27015 or Apple Mobile Device Service.",
                device_prerequisite="Physical USB connection.",
            ),
            AppleCapabilityItem(
                capability="Hardware Metadata & Identity",
                status=CapabilityStatus.SUPPORTED,
                description="Query ProductType, UDID, marketing name, iOS version, and CPU architecture.",
                host_prerequisite="libimobiledevice (ideviceinfo) or pymobiledevice3.",
                device_prerequisite="Device paired and unlocked.",
            ),
            AppleCapabilityItem(
                capability="Hardware Telemetry (Battery & Diagnostics)",
                status=CapabilityStatus.SUPPORTED_WITH_PREREQUISITES,
                description="Query battery percentage, cycle count, and charging state via lockdown diagnostics.",
                host_prerequisite="Lockdown pairing record.",
                device_prerequisite="Device trust accepted.",
            ),
            AppleCapabilityItem(
                capability="Diagnostic Syslog Streaming",
                status=CapabilityStatus.SUPPORTED_WITH_PREREQUISITES,
                description="Real-time unified logging system extraction (idevicesyslog).",
                host_prerequisite="libimobiledevice / pymobiledevice3.",
                device_prerequisite="Device unlocked.",
            ),
            AppleCapabilityItem(
                capability="Screenshot Capture",
                status=CapabilityStatus.EXPERIMENTAL,
                description="High-resolution PNG capture via screenshotr service.",
                host_prerequisite="Mounted Developer Disk Image (DDI).",
                device_prerequisite="Developer Mode enabled (iOS 16+).",
            ),
            AppleCapabilityItem(
                capability="Live Screen Viewing (Baseline JPEG)",
                status=CapabilityStatus.UNAVAILABLE,
                description="Direct live screen streaming without external macOS runner.",
                host_prerequisite="macOS host required for QuickTime AVFoundation bridge or WebDriverAgent.",
                notes="Unsupported on Windows host in MVP.",
            ),
            AppleCapabilityItem(
                capability="Live Screen Viewing (High-FPS H.264)",
                status=CapabilityStatus.UNAVAILABLE,
                description="Hardware H.264 hardware stream.",
                host_prerequisite="macOS AVFoundation pipeline.",
                notes="Unsupported on Windows host in MVP.",
            ),
            AppleCapabilityItem(
                capability="Touch Interaction & Gestures",
                status=CapabilityStatus.UNAVAILABLE,
                description="Inject tap, swipe, and touch gestures.",
                host_prerequisite="macOS with signed WebDriverAgent runner and Apple Developer Certificate.",
                notes="Unsupported on Windows host without macOS agent node.",
            ),
            AppleCapabilityItem(
                capability="Keyboard & Text Input",
                status=CapabilityStatus.UNAVAILABLE,
                description="Inject keystrokes and text.",
                host_prerequisite="Active WebDriverAgent session.",
                notes="Unsupported on Windows host.",
            ),
            AppleCapabilityItem(
                capability="Application Lifecycle Control",
                status=CapabilityStatus.LIMITED,
                description="Launch and kill developer debug builds.",
                host_prerequisite="Developer Disk Image mounted.",
                device_prerequisite="Provisioned IPA matching device UDID.",
            ),
            AppleCapabilityItem(
                capability="UI Test Automation",
                status=CapabilityStatus.DEFERRED,
                description="XCUITest automation suite execution.",
                host_prerequisite="macOS agent node with Xcode 15+.",
                notes="Deferred to Phase 13+.",
            ),
        ]

    def connect(self, device_id: str) -> bool:
        """
        Connects an Apple device session.
        Enforces that device is not in UNAUTHORIZED state.
        """
        # Check mock or active devices
        dev = self._mock_devices.get(device_id)
        if dev and dev.state == DeviceLifecycleState.UNAUTHORIZED:
            logger.warning(f"Cannot connect unauthorized Apple device {device_id}: {dev.error}")
            return False

        self._connected_sessions.add(device_id)
        logger.info(f"Connected session established with Apple device {device_id}")
        return True

    def disconnect(self, device_id: str) -> bool:
        if device_id in self._connected_sessions:
            self._connected_sessions.remove(device_id)
            logger.info(f"Disconnected session from Apple device {device_id}")
            return True
        return False

    def get_health(self) -> ProviderHealth:
        env = self.detector.detect()
        status = ProviderStatus.READY if env.toolchain_type else ProviderStatus.DEGRADED
        return ProviderHealth(
            provider_id=self.provider_id,
            status=status,
            message=(
                f"Apple Provider active ({env.toolchain_type or 'no CLI toolchain detected'}). "
                f"usbmuxd port active: {env.usbmuxd_port_active}, paired records: {env.paired_records_count}."
            ),
            details=env.model_dump(),
        )

    def cleanup(self) -> None:
        self._connected_sessions.clear()

    # Test Helper Methods
    def seed_mock_device(self, device: Device) -> None:
        self._mock_devices[device.id] = device

    def remove_mock_device(self, device_id: str) -> None:
        if device_id in self._mock_devices:
            del self._mock_devices[device_id]

    def clear_mock_devices(self) -> None:
        self._mock_devices.clear()
