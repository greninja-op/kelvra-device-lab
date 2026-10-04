"""
Unit and integration tests for DeviceRegistry in KELVRA Device Lab.
Adheres strictly to docs/DEVICE_REGISTRY.md and Zero Emoji Prohibition.
"""

import threading
import pytest
from src.domain_model import (
    Device,
    DeviceCapability,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)
from src.device_registry import DeviceEvent, DeviceEventType, DeviceRegistry
from src.mock_provider import MockDeviceProvider
from src.provider_base import ProviderStatus


def _create_mock_device(
    serial: str,
    state: DeviceLifecycleState = DeviceLifecycleState.AVAILABLE,
    provider_id: str = "mock_01"
) -> Device:
    return Device(
        id=f"android:{serial}",
        serial=serial,
        provider_id=provider_id,
        platform=DevicePlatform.ANDROID_PHYSICAL,
        device_type=DeviceType.PHYSICAL,
        display_name=f"Device {serial}",
        manufacturer="MockCorp",
        model=f"MockPhone-{serial}",
        state=state,
        capabilities=[DeviceCapability.DISCOVERY, DeviceCapability.SCREEN_STREAM_JPEG]
    )


def test_registry_provider_registration_and_health():
    registry = DeviceRegistry()
    provider = MockDeviceProvider("mock_01")
    registry.register_provider(provider)

    health_list = registry.get_providers_health()
    assert len(health_list) == 1
    assert health_list[0].provider_id == "mock_01"
    assert health_list[0].status == ProviderStatus.READY

    registry.unregister_provider("mock_01")
    assert len(registry.get_providers_health()) == 0


def test_registry_reconciliation_discovery_and_disappearance():
    registry = DeviceRegistry()
    provider = MockDeviceProvider("mock_01")
    registry.register_provider(provider)

    events: list[DeviceEvent] = []
    registry.subscribe(lambda e: events.append(e))

    dev1 = _create_mock_device("dev-1", DeviceLifecycleState.AVAILABLE)
    dev2 = _create_mock_device("dev-2", DeviceLifecycleState.AVAILABLE)

    # First reconciliation: dev1 and dev2 discovered
    registry.reconcile_discovered_devices(provider.provider_id, [dev1, dev2])
    assert len(registry.list_devices()) == 2
    assert len(events) == 2
    assert events[0].event_type == DeviceEventType.DEVICE_DISCOVERED
    assert events[0].device_id == "android:dev-1"

    # Second reconciliation: dev2 is missing (detached)
    events.clear()
    registry.reconcile_discovered_devices(provider.provider_id, [dev1])
    assert len(registry.list_devices()) == 2
    dev2_reconciled = registry.get_device("android:dev-2")
    assert dev2_reconciled is not None
    assert dev2_reconciled.state == DeviceLifecycleState.DISCONNECTED
    assert len(events) == 1
    assert events[0].event_type == DeviceEventType.DEVICE_DISCONNECTED


def test_registry_connection_flow():
    registry = DeviceRegistry()
    provider = MockDeviceProvider("mock_01")
    registry.register_provider(provider)

    dev = _create_mock_device("dev-conn", DeviceLifecycleState.AVAILABLE)
    provider.add_device(dev)
    registry.poll_all_providers()

    events: list[DeviceEvent] = []
    registry.subscribe(lambda e: events.append(e))

    # Connect device
    ok = registry.connect_device("android:dev-conn")
    assert ok is True
    connected_dev = registry.get_device("android:dev-conn")
    assert connected_dev.state == DeviceLifecycleState.CONNECTED
    assert connected_dev.connected_at is not None

    # Disconnect device
    disc_ok = registry.disconnect_device("android:dev-conn")
    assert disc_ok is True
    disc_dev = registry.get_device("android:dev-conn")
    assert disc_dev.state == DeviceLifecycleState.AVAILABLE


def test_registry_stats_counters():
    registry = DeviceRegistry()
    provider = MockDeviceProvider("mock_01")
    registry.register_provider(provider)

    dev_avail = _create_mock_device("avail-1", DeviceLifecycleState.AVAILABLE)
    dev_unauth = _create_mock_device("unauth-1", DeviceLifecycleState.UNAUTHORIZED)
    dev_busy = _create_mock_device("busy-1", DeviceLifecycleState.BUSY)

    provider.add_device(dev_avail)
    provider.add_device(dev_unauth)
    provider.add_device(dev_busy)
    registry.poll_all_providers()

    stats = registry.get_stats()
    assert stats["total"] == 3
    assert stats["unauthorized"] == 1
    assert stats["busy"] == 1
    assert stats["online"] == 2  # available + busy


def test_registry_thread_safety():
    registry = DeviceRegistry()
    provider = MockDeviceProvider("mock_01")
    registry.register_provider(provider)

    errors = []

    def worker(worker_id: int):
        try:
            for i in range(20):
                dev = _create_mock_device(f"w{worker_id}-d{i}")
                registry.reconcile_discovered_devices(provider.provider_id, [dev])
                _ = registry.list_devices()
                _ = registry.get_stats()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(registry.list_devices()) > 0
