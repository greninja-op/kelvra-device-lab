"""
Session Isolation and Single-Writer Lease Manager for KELVRA Device Lab.
Enforces exclusive operator lease allocation, heartbeat renewals, and resource cleanup.
Adheres strictly to docs/SESSION_ISOLATION.md and zero-emoji compliance.
"""

import logging
import threading
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.domain_model import DeviceLifecycleState

logger = logging.getLogger("kelvra.device_lab.session_manager")


class LeaseConflictError(Exception):
    """Raised when an exclusive lease cannot be acquired because the device is already locked."""
    def __init__(self, message: str, held_by: str, expires_in_seconds: float):
        super().__init__(message)
        self.held_by = held_by
        self.expires_in_seconds = expires_in_seconds


class DeviceLease(BaseModel):
    """Exclusive operator lease holding device control authority."""
    lease_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    serial: str
    client_id: str
    session_token: str = Field(default_factory=lambda: f"kdl-{uuid.uuid4().hex[:16]}")
    purpose: str = "Manual Teleoperation"
    acquired_at: float = Field(default_factory=time.time)
    expires_at: float
    last_heartbeat: float = Field(default_factory=time.time)
    duration_seconds: float = 300.0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self.expires_at - time.time())


class SessionManager:
    """
    Thread-safe session manager guaranteeing Single-Writer Lease exclusivity.
    Permits unlimited concurrent read-only stream viewers, but restricts
    touch, swipe, keyboard input, and automated execution to exactly one session.
    """

    def __init__(self, default_lease_duration: float = 300.0):
        self._lock = threading.RLock()
        self._leases: Dict[str, DeviceLease] = {}  # device_id -> DeviceLease
        self._default_duration = default_lease_duration
        self._device_registry = None

    def set_registry(self, registry):
        """Attaches DeviceRegistry for updating lifecycle state."""
        self._device_registry = registry

    def _normalize_id(self, device_id_or_serial: str) -> str:
        if device_id_or_serial.startswith("android:"):
            return device_id_or_serial
        return f"android:{device_id_or_serial}"

    def acquire_lease(
        self,
        device_id_or_serial: str,
        client_id: str,
        duration_seconds: Optional[float] = None,
        purpose: str = "Manual Teleoperation"
    ) -> DeviceLease:
        """
        Acquires exclusive single-writer operator lease on a device.
        Raises LeaseConflictError if held by another active session.
        Raises ValueError / PermissionError if device is offline or unauthorized.
        """
        normalized_id = self._normalize_id(device_id_or_serial)
        duration = duration_seconds or self._default_duration

        with self._lock:
            # Check device status if registry is present
            if self._device_registry:
                device = self._device_registry.get_device(normalized_id)
                if not device:
                    raise ValueError(f"Device {normalized_id} not registered.")
                if device.state == DeviceLifecycleState.UNAUTHORIZED:
                    raise PermissionError(
                        f"Device {normalized_id} is unauthorized. Unlock screen and accept RSA prompt."
                    )
                if device.state in (DeviceLifecycleState.UNAVAILABLE, DeviceLifecycleState.DISCONNECTED):
                    raise ValueError(f"Device {normalized_id} is unavailable or disconnected.")

            now = time.time()
            existing = self._leases.get(normalized_id)

            if existing:
                if existing.is_expired:
                    # Clean up expired lease
                    logger.info(f"Existing lease for {normalized_id} held by {existing.client_id} expired.")
                    del self._leases[normalized_id]
                elif existing.client_id == client_id:
                    # Re-acquisition by same client -> renew lease
                    existing.expires_at = now + duration
                    existing.last_heartbeat = now
                    existing.purpose = purpose or existing.purpose
                    logger.info(f"Renewed existing lease for {client_id} on {normalized_id}")
                    return existing
                else:
                    # Locked by different client
                    remaining = existing.remaining_seconds
                    logger.warning(
                        f"Lease collision on {normalized_id}: requested by {client_id}, held by {existing.client_id}"
                    )
                    raise LeaseConflictError(
                        f"Device is locked by session '{existing.client_id}'.",
                        held_by=existing.client_id,
                        expires_in_seconds=remaining
                    )

            # Create new exclusive lease
            serial = normalized_id.split(":", 1)[1] if ":" in normalized_id else normalized_id
            lease = DeviceLease(
                device_id=normalized_id,
                serial=serial,
                client_id=client_id,
                purpose=purpose,
                acquired_at=now,
                expires_at=now + duration,
                last_heartbeat=now,
                duration_seconds=duration
            )
            self._leases[normalized_id] = lease

            # Update registry lifecycle state to BUSY if available
            if self._device_registry:
                try:
                    self._device_registry.transition_device(normalized_id, DeviceLifecycleState.BUSY)
                except Exception as exc:
                    logger.debug(f"Lifecycle state transition to BUSY: {exc}")

            logger.info(f"Granted exclusive lease on {normalized_id} to {client_id} (lease_id={lease.lease_id})")
            return lease

    def renew_lease(
        self,
        device_id_or_serial: str,
        session_token: str,
        extension_seconds: Optional[float] = None
    ) -> DeviceLease:
        """Extends an active lease heartbeat."""
        normalized_id = self._normalize_id(device_id_or_serial)
        extension = extension_seconds or self._default_duration

        with self._lock:
            lease = self._leases.get(normalized_id)
            if not lease:
                raise ValueError(f"No active lease found for {normalized_id}")
            if lease.session_token != session_token:
                raise PermissionError("Invalid session token for lease renewal.")
            if lease.is_expired:
                del self._leases[normalized_id]
                raise ValueError("Lease has already expired. Re-acquisition required.")

            now = time.time()
            lease.expires_at = now + extension
            lease.last_heartbeat = now
            logger.debug(f"Heartbeat received: lease renewed for {normalized_id} until {lease.expires_at}")
            return lease

    def release_lease(
        self,
        device_id_or_serial: str,
        session_token: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """Releases an exclusive lease and restores device to available state."""
        normalized_id = self._normalize_id(device_id_or_serial)

        with self._lock:
            lease = self._leases.get(normalized_id)
            if not lease:
                return True

            if not force and session_token and lease.session_token != session_token:
                raise PermissionError("Unauthorized: session token does not match lease holder.")

            del self._leases[normalized_id]
            logger.info(f"Released lease on {normalized_id} (held by {lease.client_id})")

            # Restore registry state
            if self._device_registry:
                try:
                    self._device_registry.transition_device(normalized_id, DeviceLifecycleState.AVAILABLE)
                except Exception as exc:
                    logger.debug(f"Registry transition on lease release: {exc}")

            return True

    def get_active_lease(self, device_id_or_serial: str) -> Optional[DeviceLease]:
        """Returns the active non-expired lease, or None if unleased or expired."""
        normalized_id = self._normalize_id(device_id_or_serial)
        with self._lock:
            lease = self._leases.get(normalized_id)
            if lease and lease.is_expired:
                del self._leases[normalized_id]
                if self._device_registry:
                    try:
                        self._device_registry.transition_device(normalized_id, DeviceLifecycleState.AVAILABLE)
                    except Exception:
                        pass
                return None
            return lease

    def validate_writer(self, device_id_or_serial: str, session_token: Optional[str] = None) -> bool:
        """
        Validates whether the caller holds active exclusive writer authority.
        Returns True if lease exists and token matches, or False otherwise.
        """
        lease = self.get_active_lease(device_id_or_serial)
        if not lease:
            return False
        if not session_token:
            return False
        return lease.session_token == session_token

    def revoke_device_leases(self, device_id_or_serial: str) -> int:
        """Revokes all leases on device disconnection or detachment."""
        normalized_id = self._normalize_id(device_id_or_serial)
        with self._lock:
            if normalized_id in self._leases:
                del self._leases[normalized_id]
                logger.info(f"Revoked active leases for disconnected device {normalized_id}")
                return 1
            return 0

    def list_active_leases(self) -> List[DeviceLease]:
        """Returns all non-expired leases."""
        with self._lock:
            active = []
            expired_keys = []
            for dev_id, lease in self._leases.items():
                if lease.is_expired:
                    expired_keys.append(dev_id)
                else:
                    active.append(lease)
            for k in expired_keys:
                del self._leases[k]
            return active
