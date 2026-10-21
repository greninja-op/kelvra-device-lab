#!/usr/bin/env python3
"""
KELVRA Device Lab — Production Deployment Pre-Flight Verification Script.
Checks runtime environment, core dependencies, toolchain availability,
network port bindings, and storage filesystem permissions.

Zero Emoji Prohibition Enforced.
"""

import importlib
import os
import shutil
import socket
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class PreFlightCheck:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.results: List[Tuple[str, str, str]] = []  # (Category, Status, Detail)
        self.has_failures = False

    def check_python(self) -> None:
        version = sys.version_info
        ver_str = f"{version.major}.{version.minor}.{version.micro}"
        if version >= (3, 10):
            self.results.append(("Python Version", "PASS", f"Python {ver_str} (>= 3.10 required)"))
        else:
            self.results.append(("Python Version", "FAIL", f"Python {ver_str} is below required 3.10+"))
            self.has_failures = True

    def check_dependencies(self) -> None:
        required_pkgs = ["fastapi", "uvicorn", "websockets", "pydantic", "httpx"]
        missing = []
        for pkg in required_pkgs:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)

        if not missing:
            self.results.append(("Core Dependencies", "PASS", "All required packages installed"))
        else:
            self.results.append(("Core Dependencies", "FAIL", f"Missing packages: {', '.join(missing)}"))
            self.has_failures = True

    def check_adb_toolchain(self) -> None:
        adb_path = shutil.which("adb")
        if adb_path:
            self.results.append(("ADB Toolchain", "PASS", f"Found at: {adb_path}"))
            return

        sdk_candidates = [
            os.environ.get("ANDROID_HOME"),
            os.environ.get("ANDROID_SDK_ROOT"),
            os.path.expanduser("~/AppData/Local/Android/Sdk"),
            os.path.expanduser("~/Android/Sdk"),
        ]
        found_in_sdk = None
        for cand in sdk_candidates:
            if cand and os.path.isdir(cand):
                candidate_adb = Path(cand) / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
                if candidate_adb.is_file():
                    found_in_sdk = str(candidate_adb)
                    break

        if found_in_sdk:
            self.results.append(("ADB Toolchain", "PASS", f"Found in SDK: {found_in_sdk}"))
        else:
            self.results.append(
                ("ADB Toolchain", "WARN", "adb not found in PATH or standard SDK locations (emulation/mock available)")
            )

    def check_port_availability(self, port: int = 8098) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            result = s.connect_ex(("127.0.0.1", port))
            if result != 0:
                self.results.append(("Port Availability", "PASS", f"Port :{port} is free and ready to bind"))
            else:
                self.results.append(
                    ("Port Availability", "WARN", f"Port :{port} is currently bound (service may already be running)")
                )

    def check_directories(self) -> None:
        dirs_to_check = [
            self.root_dir / "artifacts",
            self.root_dir / "artifacts" / "screenshots",
            self.root_dir / "artifacts" / "recordings",
            self.root_dir / "artifacts" / "logs",
            self.root_dir / "artifacts" / "reports",
            self.root_dir / "logs",
            self.root_dir / "static",
        ]
        failed_dirs = []
        for d in dirs_to_check:
            d.mkdir(parents=True, exist_ok=True)
            test_file = d / ".write_test"
            try:
                test_file.write_text("ok", encoding="utf-8")
                test_file.unlink()
            except Exception as e:
                failed_dirs.append(f"{d.name} ({str(e)})")

        if not failed_dirs:
            self.results.append(("Directory Permissions", "PASS", "All required directories writable"))
        else:
            self.results.append(
                ("Directory Permissions", "FAIL", f"Write failed on directories: {', '.join(failed_dirs)}")
            )
            self.has_failures = True

    def run_all(self) -> bool:
        self.check_python()
        self.check_dependencies()
        self.check_adb_toolchain()
        self.check_port_availability()
        self.check_directories()
        return not self.has_failures

    def print_report(self) -> None:
        print("\n==================================================================")
        print(" KELVRA Device Lab - Pre-Flight Deployment Verification Report")
        print("==================================================================")
        for cat, status, detail in self.results:
            status_tag = f"[{status}]"
            print(f" {status_tag:<8} | {cat:<24} | {detail}")
        print("------------------------------------------------------------------")
        overall = "DEPLOYMENT READY" if not self.has_failures else "DEPLOYMENT BLOCKED"
        print(f" OVERALL STATUS: [{overall}]")
        print("==================================================================\n")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    checker = PreFlightCheck(root)
    success = checker.run_all()
    checker.print_report()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
