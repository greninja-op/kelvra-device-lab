# KELVRA Device Lab — Synchronization File Plan

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SYNCHRONIZATION_FILE_PLAN.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Scope Status:** FROZEN & PREPARED (Pending Explicit User Authorization)
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Overview & Synchronization Categorization

To guarantee that integration preparation never results in uncontrolled code mutation, all files across both repositories are classified into three immutable categories:
- **Category A: Standalone Subsystem Files (Device Lab Core):** Remain strictly within `Kelvra/KELVRA Device Lab/`. Never copied or merged into Bench's source tree.
- **Category B: New Bridge Adapters (Bench Side):** New modular integration files planned for Bench's `src/integrations/` directory upon authorized synchronization.
- **Category C: Configuration Updates (Bench Side):** Non-breaking environment variable additions to Bench's configuration loader.
- **Category D: Prohibited Touch-Points:** Files strictly forbidden from modification under any circumstance.

---

## 2. File-by-File Inventory

### Category A: Standalone Subsystem Files (`Kelvra/KELVRA Device Lab/`)
*Action: Retained exclusively in Device Lab repository; zero displacement.*

| Relative Path | Module Role | Action During Sync |
|:---|:---|:---:|
| `src/server.py` | FastAPI REST gateway, WebSocket server, routes | PRESERVE IN PLACE |
| `src/domain_model.py` | Device, lease, state, workflow data models | PRESERVE IN PLACE |
| `src/device_registry.py` | Unified device catalog and thread-safe registry | PRESERVE IN PLACE |
| `src/lifecycle.py` | State machine transitions and listener callbacks | PRESERVE IN PLACE |
| `src/android_provider.py` | Physical Android provider (`adb.exe` lifecycle) | PRESERVE IN PLACE |
| `src/avd_manager.py` | AVD inventory, creation, emulator execution | PRESERVE IN PLACE |
| `src/apple_provider.py` | Apple AMDS `usbmuxd` lockdown provider | PRESERVE IN PLACE |
| `src/screen_streamer.py` | JPEG streaming loop and client session tracking | PRESERVE IN PLACE |
| `src/input_controller.py` | Coordinate translation and input dispatch | PRESERVE IN PLACE |
| `src/session_manager.py` | Single-writer lease arbiter and expirations | PRESERVE IN PLACE |
| `src/automation_engine.py` | Declarative step runner and reporting | PRESERVE IN PLACE |
| `src/artifact_manager.py` | 500 MB quota storage and LRU pruning | PRESERVE IN PLACE |
| `src/recording_manager.py` | `screenrecord` capture lifecycle | PRESERVE IN PLACE |
| `src/logcat_service.py` | Circular buffer (2k) and secret redaction | PRESERVE IN PLACE |
| `src/diagnostics_service.py`| Aggregate hardware and provider telemetry | PRESERVE IN PLACE |
| `static/*` | Vanilla ES6 Studio UI (HTML/CSS/JS) | PRESERVE IN PLACE |
| `tests/*` | 155 pytest test cases (Phases 1-15) | PRESERVE IN PLACE |
| `docs/*` | All architecture and phase documentation | PRESERVE IN PLACE |

---

### Category B: Future Bridge Adapters (`Kelvra/kelvra-bench/src/integrations/`)
*Action: To be authored in Bench ONLY after explicit user authorization in future phase.*

| Planned Target Path | Intended Purpose | Sync Strategy |
|:---|:---|:---|
| `src/integrations/__init__.py` | Package definition for Bench third-party integrations | New file creation |
| `src/integrations/device_lab_bridge.py` | Asynchronous HTTP client wrapping Device Lab REST API | New file creation |
| `src/integrations/device_lab_mcp.py` | Swarm MCP tool definitions exposing mobile tools | New file creation |

---

### Category C: Configuration Updates (`Kelvra/kelvra-bench/`)
*Action: Non-breaking configuration hook additions upon authorization.*

| Target Path | Modification Description | Breaking Change Risk |
|:---|:---|:---:|
| `.env.example` | Add `KELVRA_DEVICE_LAB_ENABLED=false` and `KELVRA_DEVICE_LAB_URL=http://127.0.0.1:8098` | ZERO (Default false) |
| `src/config.py` | Read `KELVRA_DEVICE_LAB_ENABLED` and `KELVRA_DEVICE_LAB_URL` with fallback defaults | ZERO (Additive only) |

---

### Category D: Prohibited Touch-Points (Absolute Do-Not-Touch)
*Action: Strictly forbidden from modification or inspection edits.*

- `Kelvra/kelvra-voice/*` (All files)
- `Kelvra/kelvra-bench/src/voice_*.py`
- `Kelvra/kelvra-bench/src/tts_engine.py`
- `Kelvra/kelvra-bench/src/branch_manager.py`
- `Kelvra/kelvra-bench/src/conflict_engine.py`

---

## 3. Pre-Synchronization Diff Integrity Gate

Prior to executing any file copy or creation during synchronization:
1. `git status` on both repositories must verify clean working trees.
2. An automated diff preview must be reviewed by the operator.
3. Every new bridge file must be verified for zero raw Unicode emojis.
4. No existing files in Bench will be overwritten without explicit approval.
