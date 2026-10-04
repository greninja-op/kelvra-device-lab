"""
Unit tests for Device Lifecycle FSM in KELVRA Device Lab.
Adheres strictly to docs/DEVICE_LIFECYCLE.md and Zero Emoji Prohibition.
"""

import pytest
from src.domain_model import (
    Device,
    DeviceError,
    DeviceLifecycleState,
    DevicePlatform,
)
from src.lifecycle import (
    VALID_TRANSITIONS,
    InvalidLifecycleTransitionError,
    can_transition,
    transition_device,
)


def _make_test_device(initial_state: DeviceLifecycleState = DeviceLifecycleState.DISCOVERED) -> Device:
    return Device(
        id="android:test-serial-01",
        serial="test-serial-01",
        provider_id="mock_provider",
        platform=DevicePlatform.ANDROID_PHYSICAL,
        display_name="Test Device",
        state=initial_state
    )


def test_valid_lifecycle_transitions():
    device = _make_test_device(DeviceLifecycleState.DISCOVERED)

    # DISCOVERED -> AVAILABLE
    transition_device(device, DeviceLifecycleState.AVAILABLE, "Device authorized and introspected")
    assert device.state == DeviceLifecycleState.AVAILABLE

    # AVAILABLE -> CONNECTING
    transition_device(device, DeviceLifecycleState.CONNECTING, "Session connection initiated")
    assert device.state == DeviceLifecycleState.CONNECTING

    # CONNECTING -> CONNECTED
    transition_device(device, DeviceLifecycleState.CONNECTED, "Session established")
    assert device.state == DeviceLifecycleState.CONNECTED
    assert device.connected_at is not None

    # CONNECTED -> BUSY
    transition_device(device, DeviceLifecycleState.BUSY, "Automation test running")
    assert device.state == DeviceLifecycleState.BUSY

    # BUSY -> CONNECTED
    transition_device(device, DeviceLifecycleState.CONNECTED, "Automation finished")
    assert device.state == DeviceLifecycleState.CONNECTED

    # CONNECTED -> DISCONNECTING
    transition_device(device, DeviceLifecycleState.DISCONNECTING, "Closing session")
    assert device.state == DeviceLifecycleState.DISCONNECTING

    # DISCONNECTING -> AVAILABLE
    transition_device(device, DeviceLifecycleState.AVAILABLE, "Session released")
    assert device.state == DeviceLifecycleState.AVAILABLE
    assert device.connected_at is None


def test_invalid_lifecycle_transition_raises():
    device = _make_test_device(DeviceLifecycleState.DISCOVERED)

    # DISCOVERED cannot transition directly to CONNECTED without intermediate steps
    with pytest.raises(InvalidLifecycleTransitionError) as exc_info:
        transition_device(device, DeviceLifecycleState.CONNECTED, "Direct jump attempt")

    assert "Cannot transition device 'android:test-serial-01' from 'discovered' to 'connected'" in str(exc_info.value)
    assert device.state == DeviceLifecycleState.DISCOVERED


def test_unauthorized_lifecycle():
    device = _make_test_device(DeviceLifecycleState.DISCOVERED)

    err = DeviceError(
        code="ADB_UNAUTHORIZED",
        message="Device prompt pending",
        recovery_hint="Tap accept prompt on device"
    )
    transition_device(device, DeviceLifecycleState.UNAUTHORIZED, "Host unapproved", error=err)
    assert device.state == DeviceLifecycleState.UNAUTHORIZED
    assert device.error is not None
    assert device.error.code == "ADB_UNAUTHORIZED"

    # Unauthorized -> Available once user accepts prompt
    transition_device(device, DeviceLifecycleState.AVAILABLE, "RSA key accepted")
    assert device.state == DeviceLifecycleState.AVAILABLE
    assert device.error is None  # Resolved errors cleared on available


def test_error_state_transition_and_recovery():
    device = _make_test_device(DeviceLifecycleState.CONNECTING)

    err = DeviceError(code="PORT_FORWARD_FAILED", message="ADB port forward failed")
    transition_device(device, DeviceLifecycleState.ERROR, "Transport error", error=err)
    assert device.state == DeviceLifecycleState.ERROR
    assert device.error.code == "PORT_FORWARD_FAILED"

    # Recovery: ERROR -> AVAILABLE
    transition_device(device, DeviceLifecycleState.AVAILABLE, "Recovered")
    assert device.state == DeviceLifecycleState.AVAILABLE
    assert device.error is None


def test_idempotent_transition():
    device = _make_test_device(DeviceLifecycleState.AVAILABLE)
    transition_device(device, DeviceLifecycleState.AVAILABLE, "No-op reaffirmation")
    assert device.state == DeviceLifecycleState.AVAILABLE
