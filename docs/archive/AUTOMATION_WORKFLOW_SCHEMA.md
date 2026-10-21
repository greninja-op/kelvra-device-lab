# KELVRA Device Lab — Automation Workflow Schema Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/AUTOMATION_WORKFLOW_SCHEMA.md`
- **Subsystem:** Automation & Observability Subsystem
- **Phase:** Phase 13 — Device Automation, Screenshots, Recordings, Logs & Diagnostics
- **Authority:** Declarative Workflow Syntax, Validation Rules & Action Catalog
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Executive Summary

This document specifies the declarative schema for KELVRA Device Lab automation workflows. Workflows are defined as structured JSON manifests comprising metadata and an ordered array of typed action steps. All workflow submissions are validated against strict JSON schema rules and pre-execution device capability checks before execution commences.

---

## 2. Top-Level Workflow Schema (`WorkflowDefinition`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WorkflowDefinition",
  "type": "object",
  "required": ["name", "steps"],
  "properties": {
    "workflow_id": {
      "type": "string",
      "description": "Unique identifier assigned by server or specified by client (format: wf-[a-f0-9]{8})"
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Human-readable label for this automation workflow"
    },
    "description": {
      "type": "string",
      "description": "Optional detailed synopsis of what the workflow exercises"
    },
    "target_device": {
      "type": "string",
      "description": "Target device serial or canonical ID (e.g. 'android:emulator-5554')"
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/WorkflowStep" }
    }
  }
}
```

---

## 3. Action Step Catalog (`WorkflowStep`)

### 3.1 `WAIT` / `DELAY`
Pauses workflow execution for a specified duration in milliseconds.
```json
{
  "step_name": "Settle animation",
  "action": "WAIT",
  "duration_ms": 1000
}
```

### 3.2 `TAP`
Injects a single touch down/up event at specified screen coordinates. Coordinates are bounds-checked against device resolution.
```json
{
  "step_name": "Click primary login button",
  "action": "TAP",
  "x": 540,
  "y": 1800
}
```

### 3.3 `SWIPE`
Executes a linear touch swipe from `(x1, y1)` to `(x2, y2)` over `duration_ms`.
```json
{
  "step_name": "Scroll down feed",
  "action": "SWIPE",
  "x1": 500,
  "y1": 1600,
  "x2": 500,
  "y2": 400,
  "duration_ms": 300
}
```

### 3.4 `KEY`
Injects an Android hardware keycode or key label (`HOME`, `BACK`, `APP_SWITCH`, `POWER`, `VOLUME_UP`, `VOLUME_DOWN`, `ENTER`).
```json
{
  "step_name": "Navigate to Home Screen",
  "action": "KEY",
  "key": "HOME"
}
```

### 3.5 `TYPE_TEXT`
Injects text characters into the currently focused text input field. Control characters are escaped for shell safety.
```json
{
  "step_name": "Type search query",
  "action": "TYPE_TEXT",
  "text": "kelvra device lab"
}
```

### 3.6 `LAUNCH_APP`
Starts an application package and optional activity.
```json
{
  "step_name": "Open System Settings",
  "action": "LAUNCH_APP",
  "package": "com.android.settings",
  "activity": ".Settings"
}
```

### 3.7 `STOP_APP`
Forcefully terminates an application package to reset state.
```json
{
  "step_name": "Force stop Settings",
  "action": "STOP_APP",
  "package": "com.android.settings"
}
```

### 3.8 `SCREENSHOT`
Captures a static verification frame and archives it as a tracked artifact in `artifacts/screenshots/`.
```json
{
  "step_name": "Capture post-login verification frame",
  "action": "SCREENSHOT"
}
```

### 3.9 `ASSERT_STATE`
Verifies that the target device's FSM lifecycle state matches expectations.
```json
{
  "step_name": "Verify device remains available",
  "action": "ASSERT_STATE",
  "expected_state": "available"
}
```

---

## 4. Complete Workflow Manifest Example

```json
{
  "name": "SmokeVerificationSuite",
  "description": "Standard Android physical smoke test exercising home screen, navigation, and visual verification.",
  "target_device": "android:MOCK_P13_01",
  "steps": [
    {
      "step_name": "Wake and Go Home",
      "action": "KEY",
      "key": "HOME",
      "timeout_seconds": 5
    },
    {
      "step_name": "Pause UI Settle",
      "action": "WAIT",
      "duration_ms": 500
    },
    {
      "step_name": "Capture Baseline Frame",
      "action": "SCREENSHOT"
    },
    {
      "step_name": "Launch Target Application",
      "action": "LAUNCH_APP",
      "package": "com.android.settings"
    },
    {
      "step_name": "Wait For Activity Displayed",
      "action": "WAIT",
      "duration_ms": 1200
    },
    {
      "step_name": "Capture App Running Evidence",
      "action": "SCREENSHOT"
    },
    {
      "step_name": "Clean Up Application",
      "action": "STOP_APP",
      "package": "com.android.settings"
    },
    {
      "step_name": "Assert Device Status",
      "action": "ASSERT_STATE",
      "expected_state": "available"
    }
  ]
}
```
