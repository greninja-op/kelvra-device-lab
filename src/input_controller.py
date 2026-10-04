"""
Input Controller for KELVRA Device Lab.
Provides remote touch, gesture, hardware button, and keyboard input injection over ADB.
Enforces session lease validation, device authorization checks, coordinate bounds verification,
and discrete argument vector execution with shell=False.
"""

import io
import logging
import re
import subprocess
from typing import Optional, Tuple
from PIL import Image

from src.device_manager import DeviceManager
from src.domain_model import DeviceLifecycleState

logger = logging.getLogger("kelvra.device_lab.input")


# Standard Android Keycodes
KEYCODES = {
    "HOME": 3,
    "BACK": 4,
    "POWER": 26,
    "VOLUME_UP": 24,
    "VOLUME_DOWN": 25,
    "APP_SWITCH": 187,
    "ENTER": 66,
    "DEL": 67,
    "TAB": 61,
    "SPACE": 62,
    "MENU": 82
}


class InputController:
    """Manages remote input events, coordinate validation, session verification, and frame captures."""

    def __init__(self, device_manager: DeviceManager, session_manager=None, device_registry=None):
        self.device_manager = device_manager
        self.session_manager = session_manager
        self.device_registry = device_registry

    def set_session_manager(self, session_manager):
        self.session_manager = session_manager

    def set_device_registry(self, device_registry):
        self.device_registry = device_registry

    def _normalize_id(self, serial: str) -> str:
        if serial.startswith("android:"):
            return serial
        return f"android:{serial}"

    def _validate_permission(self, serial: str, session_token: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates whether input dispatch is permitted on the target device.
        Checks device authorization, connection status, and operator lease holding.
        """
        device_id = self._normalize_id(serial)

        # 1. Device Registry check
        if self.device_registry:
            dev = self.device_registry.get_device(device_id)
            if dev:
                if dev.state == DeviceLifecycleState.UNAUTHORIZED:
                    return False, f"Device {serial} is unauthorized. Confirm RSA key on screen."
                if dev.state in (DeviceLifecycleState.UNAVAILABLE, DeviceLifecycleState.DISCONNECTED):
                    return False, f"Device {serial} is offline or unavailable."

        # 2. Session Manager lease check if session_token is provided or lease is active
        if self.session_manager:
            active_lease = self.session_manager.get_active_lease(device_id)
            if active_lease:
                if not session_token or active_lease.session_token != session_token:
                    return False, f"Device is exclusively locked by session '{active_lease.client_id}'."

        return True, ""

    def _get_display_bounds(self, serial: str) -> Tuple[int, int]:
        """Returns (width, height) bounds for coordinate validation, defaulting to 1080x2400."""
        if self.device_manager:
            dev_info = self.device_manager.get_device(serial)
            if dev_info and getattr(dev_info, "screen_width", None) and getattr(dev_info, "screen_height", None):
                return dev_info.screen_width, dev_info.screen_height

        device_id = self._normalize_id(serial)
        if self.device_registry:
            dev = self.device_registry.get_device(device_id)
            if dev and hasattr(dev, "metadata") and isinstance(dev.metadata, dict):
                res = dev.metadata.get("display_resolution")
                if res and isinstance(res, str):
                    match = re.match(r"(\d+)x(\d+)", res)
                    if match:
                        return int(match.group(1)), int(match.group(2))
        return 1080, 2400

    def tap(self, serial: str, x: int, y: int, session_token: Optional[str] = None) -> bool:
        """Inject tap event at (x, y) with coordinate boundary checking."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Tap rejected on {serial}: {reason}")
            return False

        max_w, max_h = self._get_display_bounds(serial)
        if x < 0 or y < 0 or x > max_w * 2 or y > max_h * 2:
            logger.warning(f"Tap coordinates ({x}, {y}) out of realistic bounds on {serial}")
            return False

        logger.info(f"Injecting tap on {serial} at ({x}, {y})")
        if serial in self.device_manager._mock_devices:
            return True

        res = self.device_manager.run_adb(["shell", "input", "tap", str(x), str(y)], serial=serial, timeout=3.0)
        return res.returncode == 0

    def long_press(
        self,
        serial: str,
        x: int,
        y: int,
        duration_ms: int = 1000,
        session_token: Optional[str] = None
    ) -> bool:
        """Inject long press (simulated via swipe with identical start/end coordinates)."""
        return self.swipe(serial, x, y, x, y, duration_ms=duration_ms, session_token=session_token)

    def swipe(
        self,
        serial: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
        session_token: Optional[str] = None
    ) -> bool:
        """Inject swipe gesture from (x1, y1) to (x2, y2)."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Swipe rejected on {serial}: {reason}")
            return False

        max_w, max_h = self._get_display_bounds(serial)
        for cx, cy in [(x1, y1), (x2, y2)]:
            if cx < 0 or cy < 0 or cx > max_w * 2 or cy > max_h * 2:
                logger.warning(f"Swipe coordinates ({cx}, {cy}) out of bounds on {serial}")
                return False

        duration = max(50, min(5000, duration_ms))
        logger.info(f"Injecting swipe on {serial} from ({x1},{y1}) to ({x2},{y2}) in {duration}ms")
        if serial in self.device_manager._mock_devices:
            return True

        res = self.device_manager.run_adb(
            ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)],
            serial=serial,
            timeout=5.0
        )
        return res.returncode == 0

    def keyevent(self, serial: str, key: str | int, session_token: Optional[str] = None) -> bool:
        """Inject hardware key event by name (e.g. 'BACK', 'HOME') or keycode integer."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Keyevent rejected on {serial}: {reason}")
            return False

        if isinstance(key, str):
            keycode = KEYCODES.get(key.upper(), None)
            if keycode is None:
                try:
                    keycode = int(key)
                except ValueError:
                    logger.warning(f"Unknown key name '{key}' on {serial}")
                    return False
        else:
            keycode = key

        logger.info(f"Injecting keyevent {keycode} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True

        res = self.device_manager.run_adb(["shell", "input", "keyevent", str(keycode)], serial=serial, timeout=3.0)
        return res.returncode == 0

    def type_text(self, serial: str, text: str, session_token: Optional[str] = None) -> bool:
        """Inject keyboard text input with strict sanitization."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Text input rejected on {serial}: {reason}")
            return False

        if not text:
            return True

        logger.info(f"Injecting text input ({len(text)} chars) on {serial}")
        if serial in self.device_manager._mock_devices:
            return True

        # ADB input text escaping: replace spaces with %s and escape shell control characters
        escaped_text = (
            text.replace(" ", "%s")
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace("&", "\\&")
            .replace(";", "\\;")
            .replace("|", "\\|")
            .replace("<", "\\<")
            .replace(">", "\\>")
            .replace("`", "\\`")
            .replace("$", "\\$")
        )
        res = self.device_manager.run_adb(["shell", "input", "text", escaped_text], serial=serial, timeout=4.0)
        return res.returncode == 0

    def launch_app(
        self,
        serial: str,
        package: str,
        activity: Optional[str] = None,
        session_token: Optional[str] = None
    ) -> bool:
        """Launch an application component."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Launch app rejected on {serial}: {reason}")
            return False

        logger.info(f"Launching app {package} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True

        if activity:
            comp = f"{package}/{activity}" if not activity.startswith(package) else activity
            res = self.device_manager.run_adb(["shell", "am", "start", "-n", comp], serial=serial, timeout=5.0)
        else:
            res = self.device_manager.run_adb(
                ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
                serial=serial,
                timeout=5.0
            )
        return res.returncode == 0

    def stop_app(self, serial: str, package: str, session_token: Optional[str] = None) -> bool:
        """Force-stop an application package."""
        allowed, reason = self._validate_permission(serial, session_token)
        if not allowed:
            logger.warning(f"Stop app rejected on {serial}: {reason}")
            return False

        logger.info(f"Force-stopping package {package} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True

        res = self.device_manager.run_adb(["shell", "am", "force-stop", package], serial=serial, timeout=3.0)
        return res.returncode == 0

    def take_screenshot(self, serial: str, max_width: int = 1080, quality: int = 75) -> Optional[bytes]:
        """Capture screenshot from device and return compressed JPEG bytes."""
        if serial in self.device_manager._mock_devices:
            # Synthetic test pattern for mock devices
            img = Image.new("RGB", (720, 1600), color=(38, 38, 36))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue()

        cmd = [self.device_manager.adb_path, "-s", serial, "exec-out", "screencap", "-p"]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=5.0, check=False)
            if res.returncode == 0 and res.stdout:
                raw_bytes = res.stdout
                try:
                    img = Image.open(io.BytesIO(raw_bytes))
                    if img.width > max_width:
                        ratio = max_width / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                    buf = io.BytesIO()
                    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
                    return buf.getvalue()
                except Exception as img_err:
                    logger.warning(f"Image processing error: {img_err}, returning raw payload")
                    return raw_bytes
            return None
        except Exception as exc:
            logger.error(f"Screenshot capture failed for {serial}: {exc}")
            return None
