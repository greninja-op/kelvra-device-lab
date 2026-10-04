"""
Diagnostics Service for KELVRA Device Lab.
Aggregates verifiable, measurable diagnostics across providers, hardware connections,
active video streams, operator leases, and emulator runtimes.
Enforces the zero-fabrication contract: all metrics are directly measured or queried.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.device_registry import DeviceRegistry
from src.domain_model import DeviceLifecycleState, DevicePlatform

logger = logging.getLogger("kelvra.device_lab.diagnostics")


class DeviceDiagnosticReport(BaseModel):
    device_id: str
    serial: str
    platform: str
    lifecycle_state: str
    is_authorized: bool
    provider_id: str
    provider_health: Dict[str, Any]
    stream_diagnostics: Optional[Dict[str, Any]] = None
    session_lease: Optional[Dict[str, Any]] = None
    emulator_health: Optional[Dict[str, Any]] = None
    battery_telemetry: Optional[Dict[str, Any]] = None
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)
    measured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DiagnosticsService:
    """Collects and organizes measurable diagnostic reports for connected devices."""

    def __init__(
        self,
        device_registry: DeviceRegistry,
        screen_streamer=None,
        session_manager=None,
        avd_manager=None,
        device_manager=None,
        max_error_history: int = 20
    ):
        self.device_registry = device_registry
        self.screen_streamer = screen_streamer
        self.session_manager = session_manager
        self.avd_manager = avd_manager
        self.device_manager = device_manager
        self.max_error_history = max_error_history
        self._error_logs: Dict[str, List[Dict[str, Any]]] = {}

    def log_error(self, device_id: str, error_code: str, message: str, operation: str = "general"):
        if device_id not in self._error_logs:
            self._error_logs[device_id] = []
        entry = {
            "error_code": error_code,
            "message": message,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._error_logs[device_id].append(entry)
        if len(self._error_logs[device_id]) > self.max_error_history:
            self._error_logs[device_id].pop(0)

    def get_diagnostics(self, serial_or_id: str) -> Optional[DeviceDiagnosticReport]:
        """Gathers verifiable diagnostic metrics for a specific device."""
        dev = self.device_registry.get_device(serial_or_id)
        if not dev:
            raw_serial = serial_or_id.split(":", 1)[1] if ":" in serial_or_id else serial_or_id
            dev = self.device_registry.get_device(f"android:{raw_serial}")
            if not dev:
                dev = self.device_registry.get_device(f"apple:{raw_serial}")

        if not dev:
            return None

        raw_serial = dev.serial

        # 1. Provider health
        provider = self.device_registry._providers.get(dev.provider_id)
        p_health = {}
        if provider:
            try:
                p_health = provider.get_device_health(dev.id)
            except Exception as e:
                p_health = {"status": "error", "error": str(e)}
        else:
            p_health = {"status": "unregistered_provider"}

        # 2. Screen stream diagnostics
        stream_diag = None
        if self.screen_streamer:
            try:
                diag = self.screen_streamer.get_diagnostics(raw_serial)
                if diag:
                    stream_diag = diag.model_dump()
            except Exception:
                pass

        # 3. Session Lease
        lease_data = None
        if self.session_manager:
            lease = self.session_manager.get_active_lease(dev.id)
            if lease:
                lease_data = lease.model_dump()

        # 4. Emulator Health (if AVD)
        emu_health = None
        if dev.platform == DevicePlatform.ANDROID_VIRTUAL and self.avd_manager:
            # Match running AVD by serial
            for avd_name, avd_cfg in self.avd_manager._avds.items():
                if avd_cfg.running_serial == raw_serial:
                    sess = self.avd_manager.get_active_session(avd_name)
                    emu_health = {
                        "avd_name": avd_name,
                        "status": avd_cfg.status.value,
                        "console_port": avd_cfg.console_port,
                        "pid": sess.pid if sess else None,
                        "state": sess.state.value if sess else "NONE",
                        "boot_completed": sess.boot_completed if sess else False,
                        "boot_duration_seconds": sess.boot_duration_seconds if sess else None
                    }
                    break

        # 5. Battery & Hardware Telemetry (measured only)
        battery_data = None
        if "battery_level" in dev.metadata:
            battery_data = {
                "level": dev.metadata.get("battery_level"),
                "charging": dev.metadata.get("battery_charging", False),
                "temperature_c": dev.metadata.get("battery_temperature")
            }
        elif self.device_manager:
            mgr_dev = self.device_manager.get_device(raw_serial)
            if mgr_dev and hasattr(mgr_dev, "battery_level"):
                battery_data = {
                    "level": mgr_dev.battery_level,
                    "charging": mgr_dev.battery_charging,
                    "temperature_c": mgr_dev.battery_temperature
                }

        # 6. Recent error history
        recent_errs = self._error_logs.get(dev.id, [])
        if dev.error and not any(e.get("error_code") == dev.error.code for e in recent_errs):
            recent_errs = [{
                "error_code": dev.error.code,
                "message": dev.error.message,
                "operation": "lifecycle",
                "timestamp": dev.error.timestamp
            }] + recent_errs

        return DeviceDiagnosticReport(
            device_id=dev.id,
            serial=dev.serial,
            platform=dev.platform.value,
            lifecycle_state=dev.state.value,
            is_authorized=dev.state in (DeviceLifecycleState.AVAILABLE, DeviceLifecycleState.CONNECTED, DeviceLifecycleState.BUSY),
            provider_id=dev.provider_id,
            provider_health=p_health,
            stream_diagnostics=stream_diag,
            session_lease=lease_data,
            emulator_health=emu_health,
            battery_telemetry=battery_data,
            recent_errors=recent_errs
        )
