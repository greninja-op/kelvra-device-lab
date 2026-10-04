"""
Automation Engine for KELVRA Device Lab.
Executes controlled, typed mobile automation workflows across connected devices.
Enforces capability validation, step timeouts, cancellation, single-execution concurrency locking,
and detailed execution reporting with artifact generation.
Strictly prohibits arbitrary shell injection or unrestricted script execution.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.artifact_manager import ArtifactManager, ArtifactType
from src.device_registry import DeviceRegistry
from src.domain_model import DeviceLifecycleState, DevicePlatform
from src.input_controller import InputController

logger = logging.getLogger("kelvra.device_lab.automation")


class ActionType(str, Enum):
    WAIT = "WAIT"
    DELAY = "DELAY"
    TAP = "TAP"
    SWIPE = "SWIPE"
    KEY = "KEY"
    TYPE_TEXT = "TYPE_TEXT"
    SCREENSHOT = "SCREENSHOT"
    LAUNCH_APP = "LAUNCH_APP"
    STOP_APP = "STOP_APP"
    ASSERT_STATE = "ASSERT_STATE"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStep(BaseModel):
    step_name: Optional[str] = None
    action: ActionType
    # Action specific parameters
    duration_ms: Optional[int] = 500  # For WAIT, DELAY, SWIPE
    x: Optional[int] = None           # For TAP
    y: Optional[int] = None
    x1: Optional[int] = None          # For SWIPE
    y1: Optional[int] = None
    x2: Optional[int] = None
    y2: Optional[int] = None
    key: Optional[str] = None         # For KEY (e.g. HOME, BACK)
    text: Optional[str] = None        # For TYPE_TEXT
    package: Optional[str] = None     # For LAUNCH_APP, STOP_APP
    activity: Optional[str] = None
    expected_state: Optional[str] = None  # For ASSERT_STATE
    timeout_seconds: float = 10.0
    optional: bool = False             # If True, failure will not abort workflow


class WorkflowDefinition(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    name: str
    description: Optional[str] = ""
    target_device: str
    steps: List[WorkflowStep]
    timeout_seconds: float = 120.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StepExecutionResult(BaseModel):
    step_index: int
    step_name: str
    action: ActionType
    status: str  # PASSED, FAILED, SKIPPED, CANCELLED
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    artifact_id: Optional[str] = None


class WorkflowExecutionReport(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    target_device: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    step_results: List[StepExecutionResult] = Field(default_factory=list)
    error_details: Optional[str] = None
    artifact_id: Optional[str] = None


class AutomationEngine:
    """Orchestrates validation, scheduling, execution, and cancellation of automation workflows."""

    def __init__(
        self,
        device_registry: DeviceRegistry,
        input_controller: InputController,
        artifact_manager: ArtifactManager,
        session_manager=None,
        max_history: int = 50
    ):
        self.device_registry = device_registry
        self.input_controller = input_controller
        self.artifact_manager = artifact_manager
        self.session_manager = session_manager
        self.max_history = max_history

        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecutionReport] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._device_locks: Dict[str, str] = {}  # device_id -> execution_id

    def register_workflow(self, wf: WorkflowDefinition) -> WorkflowDefinition:
        self._workflows[wf.workflow_id] = wf
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionReport]:
        return self._executions.get(execution_id)

    def list_executions(self, device_id: Optional[str] = None, limit: int = 20) -> List[WorkflowExecutionReport]:
        execs = list(self._executions.values())
        if device_id:
            execs = [e for e in execs if e.target_device == device_id or e.target_device.endswith(f":{device_id}")]
        execs.sort(key=lambda e: e.started_at, reverse=True)
        return execs[:limit]

    def validate_workflow(self, wf: WorkflowDefinition) -> Tuple[bool, Optional[str]]:
        """Pre-execution validation checking device existence, authorization, and capability boundaries."""
        if not wf.steps:
            return False, "Workflow must contain at least one step."
        if len(wf.steps) > 50:
            return False, "Workflow exceeds maximum allowed steps (50)."

        dev = self.device_registry.get_device(wf.target_device)
        if not dev:
            raw = wf.target_device.split(":", 1)[1] if ":" in wf.target_device else wf.target_device
            dev = self.device_registry.get_device(f"android:{raw}") or self.device_registry.get_device(f"apple:{raw}")

        if not dev:
            return False, f"Target device '{wf.target_device}' not found in registry."

        if dev.state == DeviceLifecycleState.UNAUTHORIZED:
            return False, f"Target device '{dev.id}' is unauthorized. Physical trust authorization required."
        if dev.state in (DeviceLifecycleState.UNAVAILABLE, DeviceLifecycleState.DISCONNECTED):
            return False, f"Target device '{dev.id}' is offline or disconnected."

        # Platform capability validation
        is_apple = dev.platform in (DevicePlatform.APPLE_PHYSICAL, DevicePlatform.APPLE_VIRTUAL)
        for idx, step in enumerate(wf.steps):
            if is_apple and step.action in (ActionType.TAP, ActionType.SWIPE, ActionType.KEY, ActionType.TYPE_TEXT, ActionType.LAUNCH_APP, ActionType.STOP_APP):
                return False, f"Step {idx + 1} ({step.action.value}) is unavailable on iOS/iPadOS physical devices on Windows host."

            if step.action == ActionType.TAP:
                if step.x is None or step.y is None or step.x < 0 or step.y < 0:
                    return False, f"Step {idx + 1} TAP requires non-negative x and y coordinates."
                w = dev.metadata.get("screen_width") or getattr(dev, "screen_width", None)
                h = dev.metadata.get("screen_height") or getattr(dev, "screen_height", None)
                if w and h:
                    if step.x > w or step.y > h:
                        return False, f"Step {idx + 1} TAP coordinates ({step.x}, {step.y}) exceed screen resolution ({w}x{h})."
            elif step.action == ActionType.SWIPE:
                if any(c is None or c < 0 for c in (step.x1, step.y1, step.x2, step.y2)):
                    return False, f"Step {idx + 1} SWIPE requires non-negative (x1, y1, x2, y2) coordinates."
            elif step.action == ActionType.KEY and not step.key:
                return False, f"Step {idx + 1} KEY requires a key name."
            elif step.action == ActionType.TYPE_TEXT and step.text is None:
                return False, f"Step {idx + 1} TYPE_TEXT requires text content."
            elif step.action in (ActionType.LAUNCH_APP, ActionType.STOP_APP) and not step.package:
                return False, f"Step {idx + 1} {step.action.value} requires package name."

        return True, None

    async def execute_workflow(self, wf: WorkflowDefinition, session_token: Optional[str] = None) -> WorkflowExecutionReport:
        """Executes a validated workflow asynchronously."""
        valid, err = self.validate_workflow(wf)
        if not valid:
            raise ValueError(f"Workflow validation failed: {err}")

        dev = self.device_registry.get_device(wf.target_device)
        raw_serial = dev.serial if dev else (wf.target_device.split(":", 1)[1] if ":" in wf.target_device else wf.target_device)
        device_key = dev.id if dev else f"android:{raw_serial}"

        # Prevent concurrent workflow runs on the same device
        if device_key in self._device_locks:
            active_id = self._device_locks[device_key]
            raise ValueError(f"Device '{device_key}' is busy executing workflow execution '{active_id}'.")

        execution_id = f"exec-{uuid.uuid4().hex[:10]}"
        report = WorkflowExecutionReport(
            execution_id=execution_id,
            workflow_id=wf.workflow_id,
            workflow_name=wf.name,
            target_device=device_key,
            status=ExecutionStatus.RUNNING
        )
        self._executions[execution_id] = report
        self._device_locks[device_key] = execution_id

        # Launch execution runner task
        task = asyncio.create_task(self._run_workflow_task(execution_id, wf, raw_serial, session_token))
        self._active_tasks[execution_id] = task
        return report

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancels an active workflow execution."""
        task = self._active_tasks.get(execution_id)
        report = self._executions.get(execution_id)
        if not task or not report or report.status != ExecutionStatus.RUNNING:
            return False

        logger.info(f"Cancelling workflow execution {execution_id}")
        task.cancel()
        report.status = ExecutionStatus.CANCELLED
        report.completed_at = datetime.now(timezone.utc).isoformat()
        # Release device lock
        self._device_locks.pop(report.target_device, None)
        return True

    async def _run_workflow_task(
        self,
        execution_id: str,
        wf: WorkflowDefinition,
        raw_serial: str,
        session_token: Optional[str]
    ):
        report = self._executions[execution_id]
        t_start = asyncio.get_event_loop().time()
        device_key = report.target_device

        try:
            for idx, step in enumerate(wf.steps):
                step_name = step.step_name or f"Step {idx + 1}: {step.action.value}"
                step_res = StepExecutionResult(
                    step_index=idx,
                    step_name=step_name,
                    action=step.action,
                    status="RUNNING"
                )
                report.step_results.append(step_res)

                step_t0 = asyncio.get_event_loop().time()
                try:
                    await asyncio.wait_for(
                        self._execute_step(step, raw_serial, session_token, step_res),
                        timeout=step.timeout_seconds
                    )
                    step_res.status = "PASSED"
                except asyncio.CancelledError:
                    step_res.status = "CANCELLED"
                    raise
                except Exception as step_err:
                    step_res.status = "FAILED"
                    step_res.error_message = str(step_err)
                    logger.warning(f"Workflow {execution_id} step {idx + 1} failed: {step_err}")

                    if not step.optional:
                        report.status = ExecutionStatus.FAILED
                        report.error_details = f"Failed at step {idx + 1} ({step_name}): {step_err}"
                        break
                finally:
                    step_res.duration_ms = round((asyncio.get_event_loop().time() - step_t0) * 1000, 2)

            if report.status == ExecutionStatus.RUNNING:
                report.status = ExecutionStatus.COMPLETED

        except asyncio.CancelledError:
            report.status = ExecutionStatus.CANCELLED
            report.error_details = "Workflow execution cancelled by operator."
        except Exception as general_err:
            report.status = ExecutionStatus.FAILED
            report.error_details = f"Unexpected execution error: {general_err}"
        finally:
            report.completed_at = datetime.now(timezone.utc).isoformat()
            report.duration_ms = round((asyncio.get_event_loop().time() - t_start) * 1000, 2)
            self._device_locks.pop(device_key, None)
            self._active_tasks.pop(execution_id, None)

            # Save report as automation artifact
            try:
                report_bytes = json.dumps(report.model_dump(), indent=2).encode("utf-8")
                art = self.artifact_manager.save_artifact(
                    name=f"report_{execution_id}.json",
                    artifact_type=ArtifactType.AUTOMATION_REPORT,
                    file_format="json",
                    data=report_bytes,
                    device_id=device_key,
                    metadata={"execution_id": execution_id, "workflow_name": wf.name}
                )
                report.artifact_id = art.artifact_id
            except Exception as e:
                logger.error(f"Failed to save automation report artifact: {e}")

    async def _execute_step(
        self,
        step: WorkflowStep,
        raw_serial: str,
        session_token: Optional[str],
        result: StepExecutionResult
    ):
        if step.action in (ActionType.WAIT, ActionType.DELAY):
            sec = max(0.01, (step.duration_ms or 500) / 1000.0)
            await asyncio.sleep(sec)

        elif step.action == ActionType.TAP:
            ok = self.input_controller.tap(raw_serial, step.x, step.y, session_token=session_token)
            if not ok:
                raise RuntimeError(f"Tap dispatch failed at ({step.x}, {step.y})")

        elif step.action == ActionType.SWIPE:
            ok = self.input_controller.swipe(
                raw_serial,
                step.x1, step.y1, step.x2, step.y2,
                duration_ms=step.duration_ms or 300,
                session_token=session_token
            )
            if not ok:
                raise RuntimeError(f"Swipe dispatch failed from ({step.x1}, {step.y1}) to ({step.x2}, {step.y2})")

        elif step.action == ActionType.KEY:
            ok = self.input_controller.keyevent(raw_serial, step.key, session_token=session_token)
            if not ok:
                raise RuntimeError(f"Keyevent '{step.key}' dispatch failed")

        elif step.action == ActionType.TYPE_TEXT:
            ok = self.input_controller.type_text(raw_serial, step.text or "", session_token=session_token)
            if not ok:
                raise RuntimeError("Text typing dispatch failed")

        elif step.action == ActionType.LAUNCH_APP:
            ok = self.input_controller.launch_app(raw_serial, step.package, step.activity, session_token=session_token)
            if not ok:
                raise RuntimeError(f"Failed to launch app package '{step.package}'")

        elif step.action == ActionType.STOP_APP:
            ok = self.input_controller.stop_app(raw_serial, step.package, session_token=session_token)
            if not ok:
                raise RuntimeError(f"Failed to stop app package '{step.package}'")

        elif step.action == ActionType.SCREENSHOT:
            img_bytes = await asyncio.to_thread(self.input_controller.take_screenshot, raw_serial)
            if not img_bytes:
                raise RuntimeError("Screenshot capture returned empty frame")
            # Save screenshot as artifact
            art = self.artifact_manager.save_artifact(
                name=f"auto_screen_{raw_serial}_{int(asyncio.get_event_loop().time())}.jpeg",
                artifact_type=ArtifactType.SCREENSHOT,
                file_format="jpeg",
                data=img_bytes,
                device_id=f"android:{raw_serial}",
                metadata={"workflow_action": "SCREENSHOT"}
            )
            result.artifact_id = art.artifact_id

        elif step.action == ActionType.ASSERT_STATE:
            dev = self.device_registry.get_device(f"android:{raw_serial}")
            if not dev:
                raise RuntimeError(f"Device '{raw_serial}' disappeared from registry during assertion")
            if step.expected_state and dev.state.value.lower() != step.expected_state.lower():
                raise AssertionError(f"Expected state '{step.expected_state}', got '{dev.state.value}'")
