# KELVRA Device Lab — Integration Strategy & Architecture Evaluation

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/INTEGRATION_STRATEGY.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Selection Decision:** Approach 4 — Hybrid Out-of-Process Adapter Architecture
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Architectural Strategy Trade-Off Analysis

To integrate KELVRA Device Lab into the broader KELVRA Bench swarm ecosystem, four potential architectural integration approaches were formally evaluated against five core criteria:
1. **System Stability & Blast Radius:** Ability to prevent failures in device automation (e.g. adb hangs, USB disconnects) from crashing Bench.
2. **Standalone Teleoperation Parity:** Guarantee that Device Lab remains 100% usable as an independent tool on `:8098`.
3. **Toolchain & Dependency Isolation:** Avoidance of polluting Bench with Android SDK/ADB/Pillow dependencies.
4. **Agent Orchestration Synergies:** Ease with which Swarm agents (Scout, QA, Reviewer) can invoke mobile automation tools.
5. **Rollback & Deployment Simplicity:** Speed and safety of enabling, disabling, or reverting the integration.

---

## 2. Comparative Evaluation Matrix

| Criterion | Approach 1: Monolithic Merge | Approach 2: Git Subtree/Submodule | Approach 3: Detached Microservice | Approach 4: Hybrid Out-of-Process Adapter |
|:---|:---:|:---:|:---:|:---:|
| **Blast Radius Isolation** | POOR (Shared process/loop) | MODERATE (Shared code tree) | HIGH (Network separated) | **EXCELLENT (Loopback IPC & process guard)** |
| **Standalone Parity** | FAILED (Merged into monolith) | PARTIAL (Complex dual-mode) | EXCELLENT (Always independent) | **PERFECT (100% standalone preserved)** |
| **Dependency Hygiene** | POOR (All deps merged in Bench) | POOR (Pollutes Bench pip env) | EXCELLENT (Separate requirements) | **EXCELLENT (Dual or unified venv support)** |
| **Agent Tool Usability** | HIGH (Direct function calls) | HIGH (Direct imports) | MODERATE (HTTP client required) | **HIGH (Lightweight MCP bridge)** |
| **Rollback Simplicity** | DANGEROUS (High code diff) | COMPLEX (Submodule tracking) | EASY (Network disconnect) | **INSTANT (Single feature-flag toggle)** |
| **UI Docking Cohesion** | SEAMLESS | SEAMLESS | FRAGMENTED (Separate tabs) | **SEAMLESS (Anthropic design parity dock)** |
| **Overall Rank** | Rejected (4th) | Rejected (3rd) | Viable (2nd) | **SELECTED (1st - Recommended)** |

---

## 3. Rationale for Approach 4: Hybrid Adapter Architecture

### 3.1 Structural Topology
Under Approach 4, KELVRA Device Lab operates as an autonomous daemon service bound to port `:8098`. KELVRA Bench (`:8099`) communicates with Device Lab through a dedicated, lightweight integration adapter:

```
[ Developer / QA Operator ]
             |
             +-----------------------+
             |                       |
             v                       v
    [ KELVRA Bench UI ]     [ Device Lab Studio UI ]
         (:8099)                 (:8098)
             |                       |
             | (Embedded Dock / Tab) |
             +---------------------->+
             |
    [ Swarm Orchestrator ]
             |
             v (HTTP / WS / MCP)
    [ BenchDeviceBridge ] <----+
             |                 |
             v (REST / JSON)   | (EventBus Webhook)
    [ Device Lab Server ] -----+
         (:8098)
             |
      +------+------+
      |             |
      v             v
 [ Android ADB ] [ Apple usbmuxd ]
      |             |
 [ Physical / AVD Mobile Fleet ]
```

### 3.2 Architectural Benefits
1. **Zero Monolithic Contamination:** Bench's core event loop and Swarm execution engine are completely decoupled from OS device drivers, ADB daemon restarts, and USB disconnection spikes.
2. **Dual-Mode Operation:** Developers can launch Device Lab directly as a standalone development tool (`Kelvra/KELVRA Device Lab/`) or seamlessly inside the full KELVRA Bench studio.
3. **License & Boundary Segregation:** Apple integration relies on `usbmuxd` and external tooling without GPLv3 contamination inside Bench.
4. **Deterministic Feature-Flag Gating:** A single environment setting (`KELVRA_DEVICE_LAB_ENABLED=true/false`) enables or disables all mobile tabs and MCP tools in Bench with zero restart penalty.

---

## 4. Subsystem Governance & Responsibilities

| Responsibility Domain | Sole Owner | Delegated / Collaborative Interface |
|:---|:---:|:---|
| **Swarm Task Dispatch & Kanban Cards** | KELVRA Bench | Bench dispatches test tasks to Device Lab via `POST /api/automation/execute-inline` |
| **Human Approval & Review Gates** | KELVRA Bench | Bench prompts user before destructive APK installs or device wipes |
| **Physical & Virtual Fleet Discovery** | KELVRA Device Lab | Device Lab continuously polls hardware and reports fleet changes via EventBus |
| **Touch/Key Input Injection & Leases** | KELVRA Device Lab | Device Lab validates normalized coordinates and enforces single-writer leases |
| **Screen Streaming Pipeline** | KELVRA Device Lab | Device Lab streams frames at up to 30 FPS over JPEG WebSockets |
| **Artifact Generation & Eviction** | KELVRA Device Lab | Device Lab saves screenshots/recordings/reports, pruned under 500 MB quota |

---

## 5. Strategy Implementation Roadmap (Post-Authorization)

Upon explicit user authorization in future phases:
1. **Bridge Adapter Registration:** Introduce `src/integrations/device_lab_bridge.py` in Bench to manage HTTP/WS communication to `http://127.0.0.1:8098`.
2. **EventBus Forwarding:** Configure Device Lab's `EventPublisher` to push fleet updates to Bench's `POST /api/events`.
3. **MCP Tool Catalog Expansion:** Register mobile automation tools (`mobile_tap`, `mobile_screenshot`, `mobile_run_smoke_test`) in Bench's Swarm Tool Gateway.
4. **UI Viewport Embedding:** Add a native "Mobile Fleet" workspace tab in Bench embedding Device Lab's Anthropic-themed studio viewport.
