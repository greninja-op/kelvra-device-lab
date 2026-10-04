"""
Connection Lifecycle State Machine for KELVRA Device Lab.
Enforces valid deterministic transitions across the 10 device lifecycle states.
Zero Emoji Prohibition Enforced.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set
from src.domain_model import Device, DeviceError, DeviceLifecycleState

logger = logging.getLogger("kelvra.device_lab.lifecycle")


class InvalidLifecycleTransitionError(Exception):
    """Raised when an illegal device lifecycle state transition is attempted."""
    def __init__(self, device_id: str, current_state: DeviceLifecycleState, target_state: DeviceLifecycleState, reason: str = ""):
        self.device_id = device_id
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason
        msg = f"Cannot transition device '{device_id}' from '{current_state.value}' to '{target_state.value}'"
        if reason:
            msg += f" (Reason: {reason})"
        super().__init__(msg)


# Definitive Transition Rule Table
VALID_TRANSITIONS: Dict[DeviceLifecycleState, Set[DeviceLifecycleState]] = {
    DeviceLifecycleState.DISCOVERED: {
        DeviceLifecycleState.UNAUTHORIZED,
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.UNAUTHORIZED: {
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.DISCOVERED,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.AVAILABLE: {
        DeviceLifecycleState.CONNECTING,
        DeviceLifecycleState.BUSY,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.CONNECTING: {
        DeviceLifecycleState.CONNECTED,
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.CONNECTED: {
        DeviceLifecycleState.BUSY,
        DeviceLifecycleState.DISCONNECTING,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.BUSY: {
        DeviceLifecycleState.CONNECTED,
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.UNAVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.DISCONNECTING: {
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.UNAVAILABLE: {
        DeviceLifecycleState.DISCOVERED,
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.UNAUTHORIZED,
        DeviceLifecycleState.DISCONNECTED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.DISCONNECTED: {
        DeviceLifecycleState.DISCOVERED,
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.UNAUTHORIZED,
        DeviceLifecycleState.ERROR,
    },
    DeviceLifecycleState.ERROR: {
        DeviceLifecycleState.AVAILABLE,
        DeviceLifecycleState.DISCOVERED,
        DeviceLifecycleState.DISCONNECTED,
    },
}


def can_transition(current_state: DeviceLifecycleState, target_state: DeviceLifecycleState) -> bool:
    """Check whether a transition from current_state to target_state is permitted."""
    if current_state == target_state:
        return True  # Idempotent state re-assertion is allowed
    allowed = VALID_TRANSITIONS.get(current_state, set())
    return target_state in allowed


def transition_device(
    device: Device,
    new_state: DeviceLifecycleState,
    reason: str = "",
    error: Optional[DeviceError] = None
) -> None:
    """
    Executes a validated lifecycle transition on a device instance.
    Updates timestamps, handles error attaching/clearing, and logs state movements.
    """
    if not can_transition(device.state, new_state):
        raise InvalidLifecycleTransitionError(
            device_id=device.id,
            current_state=device.state,
            target_state=new_state,
            reason=reason
        )

    old_state = device.state
    device.state = new_state
    device.last_seen = datetime.now(timezone.utc).isoformat()

    if new_state == DeviceLifecycleState.CONNECTED:
        device.connected_at = datetime.now(timezone.utc).isoformat()
    elif new_state in (DeviceLifecycleState.DISCONNECTED, DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.DISCOVERED):
        device.connected_at = None

    if error:
        device.error = error
    elif new_state in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.CONNECTED):
        device.error = None  # Clear resolved errors upon successful availability/connection

    logger.info(
        f"Device '{device.id}' state changed: {old_state.value} -> {new_state.value}"
        + (f" ({reason})" if reason else "")
    )
