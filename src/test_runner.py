"""
Test Runner for KELVRA Device Lab.
Automates APK installation, smoke testing, and UI verification workflows.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.device_manager import DeviceManager
from src.input_controller import InputController

logger = logging.getLogger("kelvra.device_lab.test_runner")


class StepResult(BaseModel):
    step_name: str
    status: str  # PASSED, FAILED, SKIPPED
    duration_ms: float
    error_message: Optional[str] = None


class TestRunReport(BaseModel):
    __test__ = False
    test_id: str
    serial: str
    package_name: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    overall_status: str = "RUNNING"
    steps: List[StepResult] = []


class TestRunner:
    """Orchestrates test executions and APK validation on target devices."""
    __test__ = False

    def __init__(self, device_manager: DeviceManager, input_controller: InputController):
        self.device_manager = device_manager
        self.input_controller = input_controller
        self._test_reports: Dict[str, TestRunReport] = {}

    def install_apk(self, serial: str, apk_path: str, grant_permissions: bool = True) -> bool:
        """Stream install APK to target device."""
        if not os.path.exists(apk_path) and serial not in self.device_manager._mock_devices:
            logger.error(f"APK file not found: {apk_path}")
            return False

        logger.info(f"Installing APK {apk_path} on {serial}")
        if serial in self.device_manager._mock_devices:
            return True

        args = ["install", "-r"]
        if grant_permissions:
            args.append("-g")
        args.append(apk_path)

        res = self.device_manager.run_adb(args, serial=serial, timeout=60.0)
        return "Success" in res.stdout

    async def run_smoke_test(self, serial: str, package_name: str, activity: Optional[str] = None) -> TestRunReport:
        """Run standard companion smoke test workflow."""
        test_id = f"test-{int(datetime.now(timezone.utc).timestamp()*1000)}"
        report = TestRunReport(
            test_id=test_id,
            serial=serial,
            package_name=package_name
        )
        self._test_reports[test_id] = report

        # Step 1: Force stop previous instances
        t0 = asyncio.get_event_loop().time()
        ok_stop = self.input_controller.stop_app(serial, package_name)
        report.steps.append(StepResult(
            step_name="Stop previous instances",
            status="PASSED" if ok_stop else "FAILED",
            duration_ms=round((asyncio.get_event_loop().time() - t0) * 1000, 2)
        ))

        await asyncio.sleep(0.5)

        # Step 2: Launch application
        t0 = asyncio.get_event_loop().time()
        ok_launch = self.input_controller.launch_app(serial, package_name, activity)
        report.steps.append(StepResult(
            step_name="Launch application",
            status="PASSED" if ok_launch else "FAILED",
            duration_ms=round((asyncio.get_event_loop().time() - t0) * 1000, 2)
        ))

        await asyncio.sleep(1.5)

        # Step 3: Screen capture check
        t0 = asyncio.get_event_loop().time()
        screencap = await asyncio.to_thread(self.input_controller.take_screenshot, serial)
        ok_screen = screencap is not None and len(screencap) > 1000
        report.steps.append(StepResult(
            step_name="Capture screen state",
            status="PASSED" if ok_screen else "FAILED",
            duration_ms=round((asyncio.get_event_loop().time() - t0) * 1000, 2)
        ))

        # Overall Status
        all_passed = all(s.status == "PASSED" for s in report.steps)
        report.overall_status = "PASSED" if all_passed else "FAILED"
        report.completed_at = datetime.now(timezone.utc).isoformat()

        logger.info(f"Smoke test {test_id} finished with status: {report.overall_status}")
        return report

    def get_report(self, test_id: str) -> Optional[TestRunReport]:
        return self._test_reports.get(test_id)
