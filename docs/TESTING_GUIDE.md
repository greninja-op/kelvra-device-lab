# KELVRA Device Lab — Testing Guide & Verification Suite

## 1. Test Architecture Overview

KELVRA Device Lab maintains a deterministic, high-coverage automated test suite powered by `pytest` and FastAPI `TestClient`. Tests are partitioned across dedicated test files targeting individual subsystem responsibilities without inter-test side effects.

---

## 2. Test File Inventory

| Test Module | Test Focus | Count | Key Assertions |
| :--- | :--- | :--- | :--- |
| `tests/test_domain_model.py` | Typed Domain Model | 6 | Composite ID validation, empty serial rejection, capability manipulation, serialization |
| `tests/test_lifecycle.py` | Connection Lifecycle FSM | 5 | Valid transitions, invalid transition exceptions, timestamps, error attachment/clearance |
| `tests/test_device_registry.py` | Central Device Registry | 5 | Provider registration, reconciliation, disappearance detection, connection flow, thread safety |
| `tests/test_android_discovery.py` | Android Discovery Engine | 5 | ADB output parsing, authorized/unauthorized/offline handling, Wi-Fi and emulator detection |
| `tests/test_phase8_api.py` | Phase 8 REST Endpoints | 8 | List devices, state/search filters, composite ID lookup, connect/disconnect lifecycle, stats |
| `tests/test_server.py` | FastAPI Server Core | 10 | Health check, telemetry, screenshots, input injection, smoke tests |
| `tests/test_shell.py` | Shell & SPA Integration | 20 | Static asset routing, SPA fallbacks, template integrity |

**Total Verified Tests:** 59 passing tests.

---

## 3. Running the Test Suite

From the project root (`Kelvra/KELVRA Device Lab/`), run:

```bash
# Run all tests quietly
pytest -q

# Run with verbose output
pytest -v

# Run only Phase 8 specific tests
pytest tests/test_domain_model.py tests/test_lifecycle.py tests/test_device_registry.py tests/test_android_discovery.py tests/test_phase8_api.py -v
```

---

## 4. Test Isolation Guarantees

- **No Physical Hardware Dependency:** All test suites run completely offline using `MockDeviceProvider` and mocked subprocess pipes (`unittest.mock.patch`).
- **Concurrent Safety:** All fixtures perform clean teardown after each test run, ensuring no orphaned state in `DeviceRegistry` or `DeviceManager`.
- **Zero Emoji Compliance:** The test suite and its fixtures adhere strictly to the zero emoji prohibition rule.
