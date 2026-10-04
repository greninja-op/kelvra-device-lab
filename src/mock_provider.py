"""
Controlled Mock Device Provider for deterministic unit and integration testing.
Enables end-to-end verification without requiring physical USB hardware.
Zero Emoji Prohibition Enforced.
"""

from typing import Dict, List, Optional
from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.lifecycle import transition_device
from src.provider_base import BaseDeviceProvider, ProviderHealth, ProviderStatus


class MockDeviceProvider(BaseDeviceProvider):
    """
    Test-only device provider with programmatic device registration
    and deterministic connection simulations.
    """

    def __init__(self, provider_id: str = "mock_provider", healthy: bool = True):
        self._provider_id = provider_id
        self._healthy = healthy
        self._devices: Dict[str, Device] = {}
        self._capabilities: Dict[str, List[DeviceCapability]] = {}

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def platform(self) -> DevicePlatform:
        return DevicePlatform.ANDROID_PHYSICAL

    def initialize(self) -> bool:
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        self._healthy = healthy

    def add_device(self, device: Device, capabilities: Optional[List[DeviceCapability]] = None) -> None:
        self._devices[device.id] = device
        self._capabilities[device.id] = capabilities or [
            DeviceCapability.DISCOVERY,
            DeviceCapability.SCREENSHOT_CAPTURE,
            DeviceCapability.TELEMETRY_POLLING,
            DeviceCapability.LOGCAT_STREAMING
        ]

    def remove_device(self, device_id: str) -> None:
        if device_id in self._devices:
            del self._devices[device_id]
        if device_id in self._capabilities:
            del self._capabilities[device_id]

    def clear(self) -> None:
        self._devices.clear()
        self._capabilities.clear()

    def discover_devices(self) -> List[Device]:
        if not self._healthy:
            return []
        return list(self._devices.values())

    def get_capabilities(self, device_id: str) -> List[DeviceCapability]:
        return self._capabilities.get(device_id, [DeviceCapability.DISCOVERY])

    def connect(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        if not self._healthy:
            return False
        return True

    def disconnect(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        return True

    def get_health(self) -> ProviderHealth:
        if self._healthy:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.READY,
                message="Mock device provider operational"
            )
        return ProviderHealth(
            provider_id=self.provider_id,
            status=ProviderStatus.ERROR,
            message="Mock device provider simulated failure"
        )

    def cleanup(self) -> None:
        self.clear()
