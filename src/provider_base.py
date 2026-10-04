"""
Abstract Device Provider Interface for KELVRA Device Lab.
Adheres strictly to docs/DEVICE_PROVIDER_CONTRACT.md.
Zero Emoji Prohibition Enforced.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from src.domain_model import Device, DeviceCapability, DevicePlatform


class ProviderStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ProviderHealth(BaseModel):
    provider_id: str
    status: ProviderStatus
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)


class BaseDeviceProvider(ABC):
    """
    Abstract contract implemented by concrete device platform providers
    (e.g. Android ADB Provider, local AVD Provider, Mock Test Provider).
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier of the provider (e.g. 'android_adb')."""
        pass

    @property
    @abstractmethod
    def platform(self) -> DevicePlatform:
        """Platform target handled by this provider."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initializes the provider runtime and verifies platform tools availability.
        Returns True if provider is operational, False otherwise.
        """
        pass

    @abstractmethod
    def discover_devices(self) -> List[Device]:
        """
        Polls or queries attached devices.
        Returns an immutable snapshot list of newly discovered Device instances.
        Must execute safely without throwing unhandled exceptions.
        """
        pass

    @abstractmethod
    def get_capabilities(self, device_id: str) -> List[DeviceCapability]:
        """Returns the list of hardware capabilities supported for device_id."""
        pass

    @abstractmethod
    def connect(self, device_id: str) -> bool:
        """
        Establishes an active communication session with the device.
        Transitions state from AVAILABLE -> CONNECTING -> CONNECTED.
        """
        pass

    @abstractmethod
    def disconnect(self, device_id: str) -> bool:
        """
        Closes active communication session and releases allocated resources.
        Transitions state from CONNECTED -> DISCONNECTING -> AVAILABLE.
        """
        pass

    @abstractmethod
    def get_health(self) -> ProviderHealth:
        """Returns the live diagnostic health status of the provider."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleans up background threads, sockets, or spawned subprocesses."""
        pass
