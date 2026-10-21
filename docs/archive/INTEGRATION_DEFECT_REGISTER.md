# INTEGRATION_DEFECT_REGISTER.md
# KELVRA Device Lab — Phase 18 Integration Defect Register

## 1. Defect Classification Hierarchy
- **P0**: Critical security vulnerability, data loss, process crash, or system integrity violation.
- **P1**: Major functional breakdown or unhandled failure in core workflows.
- **P2**: Significant but recoverable defect with available workaround.
- **P3**: Minor usability, formatting, polish, or non-critical issue.

## 2. Defect Log

### DEF-01: Bridge Offline Exception Uncaught on Windows 3.13 Loopback
- **Severity**: P2 (Recoverable network error)
- **Affected Module**: `kelvra-bench/src/integrations/device_lab_bridge.py`
- **Reproduction**: When querying an unreachable loopback port (`127.0.0.1:59999`) on Windows, HTTPX threw `ConnectTimeout` or `NetworkError` in addition to `ConnectError`.
- **Expected Behavior**: All network connection failure classes caught and translated into structured `offline` status.
- **Actual Behavior**: Previously only `ConnectError` was explicitly caught, leaving timeout variants unhandled.
- **Root Cause**: Windows socket connection rejection timing differences in Python 3.13.
- **Fix**: Expanded exception handling tuple to `(httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.NetworkError)`.
- **Regression Test**: `test_offline_service_handling`, `test_offline_list_devices`.
- **Status**: `RESOLVED & VERIFIED`

### DEF-02: Router Test Prefix Path Assertion
- **Severity**: P3 (Test suite assertion)
- **Affected Module**: `kelvra-bench/tests/test_device_lab_integration.py`
- **Reproduction**: Route path assertions evaluated relative paths (`/health`) instead of full router prefixed paths (`/api/device-lab/health`).
- **Expected Behavior**: Assertion inspects full prefixed route paths matching APIRouter configuration.
- **Actual Behavior**: Assertion failed on missing `/health` in router paths.
- **Root Cause**: `APIRouter(prefix="/api/device-lab")` prefixes route strings internally.
- **Fix**: Updated assertions to match `/api/device-lab/*` paths.
- **Regression Test**: `test_server_routes_registered`.
- **Status**: `RESOLVED & VERIFIED`

## 3. Summary of Open Defects
- **P0 Defects**: 0
- **P1 Defects**: 0
- **P2 Defects**: 0
- **P3 Defects**: 0

**Total Open Defects**: 0
