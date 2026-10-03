"""
Input Controller for KELVRA Device Lab.
Provides remote touch, gesture, hardware button, and keyboard input injection over ADB.
"""

import io
import logging
import shlex
import subprocess
from typing import Optional
from PIL import Image

from src.device_manager import DeviceManager

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
    """Manages input events and screenshot capture."""

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager

    def tap(self, serial: str, x: int, y: int) -> bool:
        """Inject tap event at (x, y)."""
        logger.info(f"Injecting tap on {serial} at ({x}, {y})")
        if serial in self.device_manager._mock_devices:
            return True
        res = self.device_manager.run_adb(["shell", "input", "tap", str(x), str(y)], serial=serial, timeout=3.0)
        return res.returncode == 0

    def swipe(self, serial: str, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Inject swipe gesture from (x1, y1) to (x2, y2)."""
        logger.info(f"Injecting swipe on {serial} from ({x1},{y1}) to ({x2},{y2}) in {duration_ms}ms")
        if serial in self.device_manager._mock_devices:
            return True
        res = self.device_manager.run_adb(
            ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
            serial=serial,
            timeout=5.0
        )
        return res.returncode == 0

    def keyevent(self, serial: str, key: str | int) -> bool:
        """Inject key event by name or keycode integer."""
        if isinstance(key, str):
            keycode = KEYCODES.get(key.upper(), key)
        else:
            keycode = key

        logger.info(f"Injecting keyevent {keycode} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True
        res = self.device_manager.run_adb(["shell", "input", "keyevent", str(keycode)], serial=serial, timeout=3.0)
        return res.returncode == 0

    def type_text(self, serial: str, text: str) -> bool:
        """Inject keyboard text input."""
        logger.info(f"Injecting text input ({len(text)} chars) on {serial}")
        if serial in self.device_manager._mock_devices:
            return True
        # Escape spaces and special chars for adb shell input text
        escaped_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        res = self.device_manager.run_adb(["shell", "input", "text", escaped_text], serial=serial, timeout=4.0)
        return res.returncode == 0

    def launch_app(self, serial: str, package: str, activity: Optional[str] = None) -> bool:
        """Launch an application component via monkey or am start."""
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

    def stop_app(self, serial: str, package: str) -> bool:
        """Force-stop an application package."""
        logger.info(f"Force-stopping package {package} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True
        res = self.device_manager.run_adb(["shell", "am", "force-stop", package], serial=serial, timeout=3.0)
        return res.returncode == 0

    def take_screenshot(self, serial: str, max_width: int = 1080, quality: int = 75) -> Optional[bytes]:
        """Capture screenshot from device and return compressed JPEG bytes."""
        if serial in self.device_manager._mock_devices:
            # Return synthetic test pattern image
            img = Image.new("RGB", (720, 1600), color=(38, 38, 36))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue()

        cmd = [self.device_manager.adb_path, "-s", serial, "exec-out", "screencap", "-p"]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=5.0, check=False)
            if res.returncode == 0 and res.stdout:
                # Open with Pillow, optionally resize and compress to JPEG
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
                    logger.warning(f"Image processing error: {img_err}, returning raw PNG")
                    return raw_bytes
            return None
        except Exception as exc:
            logger.error(f"Screenshot capture failed for {serial}: {exc}")
            return None
