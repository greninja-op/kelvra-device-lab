# KELVRA Device Lab — Configuration & Dependency Changes

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/CONFIGURATION_AND_DEPENDENCY_CHANGES.md`
- **Subsystem:** KELVRA Device Lab
- **Host Ecosystem:** KELVRA Bench
- **Phase:** Phase 17 — Controlled KELVRA Device Lab Integration
- **Compliance Status:** AUDITED & VERIFIED (Zero Unapproved Dependencies)
- **Zero-Emoji Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Configuration Variable Additions

All configuration changes have been added additively to KELVRA Bench without breaking existing default installations.

### Added Variables in `Kelvra/kelvra-bench/.env.example` & `src/config.py`:

| Variable Name | Type | Default Value | Description |
|:---|:---:|:---:|:---|
| `KELVRA_DEVICE_LAB_ENABLED` | Boolean | `false` | Master feature flag enabling Device Lab integration in Bench UI and MCP gateway. |
| `KELVRA_DEVICE_LAB_URL` | String | `http://127.0.0.1:8098` | Local loopback URL of the standalone KELVRA Device Lab daemon. |
| `KELVRA_DEVICE_LAB_TIMEOUT_MS` | Integer | `5000` | HTTP request timeout in milliseconds for bridge communication. |

### Configuration Fallback Behavior
- If `KELVRA_DEVICE_LAB_ENABLED` is missing from the environment: defaults strictly to `false`.
- If `KELVRA_DEVICE_LAB_URL` is missing: defaults to `http://127.0.0.1:8098`.
- If `KELVRA_DEVICE_LAB_TIMEOUT_MS` is missing: defaults to `5000` ms (5.0s).

---

## 2. Package Dependency Audit

### Runtime Dependencies
Zero new third-party Python packages were added to either repository during Phase 17:
- `httpx` (already required in Bench `>=0.27.0`) is utilized for the asynchronous bridge client.
- `fastapi` and `pydantic` (already core in Bench) are utilized for router request validation.
- Zero copyleft (GPLv3) packages were imported into Bench runtime memory.

### Static Frontend Dependencies
Zero third-party JavaScript libraries or node_modules were introduced:
- `static/js/device_lab_tab.js` uses standard vanilla ES6 DOM APIs.
- `static/css/device_lab_tab.css` uses native CSS custom properties.

---

## 3. Hardware & Machine State Isolation

- **Non-Tracking of Machine State:** Device serials, connected hardware lists, and local USB topology are never tracked as canonical git configuration.
- **Audio & Audio Devices:** Zero modifications were made to `audio_devices.json` or any sound card/microphone hardware configurations.
