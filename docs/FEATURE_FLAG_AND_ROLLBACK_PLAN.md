# KELVRA Device Lab — Feature Flag & Rollback Runbook

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/FEATURE_FLAG_AND_ROLLBACK_PLAN.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 16 — Integration Preparation & Controlled Synchronization
- **Rollback Complexity:** ZERO DOWNTIME / ZERO CODE REVERSION
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Feature Flag Architecture

Integration between KELVRA Bench and KELVRA Device Lab is completely governed by declarative runtime environment variables:

```bash
# In Kelvra/kelvra-bench/.env
KELVRA_DEVICE_LAB_ENABLED=false
KELVRA_DEVICE_LAB_URL=http://127.0.0.1:8098
KELVRA_DEVICE_LAB_TIMEOUT_MS=5000
```

### Runtime Flag States

| Flag Value | Bench Subsystem Behavior | Device Lab Subsystem Behavior |
|:---|:---|:---|
| `false` (Default) | Mobile Fleet UI tabs hidden; Mobile MCP tools unregistered; zero network polling to `:8098`. | Unaffected. Device Lab runs autonomously on `:8098` for direct teleoperation. |
| `true` (Active) | Mobile Fleet UI visible; MCP tools registered in Swarm Gateway; background fleet health monitoring enabled. | Receives RPC requests and test execution runs from Bench agents; publishes events to `:8099/api/events`. |

---

## 2. Graceful Degradation & Resilience Posture

If `KELVRA_DEVICE_LAB_ENABLED=true` but the Device Lab service is offline, stopped, or experiencing network partition:

```
[ Bench UI / Agent ] ---> GET /api/devices (via Bridge)
                                  |
                                  v
                        [ Connection Refused (:8098) ]
                                  |
                                  +--> CATCH: httpx.ConnectError
                                  |
                                  +--> Log WARNING (Non-fatal)
                                  |
                                  v
                   [ Graceful UI Empty State ]
         "Device Lab is offline. Launch via run_app.bat"
```

1. **Zero Unhandled Exceptions:** The Bench bridge intercepts connection timeouts and refused connections, returning structured `ServiceUnavailable` responses.
2. **Honest Empty State:** Bench renders an informative notification banner:
   `"Device Lab service is not running on http://127.0.0.1:8098. Launch Device Lab via run_app.bat or start the background daemon."`
3. **Agent Non-Failure:** Swarm agents attempting to invoke mobile MCP tools receive a descriptive error string: `"DEVICE_LAB_UNREACHABLE: Service on port 8098 is offline"`, allowing LLM planning to branch gracefully or skip mobile test cards without crashing the swarm.

---

## 3. Emergency Instant Rollback Runbook

If any unforeseen incompatibility, memory leak, or behavioral anomaly occurs after synchronization:

### Step 1: Disable Feature Flag
Modify `Kelvra/kelvra-bench/.env`:
```bash
KELVRA_DEVICE_LAB_ENABLED=false
```

### Step 2: Reload Bench Configuration
Trigger Bench configuration reload via API or restart the Bench server:
```powershell
# From Kelvra/kelvra-bench/
python -m src.cli serve
```

### Step 3: Verify Subsystem Isolation
1. Confirm Bench UI launches cleanly without Mobile Fleet tabs.
2. Verify Device Lab continues running independently:
   ```powershell
   # In Kelvra/KELVRA Device Lab/
   python -m src.server
   ```
3. Open `http://localhost:8098` in browser to confirm full standalone teleoperation is 100% intact.

---

## 4. Disaster Recovery & Clean Decoupling

Because Approach 4 uses a decoupled adapter design, rolling back does NOT require:
- Reverting git commits.
- Git resetting branches.
- Cleaning up foreign source files in core Bench modules.
- Reinstalling Python virtual environments.

The decoupling is clean, instant, and completely deterministic.
