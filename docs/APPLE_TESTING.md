# Apple Provider Automated Testing & Verification
**KELVRA Device Lab — Phase 12 Technical Documentation**

## 1. Testing Strategy & Deterministic Isolation

Testing Apple device interactions on a continuous integration runner or developer workstation presents unique challenges:
- Physical iOS devices cannot be guaranteed to be continuously plugged in and unlocked.
- Running tests must not require a live `AppleMobileDeviceService.exe` daemon or real device hardware to achieve 100% deterministic test execution.

To solve this, `AppleEnvironmentDetector` and `AppleDeviceProvider` were engineered with pure dependency injection and environment override parameters:

```python
provider = AppleDeviceProvider(
    custom_lockdown_dir=temp_lockdown_dir,
    custom_tools_dir=temp_tools_dir,
    override_os="Windows",
    override_usbmux_port=mock_port
)
```

This guarantees 100% test reproducibility, zero flakiness, zero real-world hardware coupling, and sub-second test execution.

---

## 2. Test Suite Overview: `tests/test_phase12_apple_provider.py`

The test suite covers 17 dedicated test cases exercising every facet of the Apple integration:

| Test Case Name | Target Component | Verifications Executed |
|---|---|---|
| `test_model_mapper_known_devices` | `AppleDeviceModelMapper` | Correct mapping of iPhone 15 Pro, 14 Pro Max, 16 Pro, iPad Air 5th gen, iPad Pro M4 |
| `test_model_mapper_unknown_fallback` | `AppleDeviceModelMapper` | Graceful fallback formatting for future or unlisted hardware identifiers |
| `test_environment_detector_mocked_inactive` | `AppleEnvironmentDetector` | Proper detection when usbmuxd port is inactive and lockdown directory is missing |
| `test_environment_detector_mocked_active` | `AppleEnvironmentDetector` | Accurate reporting of active usbmuxd socket and parsed lockdown record count |
| `test_provider_discover_devices_no_usbmux` | `AppleDeviceProvider` | Returns empty list when usbmux daemon is offline without throwing exceptions |
| `test_provider_discover_devices_from_lockdown` | `AppleDeviceProvider` | Successfully parses `.plist` records from custom lockdown directory into `Device` models |
| `test_provider_discover_unauthorized_state` | `AppleDeviceProvider` | Correctly flags passcode-locked or trust-pending devices as `UNAUTHORIZED` with guidance |
| `test_provider_connect_and_disconnect` | `AppleDeviceProvider` | Lifecycle transition from `AVAILABLE` to `CONNECTED` and back to `AVAILABLE` |
| `test_provider_disconnect_nonexistent` | `AppleDeviceProvider` | Returns `False` safely when disconnecting unknown UDID |
| `test_provider_get_device_health` | `AppleDeviceProvider` | Returns operational health metrics, pairing state, and roundtrip ping latency |
| `test_provider_capabilities_catalog` | `AppleDeviceProvider` | Validates complete 12-item capability classification catalog |
| `test_api_apple_health_endpoint` | `GET /api/providers/apple/health` | HTTP 200 response with host platform, port status, and lockdown record count |
| `test_api_apple_capabilities_endpoint`| `GET /api/providers/apple/capabilities` | HTTP 200 response with capabilities list matching schema contract |
| `test_api_apple_trust_endpoint_found` | `GET /api/devices/{id}/apple/trust` | Returns accurate trust status and actionable guidance for known Apple device |
| `test_api_apple_trust_endpoint_not_found`| `GET /api/devices/{id}/apple/trust` | Returns 404 Not Found for unregistered device serial |
| `test_api_apple_pair_endpoint` | `POST /api/devices/{id}/apple/pair` | Initiates pairing handshake and returns updated pairing state |
| `test_registry_integration_with_apple` | `DeviceRegistry` + Provider | Seamless integration into global registry alongside Android physical and virtual devices |

---

## 3. Test Execution & Verification

Run the entire automated test suite from the repository root:

```powershell
python -m pytest tests/test_phase12_apple_provider.py -v
```

Execution Results:
```
tests/test_phase12_apple_provider.py::test_model_mapper_known_devices PASSED [  5%]
tests/test_phase12_apple_provider.py::test_model_mapper_unknown_fallback PASSED [ 11%]
tests/test_phase12_apple_provider.py::test_environment_detector_mocked_inactive PASSED [ 17%]
tests/test_phase12_apple_provider.py::test_environment_detector_mocked_active PASSED [ 23%]
tests/test_phase12_apple_provider.py::test_provider_discover_devices_no_usbmux PASSED [ 29%]
tests/test_phase12_apple_provider.py::test_provider_discover_devices_from_lockdown PASSED [ 35%]
tests/test_phase12_apple_provider.py::test_provider_discover_unauthorized_state PASSED [ 41%]
tests/test_phase12_apple_provider.py::test_provider_connect_and_disconnect PASSED [ 47%]
tests/test_phase12_apple_provider.py::test_provider_disconnect_nonexistent PASSED [ 52%]
tests/test_phase12_apple_provider.py::test_provider_get_device_health PASSED [ 58%]
tests/test_phase12_apple_provider.py::test_provider_capabilities_catalog PASSED [ 64%]
tests/test_phase12_apple_provider.py::test_api_apple_health_endpoint PASSED [ 70%]
tests/test_phase12_apple_provider.py::test_api_apple_capabilities_endpoint PASSED [ 76%]
tests/test_phase12_apple_provider.py::test_api_apple_trust_endpoint_found PASSED [ 82%]
tests/test_phase12_apple_provider.py::test_api_apple_trust_endpoint_not_found PASSED [ 88%]
tests/test_phase12_apple_provider.py::test_api_apple_pair_endpoint PASSED [ 94%]
tests/test_phase12_apple_provider.py::test_registry_integration_with_apple PASSED [100%]

============================== 17 passed in 1.48s ==============================
```

Combined Test Suite Verification (Total 120 tests across Phases 7-12):
```powershell
python -m pytest -q
```
Result: **120 passed in 24.91s (100% pass rate)**.
