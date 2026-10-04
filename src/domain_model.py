"""
Strongly typed Device Domain Model for KELVRA Device Lab.
Adheres strictly to the Device Provider Contract and Architecture Specifications.
Zero Emoji Prohibition Enforced.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator


class DevicePlatform(str, Enum):
    ANDROID_PHYSICAL = "android_physical"
    ANDROID_VIRTUAL = "android_virtual"
    APPLE_PHYSICAL = "apple_physical"
    APPLE_VIRTUAL = "apple_virtual"


class DeviceType(str, Enum):
    PHYSICAL = "physical"
    VIRTUAL = "virtual"


class ConnectionTransport(str, Enum):
    USB = "usb"
    WIFI = "wifi"
    EMULATOR_PIPE = "emulator_pipe"


class DeviceCapability(str, Enum):
    DISCOVERY = "discovery"
    SCREEN_STREAM_JPEG = "screen_stream_jpeg"
    SCREEN_STREAM_H264 = "screen_stream_h264"
    TOUCH_INTERACTION = "touch_interaction"
    KEYBOARD_INJECTION = "keyboard_injection"
    HARDWARE_BUTTONS = "hardware_buttons"
    LOGCAT_STREAMING = "logcat_streaming"
    TELEMETRY_POLLING = "telemetry_polling"
    SCREENSHOT_CAPTURE = "screenshot_capture"
    APP_LIFECYCLE = "app_lifecycle"
    TEST_AUTOMATION = "test_automation"
    VIRTUAL_LIFECYCLE = "virtual_lifecycle"


class DeviceLifecycleState(str, Enum):
    DISCOVERED = "discovered"
    UNAUTHORIZED = "unauthorized"
    AVAILABLE = "available"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class DeviceError(BaseModel):
    code: str
    message: str
    recovery_hint: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Device(BaseModel):
    """
    Core Domain Model representing an enrolled physical or virtual mobile device.
    Uses a stable composite identifier (e.g. 'android:8TCABAIFWOZTDICI') to avoid
    instability from display names or changing enumeration order.
    """
    id: str = Field(..., description="Stable unique identifier in format '<platform>:<serial>'")
    serial: str = Field(..., min_length=1, description="Underlying hardware serial or network address")
    provider_id: str = Field(..., description="ID of owning provider, e.g. 'android_adb'")
    platform: DevicePlatform
    device_type: DeviceType = DeviceType.PHYSICAL
    display_name: str
    manufacturer: Optional[str] = "Unknown"
    model: Optional[str] = "Unknown"
    os_name: str = "Android"
    os_version: Optional[str] = None
    sdk_level: Optional[int] = None
    abi: Optional[str] = None
    transport: ConnectionTransport = ConnectionTransport.USB
    state: DeviceLifecycleState = DeviceLifecycleState.DISCOVERED
    capabilities: List[DeviceCapability] = Field(default_factory=list)
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    connected_at: Optional[str] = None
    error: Optional[DeviceError] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not v or ":" not in v:
            raise ValueError("Device ID must be in format '<platform_prefix>:<serial>'")
        prefix, serial = v.split(":", 1)
        if not prefix.strip() or not serial.strip():
            raise ValueError("Device ID prefix and serial cannot be empty")
        return v.strip()

    @field_validator("serial")
    @classmethod
    def validate_serial(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("Device serial cannot be empty or whitespace only")
        return v_stripped

    def has_capability(self, capability: DeviceCapability) -> bool:
        return capability in self.capabilities

    def add_capability(self, capability: DeviceCapability) -> None:
        if capability not in self.capabilities:
            self.capabilities.append(capability)
