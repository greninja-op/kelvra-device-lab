# KELVRA Device Lab — KELVRA Bench Integration Contract

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/BENCH_INTEGRATION_CONTRACT.md`
- **Subsystem:** KELVRA Device Lab
- **Host System:** KELVRA Bench (`Kelvra/kelvra-bench/`)
- **Phase:** Phase 3 — System Architecture, Technical Decisions & Engineering Blueprint
- **Integration Target Phase:** Phase 8 (Deferred until explicit user authorization)
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Integration Boundary & Governance Model

During Phases 1 through 7, KELVRA Device Lab operates as an independent standalone service. 

When integrated into KELVRA Bench in Phase 8:
- **Bench Remains the Master Orchestrator:** KELVRA Bench (`:8099`) owns global agent dispatch, Kanban card workflows, worktree lifecycle, and global authentication tokens (`kbt-` tokens).
- **Device Lab Remains the Hardware Authority:** Device Lab (`:8098`) owns mobile device discovery, screen streaming pipelines, touch coordinate translation, and physical telemetry collection.
- **Zero Monolithic Merging:** Device Lab will not be blindly pasted into Bench's source tree. Integration occurs via clean REST/WebSocket protocols and EventBus message publishing.

```mermaid
flowchart TD
    subgraph BenchControlRoom ["KELVRA Bench (:8099)"]
        SWARM_ORCH["Swarm Orchestrator (Scout/QA)"]
        EVENT_BUS["Canonical EventBus (/api/events)"]
        BENCH_UI["Bench Desktop Shell (Tauri / Vite)"]
        AUTH_MGR["Auth Manager (kbt- Tokens)"]
    end

    subgraph BenchBridgeLink ["Integration Link (src/bench_bridge.py)"]
        REST_CLIENT["HTTP REST Client"]
        EVENT_PUB["Fire-and-Forget Event Publisher"]
    end

    subgraph DeviceLabSubsystem ["KELVRA Device Lab (:8098)"]
        API_LAYER["FastAPI Server & Route Gateway"]
        DEV_MGR["Device Manager & State Machine"]
        STREAM_ENG["Screen Streaming Engine"]
        TEST_RUNNER["Autonomous Test Runner"]
    end

    subgraph MobileFleet ["Connected Hardware Fleet"]
        MOBILE_DEV["Physical & Virtual Android Devices"]
    end

    SWARM_ORCH -->|1. Dispatch Test Run (HTTP)| REST_CLIENT
    REST_CLIENT -->|2. POST /api/devices/{serial}/tests/run| API_LAYER
    API_LAYER --> TEST_RUNNER
    TEST_RUNNER --> MOBILE_DEV
    TEST_RUNNER -->|3. Publish Test Result & Screenshots| EVENT_PUB
    EVENT_PUB -->|4. POST /api/events (SWARM_EVENT)| EVENT_BUS
    EVENT_BUS -->|5. Update Kanban Card| SWARM_ORCH
    BENCH_UI <-->|6. Embedded Viewport (/devices)| API_LAYER
    AUTH_MGR -->|Validate Token| API_LAYER
```

---

## 2. EventBus Integration Contract

Device Lab publishes structured events directly to KELVRA Bench's durable event store via `POST http://127.0.0.1:8099/api/events`.

### Event Schema
```json
{
  "event_type": "DEVICE_TEST_COMPLETED",
  "source": "kelvra-device-lab",
  "correlation_id": "card-4819-mobile-smoke",
  "payload": {
    "serial": "8TCABAIFWOZTDICI",
    "device_model": "POCO X6 Pro 5G",
    "platform": "android_physical",
    "test_suite": "CompanionAppSmokeTest",
    "status": "PASSED",
    "duration_ms": 4250,
    "checkpoints": [
      { "name": "app_launched", "status": "PASS", "screenshot_path": "artifacts/evidence/chk_01.png" },
      { "name": "mic_permission_granted", "status": "PASS", "screenshot_path": "artifacts/evidence/chk_02.png" }
    ],
    "telemetry": {
      "battery_pct": 84,
      "temperature_c": 33.2
    }
  },
  "timestamp": "2026-10-04T00:51:30Z"
}
```

### Event Types Published
- `DEVICE_DISCOVERED`
- `DEVICE_DISCONNECTED`
- `DEVICE_UNAUTHORIZED`
- `DEVICE_THERMAL_ALERT`
- `DEVICE_TEST_STARTED`
- `DEVICE_TEST_COMPLETED`
- `DEVICE_TEST_FAILED`

---

## 3. Tool Gateway & MCP Integration

KELVRA Bench exposes Model Context Protocol (MCP) tools to LLM swarm agents (Scout, QA, Reviewer). Device Lab registers a lightweight MCP adapter exposing device operations as structured tool calls:

```json
{
  "name": "mobile_device_tap",
  "description": "Tap a normalized coordinate on the connected mobile device screen.",
  "parameters": {
    "type": "object",
    "properties": {
      "serial": { "type": "string" },
      "x": { "type": "number", "description": "Normalized X coordinate (0.0 - 1.0)" },
      "y": { "type": "number", "description": "Normalized Y coordinate (0.0 - 1.0)" }
    },
    "required": ["serial", "x", "y"]
  }
}
```
Tools exposed to Bench agents:
- `mobile_list_devices`
- `mobile_get_telemetry`
- `mobile_device_tap`
- `mobile_device_swipe`
- `mobile_device_key`
- `mobile_device_type`
- `mobile_capture_screenshot`
- `mobile_install_apk`
- `mobile_run_smoke_test`

---

## 4. UI Docking Topology

When the user navigates to the **Devices** tab in KELVRA Bench:
1. Bench's desktop shell (Tauri/Vite) loads Device Lab's interface via an embedded sub-view pointing to `http://127.0.0.1:8098/`.
2. Because Device Lab adheres strictly to the verified KELVRA Bench design contract (`#262624`, `#1E1E1C`, `#D97757`, Lora, Inter, JetBrains Mono), the interface renders seamlessly as a native workspace pane without visual discordance.
3. If Device Lab is not running, Bench displays an honest empty state with a "Launch Device Lab" action button.
