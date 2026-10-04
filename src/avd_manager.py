"""
Android Virtual Device (AVD) Management & Emulator Lifecycle Subsystem.
Coordinates SDK environment detection, AVD inventory discovery, configuration inspection,
emulator process orchestration, boot readiness tracking, and Device Registry integration.
Adheres strictly to Process Execution Security and Zero Emoji Prohibition.
"""

import asyncio
import configparser
import logging
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.domain_model import (
    ConnectionTransport,
    Device,
    DeviceCapability,
    DeviceLifecycleState,
    DevicePlatform,
    DeviceType,
)

logger = logging.getLogger("kelvra.device_lab.avd")

# Safe AVD Name Pattern: alphanumeric, underscore, hyphen only (max 64 chars)
AVD_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")


class AvdStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    BOOTING = "booting"
    READY = "ready"
    STOPPING = "stopping"
    FAILED = "failed"


class SdkEnvironmentStatus(BaseModel):
    sdk_root: Optional[str] = None
    sdk_detected: bool = False
    adb_path: Optional[str] = None
    adb_available: bool = False
    adb_version: Optional[str] = None
    emulator_path: Optional[str] = None
    emulator_available: bool = False
    emulator_version: Optional[str] = None
    avdmanager_path: Optional[str] = None
    avdmanager_available: bool = False
    sdkmanager_path: Optional[str] = None
    sdkmanager_available: bool = False
    system_images: List[str] = Field(default_factory=list)
    avd_home: Optional[str] = None
    installed_avd_count: int = 0
    setup_guidance: Optional[str] = None


class AvdConfig(BaseModel):
    name: str
    path: str
    target: Optional[str] = "Android API"
    api_level: Optional[int] = None
    abi: Optional[str] = "x86_64"
    device_profile: Optional[str] = "Generic Phone"
    tag: Optional[str] = "google_apis"
    sdcard_size: Optional[str] = None
    heap_size: Optional[str] = None
    ram_size: Optional[str] = None
    skin: Optional[str] = None
    status: AvdStatus = AvdStatus.STOPPED
    running_serial: Optional[str] = None
    pid: Optional[int] = None
    error_message: Optional[str] = None


class EmulatorLaunchOptions(BaseModel):
    headless: bool = True
    no_snapshot: bool = True
    no_audio: bool = True
    wipe_data: bool = False
    port: Optional[int] = None
    memory_mb: Optional[int] = None
    cores: Optional[int] = None
    gpu_mode: Optional[str] = "auto"
    additional_args: List[str] = Field(default_factory=list)


class CreateAvdRequest(BaseModel):
    name: str
    system_image: str
    device_profile: str = "pixel_6"
    tag: str = "google_apis"
    abi: str = "x86_64"
    sdcard_size: Optional[str] = "512M"
    ram_mb: Optional[int] = 2048
    force: bool = False


class SdkEnvironmentDetector:
    """
    Detects host Android development tools without executing arbitrary shell strings
    or downloading unapproved components.
    """

    def __init__(
        self,
        custom_sdk_root: Optional[str] = None,
        custom_adb_path: Optional[str] = None,
        custom_emulator_path: Optional[str] = None,
        custom_avd_home: Optional[str] = None,
    ):
        self._custom_sdk_root = custom_sdk_root
        self._custom_adb_path = custom_adb_path
        self._custom_emulator_path = custom_emulator_path
        self._custom_avd_home = custom_avd_home

    def detect_environment(self) -> SdkEnvironmentStatus:
        sdk_root = self.resolve_sdk_root()
        adb_path, adb_ok, adb_ver = self.resolve_adb(sdk_root)
        emu_path, emu_ok, emu_ver = self.resolve_emulator(sdk_root)
        avdmgr_path, avdmgr_ok = self.resolve_avdmanager(sdk_root)
        sdkmgr_path, sdkmgr_ok = self.resolve_sdkmanager(sdk_root)
        sys_images = self.discover_system_images(sdk_root)
        avd_home, avd_count = self.resolve_avd_home()

        # Build guidance notes
        guidance = []
        if not sdk_root:
            guidance.append(
                "Android SDK root not found. Set ANDROID_HOME or install Android Studio SDK Platform-Tools."
            )
        if not emu_ok:
            guidance.append(
                "Android Emulator binary missing. Install 'Android Emulator' via SDK Manager or sdkmanager 'emulator'."
            )
        if not sys_images:
            guidance.append(
                "No system images found in SDK. Download a system image (e.g. 'system-images;android-34;google_apis;x86_64') via SDK Manager."
            )
        if not avdmgr_ok:
            guidance.append(
                "AVD Manager tooling missing. Install Android SDK Command-line Tools (cmdline-tools;latest)."
            )

        setup_guidance = " | ".join(guidance) if guidance else "All required Android SDK and Emulator tools are available."

        return SdkEnvironmentStatus(
            sdk_root=sdk_root,
            sdk_detected=bool(sdk_root and os.path.exists(sdk_root)),
            adb_path=adb_path,
            adb_available=adb_ok,
            adb_version=adb_ver,
            emulator_path=emu_path,
            emulator_available=emu_ok,
            emulator_version=emu_ver,
            avdmanager_path=avdmgr_path,
            avdmanager_available=avdmgr_ok,
            sdkmanager_path=sdkmgr_path,
            sdkmanager_available=sdkmgr_ok,
            system_images=sys_images,
            avd_home=avd_home,
            installed_avd_count=avd_count,
            setup_guidance=setup_guidance,
        )

    def resolve_sdk_root(self) -> Optional[str]:
        if self._custom_sdk_root is not None:
            if os.path.isdir(self._custom_sdk_root):
                return os.path.abspath(self._custom_sdk_root)
            return None

        candidates = [
            os.environ.get("ANDROID_HOME"),
            os.environ.get("ANDROID_SDK_ROOT"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
            os.path.expanduser("~/Library/Android/sdk"),
            os.path.expanduser("~/Android/Sdk"),
            "/usr/lib/android-sdk",
            "/opt/android-sdk",
        ]
        for c in candidates:
            if c and os.path.isdir(c):
                return os.path.abspath(c)
        return None

    def resolve_adb(self, sdk_root: Optional[str]) -> Tuple[Optional[str], bool, Optional[str]]:
        if self._custom_adb_path is not None:
            if os.path.isfile(self._custom_adb_path):
                path = os.path.abspath(self._custom_adb_path)
                ver = self._get_version(path, ["version"])
                return path, True, ver
            return None, False, None

        env_adb = os.environ.get("ADB_PATH")
        if env_adb and os.path.isfile(env_adb):
            ver = self._get_version(env_adb, ["version"])
            return os.path.abspath(env_adb), True, ver

        if sdk_root:
            exe_name = "adb.exe" if os.name == "nt" else "adb"
            candidate = os.path.join(sdk_root, "platform-tools", exe_name)
            if os.path.isfile(candidate):
                ver = self._get_version(candidate, ["version"])
                return os.path.abspath(candidate), True, ver

        which_adb = shutil.which("adb")
        if which_adb and os.path.isfile(which_adb):
            ver = self._get_version(which_adb, ["version"])
            return os.path.abspath(which_adb), True, ver

        return None, False, None

    def resolve_emulator(self, sdk_root: Optional[str]) -> Tuple[Optional[str], bool, Optional[str]]:
        if self._custom_emulator_path and os.path.isfile(self._custom_emulator_path):
            path = os.path.abspath(self._custom_emulator_path)
            ver = self._get_version(path, ["-version"])
            return path, True, ver

        exe_name = "emulator.exe" if os.name == "nt" else "emulator"
        if sdk_root:
            candidates = [
                os.path.join(sdk_root, "emulator", exe_name),
                os.path.join(sdk_root, "tools", exe_name),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    ver = self._get_version(c, ["-version"])
                    return os.path.abspath(c), True, ver
            if self._custom_sdk_root:
                return None, False, None

        which_emu = shutil.which("emulator")
        if which_emu and os.path.isfile(which_emu):
            ver = self._get_version(which_emu, ["-version"])
            return os.path.abspath(which_emu), True, ver

        return None, False, None

    def resolve_avdmanager(self, sdk_root: Optional[str]) -> Tuple[Optional[str], bool]:
        bat_or_sh = "avdmanager.bat" if os.name == "nt" else "avdmanager"
        if sdk_root:
            candidates = [
                os.path.join(sdk_root, "cmdline-tools", "latest", "bin", bat_or_sh),
                os.path.join(sdk_root, "tools", "bin", bat_or_sh),
            ]
            cmdline_dir = os.path.join(sdk_root, "cmdline-tools")
            if os.path.isdir(cmdline_dir):
                for entry in os.listdir(cmdline_dir):
                    sub = os.path.join(cmdline_dir, entry, "bin", bat_or_sh)
                    if sub not in candidates:
                        candidates.append(sub)

            for c in candidates:
                if os.path.isfile(c):
                    return os.path.abspath(c), True
            if self._custom_sdk_root:
                return None, False

        which_avd = shutil.which("avdmanager")
        if which_avd and os.path.isfile(which_avd):
            return os.path.abspath(which_avd), True

        return None, False

    def resolve_sdkmanager(self, sdk_root: Optional[str]) -> Tuple[Optional[str], bool]:
        bat_or_sh = "sdkmanager.bat" if os.name == "nt" else "sdkmanager"
        if sdk_root:
            candidates = [
                os.path.join(sdk_root, "cmdline-tools", "latest", "bin", bat_or_sh),
                os.path.join(sdk_root, "tools", "bin", bat_or_sh),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    return os.path.abspath(c), True
            if self._custom_sdk_root:
                return None, False

        which_sdk = shutil.which("sdkmanager")
        if which_sdk and os.path.isfile(which_sdk):
            return os.path.abspath(which_sdk), True

        return None, False

    def discover_system_images(self, sdk_root: Optional[str]) -> List[str]:
        if not sdk_root:
            return []
        sys_img_dir = os.path.join(sdk_root, "system-images")
        if not os.path.isdir(sys_img_dir):
            return []

        images: List[str] = []
        try:
            for api_dir in os.listdir(sys_img_dir):
                api_path = os.path.join(sys_img_dir, api_dir)
                if not os.path.isdir(api_path):
                    continue
                for tag_dir in os.listdir(api_path):
                    tag_path = os.path.join(api_path, tag_dir)
                    if not os.path.isdir(tag_path):
                        continue
                    for abi_dir in os.listdir(tag_path):
                        abi_path = os.path.join(tag_path, abi_dir)
                        if os.path.isdir(abi_path):
                            images.append(f"{api_dir};{tag_dir};{abi_dir}")
        except Exception as e:
            logger.warning("Error traversing system-images: %s", e)
        return images

    def resolve_avd_home(self) -> Tuple[str, int]:
        if self._custom_avd_home and os.path.isdir(self._custom_avd_home):
            avd_dir = os.path.abspath(self._custom_avd_home)
        else:
            android_avd_home = os.environ.get("ANDROID_AVD_HOME")
            if android_avd_home and os.path.isdir(android_avd_home):
                avd_dir = os.path.abspath(android_avd_home)
            else:
                user_home = os.path.expanduser("~")
                avd_dir = os.path.join(user_home, ".android", "avd")

        count = 0
        if os.path.isdir(avd_dir):
            try:
                count = len([f for f in os.listdir(avd_dir) if f.endswith(".ini")])
            except Exception:
                count = 0
        return avd_dir, count

    def _get_version(self, executable: str, args: List[str]) -> Optional[str]:
        try:
            res = subprocess.run(
                [executable] + args,
                capture_output=True,
                text=True,
                timeout=3.0,
                shell=False,
            )
            out = res.stdout.strip() or res.stderr.strip()
            first_line = out.split("\n")[0] if out else None
            return first_line
        except Exception:
            return None


class EmulatorSession:
    """Represents a running or launching emulator instance."""

    def __init__(
        self,
        avd_name: str,
        options: EmulatorLaunchOptions,
        pid: Optional[int] = None,
        process: Optional[subprocess.Popen] = None,
    ):
        self.avd_name = avd_name
        self.options = options
        self.pid = pid
        self.process = process
        self.serial: Optional[str] = None
        self.state: AvdStatus = AvdStatus.STARTING
        self.started_at: float = time.time()
        self.boot_completed_at: Optional[float] = None
        self.error_message: Optional[str] = None
        self.boot_task: Optional[asyncio.Task] = None


class AvdManager:
    """
    Central Coordinator for Android Virtual Device management and emulator lifecycle.
    Integrates directly with the DeviceRegistry and respects process safety rules.
    """

    def __init__(
        self,
        sdk_detector: Optional[SdkEnvironmentDetector] = None,
        device_registry: Any = None,
        adb_runner: Optional[Callable[[List[str], float], Tuple[int, str, str]]] = None,
    ):
        self.sdk_detector = sdk_detector or SdkEnvironmentDetector()
        self.device_registry = device_registry
        self._adb_runner = adb_runner or self._default_adb_runner
        self._sessions: Dict[str, EmulatorSession] = {}  # Key: avd_name
        self._mock_avds: Dict[str, AvdConfig] = {}  # For testing offline

    # --- INVENTORY & INSPECTION ---

    def list_avds(self) -> List[AvdConfig]:
        """Discovers all configured AVDs and cross-references active emulator sessions."""
        env = self.sdk_detector.detect_environment()
        avds: Dict[str, AvdConfig] = {}

        # 1. Include registered mock AVDs (if any for testing)
        for name, cfg in self._mock_avds.items():
            avds[name] = cfg.model_copy()

        # 2. Parse physical ~/.android/avd directory
        avd_dir = env.avd_home
        if avd_dir and os.path.isdir(avd_dir):
            try:
                for fname in os.listdir(avd_dir):
                    if fname.endswith(".ini"):
                        avd_name = fname[:-4]
                        ini_path = os.path.join(avd_dir, fname)
                        config = self._parse_avd_ini(avd_name, ini_path)
                        if config:
                            avds[avd_name] = config
            except Exception as e:
                logger.warning("Error reading AVD directory '%s': %s", avd_dir, e)

        # 3. Correlate with running emulator processes and active sessions
        running_emulators = self._detect_running_emulators()

        for name, config in avds.items():
            session = self._sessions.get(name)
            if session:
                config.status = session.state
                config.running_serial = session.serial
                config.pid = session.pid
                config.error_message = session.error_message
            else:
                # Check if an external emulator matches this AVD name
                for serial, emu_avd_name in running_emulators.items():
                    if emu_avd_name == name:
                        config.status = AvdStatus.READY
                        config.running_serial = serial
                        break

        return list(avds.values())

    def get_avd(self, name: str) -> Optional[AvdConfig]:
        for avd in self.list_avds():
            if avd.name == name:
                return avd
        return None

    def add_mock_avd(self, config: AvdConfig) -> None:
        """Register a mock AVD definition for testing."""
        self._mock_avds[config.name] = config

    def clear_mock_avds(self) -> None:
        self._mock_avds.clear()

    # --- CREATION & DELETION ---

    def create_avd(self, req: CreateAvdRequest) -> AvdConfig:
        """Validates inputs and creates an AVD via avdmanager tooling."""
        # 1. Path traversal guard
        if ".." in req.name or "/" in req.name or "\\" in req.name:
            raise ValueError("AVD name cannot contain path separators or relative path tokens.")

        # Validate alphanumeric
        if not AVD_NAME_REGEX.match(req.name):
            raise ValueError(
                f"Invalid AVD name '{req.name}'. Name must contain only alphanumeric characters, underscores, or hyphens (max 64 chars)."
            )

        # 2. Check for duplicate name
        existing = self.get_avd(req.name)
        if existing and not req.force:
            raise ValueError(f"AVD with name '{req.name}' already exists. Use force=True to overwrite.")

        # 3. Environment readiness checks
        env = self.sdk_detector.detect_environment()
        if not env.avdmanager_available:
            raise RuntimeError(
                "Cannot create AVD: 'avdmanager' tool is missing. Install SDK Command-line Tools (cmdline-tools;latest)."
            )

        # 4. Verify system image availability
        if req.system_image not in env.system_images and not self._mock_avds:
            raise RuntimeError(
                f"Required system image '{req.system_image}' is not installed locally. "
                "Download it first via Android SDK Manager or sdkmanager."
            )

        # 5. Build structured command
        cmd = [
            env.avdmanager_path,
            "create",
            "avd",
            "-n",
            req.name,
            "-k",
            req.system_image,
            "-d",
            req.device_profile,
            "-t",
            req.tag,
            "-a",
            req.abi,
        ]
        if req.force:
            cmd.append("--force")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20.0,
                shell=False,
                input="no\n",  # Answer 'no' to custom hardware profile prompt if asked
            )
            if res.returncode != 0:
                err_msg = res.stderr.strip() or res.stdout.strip() or "Unknown error"
                raise RuntimeError(f"avdmanager create failed: {err_msg}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("AVD creation timed out after 20.0 seconds.")

        # Refresh and return created AVD
        created = self.get_avd(req.name)
        if not created:
            # Fallback construct
            created = AvdConfig(
                name=req.name,
                path=os.path.join(env.avd_home or "", f"{req.name}.avd"),
                target=req.system_image,
                abi=req.abi,
                device_profile=req.device_profile,
                tag=req.tag,
                status=AvdStatus.STOPPED,
            )
        return created

    def delete_avd(self, name: str, confirm: bool = False) -> bool:
        """Deletes an AVD with mandatory confirmation."""
        if not confirm:
            raise ValueError(f"Explicit confirmation required to delete AVD '{name}'. Set confirm=True.")

        avd = self.get_avd(name)
        if not avd:
            raise ValueError(f"AVD '{name}' not found.")

        # Safety: Do not delete running emulator
        if avd.status in (AvdStatus.STARTING, AvdStatus.BOOTING, AvdStatus.READY):
            raise RuntimeError(f"Cannot delete AVD '{name}' while it is currently running or booting.")

        # If it's a mock AVD
        if name in self._mock_avds:
            del self._mock_avds[name]
            return True

        env = self.sdk_detector.detect_environment()
        if env.avdmanager_available:
            cmd = [env.avdmanager_path, "delete", "avd", "-n", name]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10.0, shell=False)
                if res.returncode == 0:
                    return True
            except Exception as e:
                logger.warning("avdmanager delete failed: %s", e)

        # Fallback filesystem cleanup
        ini_file = os.path.join(env.avd_home or "", f"{name}.ini")
        avd_folder = os.path.join(env.avd_home or "", f"{name}.avd")
        if os.path.isfile(ini_file):
            try:
                os.remove(ini_file)
            except Exception:
                pass
        if os.path.isdir(avd_folder):
            try:
                shutil.rmtree(avd_folder, ignore_errors=True)
            except Exception:
                pass
        return True

    # --- EMULATOR LIFECYCLE MANAGEMENT ---

    async def launch_emulator(
        self,
        name: str,
        options: Optional[EmulatorLaunchOptions] = None,
    ) -> EmulatorSession:
        """
        Launches an emulator process with strict argument vectors and monitors boot completion.
        """
        options = options or EmulatorLaunchOptions()

        # 1. Duplicate launch prevention
        if name in self._sessions:
            existing = self._sessions[name]
            if existing.state in (AvdStatus.STARTING, AvdStatus.BOOTING, AvdStatus.READY):
                raise ValueError(
                    f"Emulator '{name}' is already running (state={existing.state.value}, pid={existing.pid})."
                )

        avd = self.get_avd(name)
        if not avd:
            raise ValueError(f"AVD '{name}' does not exist.")

        # 2. Tool availability check
        env = self.sdk_detector.detect_environment()
        if not env.emulator_available:
            raise RuntimeError(
                f"Cannot launch emulator: Emulator executable missing. {env.setup_guidance}"
            )

        # 3. Build structured command vector
        cmd = [env.emulator_path, "-avd", name]
        if options.headless:
            cmd.append("-no-window")
        if options.no_snapshot:
            cmd.append("-no-snapshot")
        if options.no_audio:
            cmd.append("-no-audio")
        if options.wipe_data:
            cmd.append("-wipe-data")
        if options.port:
            cmd.extend(["-port", str(options.port)])
        if options.memory_mb:
            cmd.extend(["-memory", str(options.memory_mb)])
        if options.cores:
            cmd.extend(["-cores", str(options.cores)])
        if options.gpu_mode:
            cmd.extend(["-gpu", options.gpu_mode])
        cmd.extend(options.additional_args)

        logger.info("Launching emulator: %s", " ".join(cmd))

        # 4. Spawn process safely
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to spawn emulator process: {e}")

        session = EmulatorSession(
            avd_name=name,
            options=options,
            pid=proc.pid,
            process=proc,
        )
        self._sessions[name] = session

        # 5. Start background boot tracker task
        session.boot_task = asyncio.create_task(self._track_boot_sequence(session))
        return session

    async def stop_emulator(self, name_or_serial: str, force: bool = False) -> bool:
        """
        Gracefully terminates an emulator session via ADB emu kill or controlled SIGTERM.
        """
        session: Optional[EmulatorSession] = None
        target_name = name_or_serial

        # Find session by AVD name or serial
        if name_or_serial in self._sessions:
            session = self._sessions[name_or_serial]
        else:
            for s in self._sessions.values():
                if s.serial == name_or_serial:
                    session = s
                    target_name = s.avd_name
                    break

        if not session:
            # Check if this is an untracked external emulator
            if name_or_serial.startswith("emulator-"):
                return await self._kill_untracked_emulator(name_or_serial)
            return False

        session.state = AvdStatus.STOPPING

        # Attempt 1: ADB emu kill
        if session.serial:
            logger.info("Attempting graceful shutdown for %s via emu kill", session.serial)
            code, _, _ = self._adb_runner(["-s", session.serial, "emu", "kill"], 5.0)
            if code == 0:
                await asyncio.sleep(1.0)

        # Attempt 2: Process terminate
        if session.process and session.process.poll() is None:
            try:
                session.process.terminate()
                for _ in range(10):
                    if session.process.poll() is not None:
                        break
                    await asyncio.sleep(0.3)
            except Exception:
                pass

        # Attempt 3: Force kill if still running
        if session.process and session.process.poll() is None:
            if force or True:
                try:
                    session.process.kill()
                    session.process.wait(timeout=2.0)
                except Exception:
                    pass

        # Clean up session state
        session.state = AvdStatus.STOPPED
        if session.boot_task and not session.boot_task.done():
            session.boot_task.cancel()

        # Reconcile with Device Registry
        if session.serial and self.device_registry:
            dev_id = f"android:{session.serial}"
            dev = self.device_registry.get_device(dev_id)
            if dev:
                self.device_registry.transition_device(dev_id, DeviceLifecycleState.UNAVAILABLE)

        del self._sessions[target_name]
        logger.info("Emulator session '%s' stopped successfully", target_name)
        return True

    async def shutdown_all(self) -> None:
        """Invoked on server shutdown to guarantee zero orphaned emulator processes."""
        names = list(self._sessions.keys())
        for name in names:
            try:
                await self.stop_emulator(name, force=True)
            except Exception as e:
                logger.error("Error shutting down emulator '%s': %s", name, e)

    # --- BOOT TRACKING & REGISTRY RECONCILIATION ---

    async def _track_boot_sequence(self, session: EmulatorSession) -> None:
        """
        Polls ADB for the spawned emulator and monitors sys.boot_completed.
        """
        max_boot_seconds = 120.0
        start_time = time.time()
        session.state = AvdStatus.STARTING

        try:
            # Stage 1: Detect emulator serial in adb devices (up to 45s)
            serial: Optional[str] = None
            while time.time() - start_time < 45.0:
                if session.process and session.process.poll() is not None:
                    # Process died early
                    exit_code = session.process.poll()
                    err = self._read_stderr_snippet(session.process)
                    session.state = AvdStatus.FAILED
                    session.error_message = f"Emulator process crashed with exit code {exit_code}: {err}"
                    logger.error("Emulator crash: %s", session.error_message)
                    return

                serials = self._list_adb_emulator_serials()
                if serials:
                    # Match by checking avd name or picking the newest
                    for s in serials:
                        avd_name = self._get_emulator_avd_name(s)
                        if avd_name == session.avd_name:
                            serial = s
                            break
                    if not serial and serials:
                        serial = serials[0]

                if serial:
                    session.serial = serial
                    session.state = AvdStatus.BOOTING
                    logger.info("Found emulator serial '%s' for AVD '%s'", serial, session.avd_name)
                    break
                await asyncio.sleep(2.0)

            if not serial:
                session.state = AvdStatus.FAILED
                session.error_message = "Timed out waiting for emulator serial to attach to ADB."
                return

            # Stage 2: Monitor sys.boot_completed (up to max_boot_seconds)
            while time.time() - start_time < max_boot_seconds:
                if session.process and session.process.poll() is not None:
                    session.state = AvdStatus.FAILED
                    session.error_message = "Emulator process terminated unexpectedly during boot."
                    return

                code, out, _ = self._adb_runner(["-s", serial, "shell", "getprop", "sys.boot_completed"], 3.0)
                if code == 0 and out.strip() == "1":
                    session.state = AvdStatus.READY
                    session.boot_completed_at = time.time()
                    logger.info(
                        "Emulator '%s' (%s) completed boot in %.1fs",
                        session.avd_name,
                        serial,
                        session.boot_completed_at - session.started_at,
                    )
                    self._register_with_device_registry(session)
                    return

                await asyncio.sleep(2.5)

            session.state = AvdStatus.FAILED
            session.error_message = f"Boot completion timed out after {max_boot_seconds} seconds."

        except asyncio.CancelledError:
            session.state = AvdStatus.STOPPED
        except Exception as e:
            session.state = AvdStatus.FAILED
            session.error_message = str(e)

    def _register_with_device_registry(self, session: EmulatorSession) -> None:
        if not self.device_registry or not session.serial:
            return

        device_id = f"android:{session.serial}"
        virtual_dev = Device(
            id=device_id,
            serial=session.serial,
            provider_id="android_avd",
            platform=DevicePlatform.ANDROID_VIRTUAL,
            device_type=DeviceType.VIRTUAL,
            display_name=f"{session.avd_name} (AVD)",
            manufacturer="Google / Android Virtual Device",
            model=session.avd_name,
            transport=ConnectionTransport.EMULATOR_PIPE,
            state=DeviceLifecycleState.AVAILABLE,
            capabilities=[
                DeviceCapability.DISCOVERY,
                DeviceCapability.SCREEN_STREAM_JPEG,
                DeviceCapability.TOUCH_INTERACTION,
                DeviceCapability.KEYBOARD_INJECTION,
                DeviceCapability.HARDWARE_BUTTONS,
                DeviceCapability.LOGCAT_STREAMING,
                DeviceCapability.VIRTUAL_LIFECYCLE,
            ],
            metadata={
                "avd_name": session.avd_name,
                "pid": session.pid,
                "is_emulator": True,
                "display_resolution": "1080x2400",
            },
        )
        self.device_registry.register_device(virtual_dev)
        logger.info("Registered virtual device '%s' in Device Registry", device_id)

    # --- INTERNAL HELPERS ---

    def _read_ini_properties(self, filepath: str) -> Dict[str, str]:
        props: Dict[str, str] = {}
        if not os.path.isfile(filepath):
            return props
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith(";"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        props[k.strip()] = v.strip()
        except Exception:
            pass
        return props

    def _parse_avd_ini(self, avd_name: str, ini_path: str) -> Optional[AvdConfig]:
        """Parses an AVD .ini file and its companion config.ini."""
        if not os.path.isfile(ini_path):
            return None

        ini_props = self._read_ini_properties(ini_path)
        if not ini_props:
            return None

        avd_path = ini_props.get("path", "")
        if not avd_path or not os.path.isdir(avd_path):
            return AvdConfig(name=avd_name, path=ini_path, status=AvdStatus.STOPPED)

        config_ini = os.path.join(avd_path, "config.ini")
        cfg_props = self._read_ini_properties(config_ini)

        target = cfg_props.get("image.sysdir.1", ini_props.get("target", "Android API"))
        abi = cfg_props.get("abi.type", "x86_64")
        device_profile = cfg_props.get("hw.device.name", cfg_props.get("avd.ini.displayname", "Generic Device"))
        tag = cfg_props.get("tag.id", "google_apis")
        ram_size = cfg_props.get("hw.ramSize", cfg_props.get("hw.ramsize", "2048"))
        heap_size = cfg_props.get("vm.heapSize", cfg_props.get("vm.heapsize", "256"))
        skin = cfg_props.get("skin.name", "")

        return AvdConfig(
            name=avd_name,
            path=avd_path,
            target=target,
            abi=abi,
            device_profile=device_profile,
            tag=tag,
            ram_size=f"{ram_size}MB" if ram_size else None,
            heap_size=f"{heap_size}MB" if heap_size else None,
            skin=skin,
            status=AvdStatus.STOPPED,
        )

    def _detect_running_emulators(self) -> Dict[str, str]:
        """Queries ADB for running emulator serials and their AVD names."""
        emulators: Dict[str, str] = {}
        serials = self._list_adb_emulator_serials()
        for s in serials:
            avd_name = self._get_emulator_avd_name(s)
            if avd_name:
                emulators[s] = avd_name
        return emulators

    def _list_adb_emulator_serials(self) -> List[str]:
        code, out, _ = self._adb_runner(["devices"], 3.0)
        if code != 0:
            return []
        serials = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("List of"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].startswith("emulator-"):
                serials.append(parts[0])
        return serials

    def _get_emulator_avd_name(self, serial: str) -> Optional[str]:
        # Attempt 1: getprop ro.boot.qemu.avd_name
        code, out, _ = self._adb_runner(["-s", serial, "shell", "getprop", "ro.boot.qemu.avd_name"], 3.0)
        name = out.strip()
        if code == 0 and name:
            return name

        # Attempt 2: emu avd name
        code, out, _ = self._adb_runner(["-s", serial, "emu", "avd", "name"], 3.0)
        if code == 0 and out.strip():
            lines = out.strip().splitlines()
            if lines and "OK" not in lines[0]:
                return lines[0].strip()
            if len(lines) > 1:
                return lines[0].strip()
        return None

    async def _kill_untracked_emulator(self, serial: str) -> bool:
        code, _, _ = self._adb_runner(["-s", serial, "emu", "kill"], 5.0)
        return code == 0

    def _read_stderr_snippet(self, proc: subprocess.Popen) -> str:
        if not proc.stderr:
            return ""
        try:
            raw = proc.stderr.read(1024)
            return raw.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

    def _default_adb_runner(self, args: List[str], timeout: float) -> Tuple[int, str, str]:
        env = self.sdk_detector.detect_environment()
        adb_bin = env.adb_path or "adb"
        try:
            res = subprocess.run(
                [adb_bin] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
