# Android Virtual Device (AVD) Testing & Verification

## 1. Overview
The AVD Management subsystem involves low-level operating system processes, binary discovery across differing OS environments, time-dependent boot sequence monitoring, and hardware virtualization engines.

To maintain high continuous integration reliability and adherence to the zero-external-binary-dependency contract, all automated tests must be deterministic, isolated from host state, and capable of executing rapidly without requiring gigabytes of downloaded SDK images.

This document describes the testing architecture, fixture designs, mock isolation strategies, and test coverage metrics for Phase 11.

---

## 2. Test Architecture & Fixtures

The test suite in `tests/test_phase11_avd_management.py` is built around three core fixtures:

```
[ pytest runner ]
       |
       +--> temp_avd_dir : Isolated directory serving as ~/.android/avd
       |
       +--> mock_sdk_dir : Synthetic SDK layout with mock tools
       |                   platform-tools/adb.exe
       |                   emulator/emulator.exe
       |                   cmdline-tools/latest/bin/avdmanager.bat
       |                   system-images/android-34/google_apis/x86_64/
       |
       +--> registry     : Clean DeviceRegistry instance
```

### Deterministic Mock Isolation
To avoid relying on host system PATH or accidentally launching physical host emulators:
1. `SdkEnvironmentDetector` accepts `custom_sdk_root` and `custom_avd_home`.
2. When `custom_sdk_root` is set, `shutil.which` system PATH lookups are strictly disabled.
3. Subprocess executions (`asyncio.create_subprocess_exec`) are intercepted with mock processes that simulate process lifecycle, stdout/stderr streams, and return codes without spawning OS binaries.

---

## 3. Test Coverage Matrix (18 Tests)

| Test Identifier | Category | Verified Behavior |
|---|---|---|
| `test_sdk_unavailable_handling` | Environment | SDK detector returns clean status when directory is empty |
| `test_sdk_detected_with_tools` | Environment | Resolves adb, emulator, avdmanager, system images, and AVD home |
| `test_emulator_executable_unavailable` | Environment | Flags emulator missing while detecting adb and avdmanager |
| `test_empty_avd_inventory` | Inventory | Returns empty list when AVD home directory has no `.ini` files |
| `test_avd_inventory_parsing` | Inventory | Parses root `.ini` and headerless `config.ini`, extracting RAM, ABI, API |
| `test_invalid_avd_configuration` | Inventory | Skips corrupt `.ini` files gracefully without raising unhandled exceptions |
| `test_create_avd_name_validation` | Creation | Rejects traversal characters (`..`, `/`, `\`) and malformed names |
| `test_create_avd_duplicate_prevention`| Creation | Returns 409 Conflict if AVD profile already exists and force=False |
| `test_create_avd_missing_system_image`| Creation | Rejects creation requests when target package is not installed |
| `test_emulator_launch_missing_binary` | Lifecycle | Rejects launch with clean error when emulator binary is unavailable |
| `test_emulator_duplicate_launch_prevention` | Lifecycle | Returns 409 Conflict when attempting to launch already active AVD |
| `test_boot_sequence_and_registry_integration` | Lifecycle | Monitors boot completion and registers device in `DeviceRegistry` as `AVAILABLE` |
| `test_emulator_process_crash_handling` | Lifecycle | Detects premature process exit and transitions session to `ERROR` |
| `test_emulator_shutdown` | Lifecycle | Issues emu kill and SIGTERM, transitioning registry to `UNAVAILABLE` |
| `test_delete_avd_confirmation_required` | Security | Rejects deletion without `confirm=True` query parameter |
| `test_api_avd_environment` | REST API | `GET /api/avd/environment` returns valid status schema |
| `test_api_avd_list_and_get` | REST API | `GET /api/avd/list` and `GET /api/avd/{name}` return AVD configs |
| `test_api_avd_delete_requires_confirmation` | REST API | `DELETE /api/avd/{name}` enforces confirmation parameter |

---

## 4. Test Suite Execution & Results
Full test suite execution across all phases:

```
collected 103 items

tests/test_device_registry.py               [ 13%]  (14 tests passed)
tests/test_domain_model.py                  [ 20%]  (7 tests passed)
tests/test_input_controller.py              [ 23%]  (3 tests passed)
tests/test_lifecycle.py                     [ 28%]  (5 tests passed)
tests/test_phase10_streaming_and_control.py [ 41%]  (14 tests passed)
tests/test_phase11_avd_management.py        [ 59%]  (18 tests passed)
tests/test_phase8_api.py                    [ 66%]  (8 tests passed)
tests/test_phase9_android_provider.py       [ 78%]  (12 tests passed)
tests/test_server.py                        [ 87%]  (9 tests passed)
tests/test_shell.py                         [100%]  (13 tests passed)

============================ 103 passed in 22.32s =============================
```

Pass rate: **100% (103/103 tests passing)**.
Unicode emoji violations: **0 (Strictly enforced by test_zero_unicode_emojis_in_shell_and_assets)**.
