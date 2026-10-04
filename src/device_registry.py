"""
Device Registry and Event Dispatcher for KELVRA Device Lab.
Maintains deduplicated collection of devices, manages provider discovery,
enforces lifecycle transitions, and emits state change events.
Zero Emoji Prohibition Enforced.
"""

import logging
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from src.domain_model import Device, DeviceError, DeviceLifecycleState, DevicePlatform
from src.lifecycle import transition_device
from src.provider_base import BaseDeviceProvider, ProviderHealth, ProviderStatus

logger = logging.getLogger("kelvra.device_lab.registry")


class DeviceEventType(str, Enum):
    DEVICE_DISCOVERED = "device_discovered"
    DEVICE_STATE_CHANGED = "device_state_changed"
    DEVICE_CONNECTED = "device_connected"
    DEVICE_DISCONNECTED = "device_disconnected"
    DEVICE_REMOVED = "device_removed"


class DeviceEvent(BaseModel):
    event_type: DeviceEventType
    device_id: str
    previous_state: Optional[DeviceLifecycleState] = None
    new_state: DeviceLifecycleState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, str] = Field(default_factory=dict)


class DeviceRegistry:
    """
    Central, thread-safe registry managing the fleet of physical and virtual devices.
    Coordinates device discovery across registered providers and notifies subscribers of state transitions.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._devices: Dict[str, Device] = {}
        self._providers: Dict[str, BaseDeviceProvider] = {}
        self._listeners: List[Callable[[DeviceEvent], None]] = []

    def register_provider(self, provider: BaseDeviceProvider) -> None:
        with self._lock:
            self._providers[provider.provider_id] = provider
            logger.info(f"Registered device provider: '{provider.provider_id}'")

    def register_device(self, device: Device) -> None:
        """Directly registers a device into registry cache."""
        with self._lock:
            self._devices[device.id] = device

    def reconcile(self) -> List[Device]:
        """Polls all providers and reconciles discovered devices."""
        return self.poll_all_providers()

    def unregister_provider(self, provider_id: str) -> None:
        with self._lock:
            if provider_id in self._providers:
                self._providers[provider_id].cleanup()
                del self._providers[provider_id]
                logger.info(f"Unregistered device provider: '{provider_id}'")

    def subscribe(self, callback: Callable[[DeviceEvent], None]) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[DeviceEvent], None]) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify(self, event: DeviceEvent) -> None:
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception as exc:
                logger.warning(f"Error in DeviceRegistry event subscriber: {exc}")

    def get_device(self, device_id: str) -> Optional[Device]:
        with self._lock:
            dev = self._devices.get(device_id)
            if dev:
                return dev.model_copy()
            # Also try matching by raw serial if caller passed serial without prefix
            for d in self._devices.values():
                if d.serial == device_id:
                    return d.model_copy()
            return None

    def list_devices(
        self,
        platform: Optional[DevicePlatform] = None,
        state: Optional[DeviceLifecycleState] = None
    ) -> List[Device]:
        with self._lock:
            results = list(self._devices.values())
            if platform:
                results = [d for d in results if d.platform == platform]
            if state:
                results = [d for d in results if d.state == state]
            return [d.model_copy() for d in results]

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            total = len(self._devices)
            online = sum(1 for d in self._devices.values() if d.state in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.CONNECTED, DeviceLifecycleState.BUSY))
            unauthorized = sum(1 for d in self._devices.values() if d.state == DeviceLifecycleState.UNAUTHORIZED)
            busy = sum(1 for d in self._devices.values() if d.state == DeviceLifecycleState.BUSY)
            connected = sum(1 for d in self._devices.values() if d.state == DeviceLifecycleState.CONNECTED)
            return {
                "total": total,
                "online": online,
                "connected": connected,
                "unauthorized": unauthorized,
                "busy": busy,
            }

    def reconcile_discovered_devices(self, provider_id: str, discovered_list: List[Device]) -> List[Device]:
        """
        Reconciles newly polled devices from a provider with existing records.
        Handles device arrivals, updates, and disappearances safely.
        """
        with self._lock:
            discovered_ids = {d.id for d in discovered_list}
            now_iso = datetime.now(timezone.utc).isoformat()

            # 1. Update or Insert discovered devices
            for dev in discovered_list:
                if dev.id not in self._devices:
                    # New device discovered
                    self._devices[dev.id] = dev
                    self._notify(DeviceEvent(
                        event_type=DeviceEventType.DEVICE_DISCOVERED,
                        device_id=dev.id,
                        new_state=dev.state,
                        details={"model": dev.model or "Unknown", "serial": dev.serial}
                    ))
                else:
                    existing = self._devices[dev.id]
                    old_state = existing.state
                    # Update hardware properties
                    existing.manufacturer = dev.manufacturer or existing.manufacturer
                    existing.model = dev.model or existing.model
                    existing.display_name = dev.display_name or existing.display_name
                    existing.os_version = dev.os_version or existing.os_version
                    existing.sdk_level = dev.sdk_level or existing.sdk_level
                    existing.abi = dev.abi or existing.abi
                    existing.capabilities = dev.capabilities
                    existing.last_seen = now_iso

                    # Reconcile state if remote state changed
                    if old_state != dev.state:
                        try:
                            transition_device(existing, dev.state, "Discovery update", dev.error)
                            self._notify(DeviceEvent(
                                event_type=DeviceEventType.DEVICE_STATE_CHANGED,
                                device_id=existing.id,
                                previous_state=old_state,
                                new_state=dev.state
                            ))
                        except Exception as exc:
                            logger.warning(f"Failed to reconcile state for '{existing.id}': {exc}")

            # 2. Check for disappeared devices owned by this provider
            for existing_id, existing_dev in list(self._devices.items()):
                if existing_dev.provider_id == provider_id and existing_id not in discovered_ids:
                    old_state = existing_dev.state
                    if old_state not in (DeviceLifecycleState.DISCONNECTED, DeviceLifecycleState.UNAVAILABLE):
                        try:
                            transition_device(
                                existing_dev,
                                DeviceLifecycleState.DISCONNECTED,
                                "Device disappeared from provider poll",
                                DeviceError(code="DEVICE_DISAPPEARED", message="Device was detached or disconnected")
                            )
                            self._notify(DeviceEvent(
                                event_type=DeviceEventType.DEVICE_DISCONNECTED,
                                device_id=existing_id,
                                previous_state=old_state,
                                new_state=DeviceLifecycleState.DISCONNECTED
                            ))
                        except Exception as exc:
                            logger.debug(f"Failed to transition disappeared device '{existing_id}': {exc}")

            return [d.model_copy() for d in self._devices.values() if d.provider_id == provider_id]

    def poll_all_providers(self) -> List[Device]:
        """Queries all registered providers and reconciles their discovered devices."""
        with self._lock:
            for p_id, provider in self._providers.items():
                try:
                    devices = provider.discover_devices()
                    self.reconcile_discovered_devices(p_id, devices)
                except Exception as exc:
                    logger.warning(f"Error polling provider '{p_id}': {exc}")
            return list(self._devices.values())

    def connect_device(self, device_id: str) -> bool:
        """Establishes an active connection with device_id."""
        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                # Try finding by serial
                for d in self._devices.values():
                    if d.serial == device_id:
                        device = d
                        break

            if not device:
                logger.warning(f"Cannot connect to unknown device '{device_id}'")
                return False

            if device.state not in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.DISCOVERED):
                logger.warning(f"Device '{device.id}' in state '{device.state.value}' cannot be connected")
                return False

            provider = self._providers.get(device.provider_id)
            if not provider:
                logger.warning(f"Provider '{device.provider_id}' for device '{device.id}' not found")
                return False

            old_state = device.state
            transition_device(device, DeviceLifecycleState.CONNECTING, "User session connection request")
            self._notify(DeviceEvent(
                event_type=DeviceEventType.DEVICE_STATE_CHANGED,
                device_id=device.id,
                previous_state=old_state,
                new_state=DeviceLifecycleState.CONNECTING
            ))

            ok = provider.connect(device.id)
            if ok:
                transition_device(device, DeviceLifecycleState.CONNECTED, "Connection established successfully")
                self._notify(DeviceEvent(
                    event_type=DeviceEventType.DEVICE_CONNECTED,
                    device_id=device.id,
                    previous_state=DeviceLifecycleState.CONNECTING,
                    new_state=DeviceLifecycleState.CONNECTED
                ))
                return True
            else:
                transition_device(
                    device,
                    DeviceLifecycleState.ERROR,
                    "Provider connect failed",
                    DeviceError(code="CONNECT_FAILED", message="Provider failed to establish connection")
                )
                self._notify(DeviceEvent(
                    event_type=DeviceEventType.DEVICE_STATE_CHANGED,
                    device_id=device.id,
                    previous_state=DeviceLifecycleState.CONNECTING,
                    new_state=DeviceLifecycleState.ERROR
                ))
                return False

    def disconnect_device(self, device_id: str) -> bool:
        """Closes active connection with device_id."""
        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                for d in self._devices.values():
                    if d.serial == device_id:
                        device = d
                        break

            if not device:
                return False

            if device.state != DeviceLifecycleState.CONNECTED:
                return False

            provider = self._providers.get(device.provider_id)
            if provider:
                provider.disconnect(device.id)

            old_state = device.state
            transition_device(device, DeviceLifecycleState.DISCONNECTING, "User session disconnect request")
            transition_device(device, DeviceLifecycleState.AVAILABLE, "Session released")
            self._notify(DeviceEvent(
                event_type=DeviceEventType.DEVICE_DISCONNECTED,
                device_id=device.id,
                previous_state=old_state,
                new_state=DeviceLifecycleState.AVAILABLE
            ))
            return True

    def transition_device_state(self, device_id: str, new_state: DeviceLifecycleState, reason: str = "") -> bool:
        with self._lock:
            dev = self._devices.get(device_id)
            if not dev:
                for d in self._devices.values():
                    if d.serial == device_id:
                        dev = d
                        break
            if not dev:
                return False
            old_state = dev.state
            try:
                transition_device(dev, new_state, reason or "State transition request")
                self._notify(DeviceEvent(
                    event_type=DeviceEventType.DEVICE_STATE_CHANGED,
                    device_id=dev.id,
                    previous_state=old_state,
                    new_state=new_state
                ))
                return True
            except Exception as e:
                logger.warning(f"Failed to transition device '{dev.id}': {e}")
                return False

    transition_device = transition_device_state

    def get_providers_health(self) -> List[ProviderHealth]:
        with self._lock:
            return [provider.get_health() for provider in self._providers.values()]

    def shutdown(self) -> None:
        with self._lock:
            for p_id, provider in self._providers.items():
                try:
                    provider.cleanup()
                except Exception as exc:
                    logger.debug(f"Error during provider cleanup '{p_id}': {exc}")
            self._devices.clear()
            self._listeners.clear()
