# Emulator Resource Management & Concurrency Limits

## 1. Overview
Android emulators are high-demand virtualization workloads. Each active instance consumes between 1.5 GB and 4 GB of host RAM, 2 to 4 virtual CPU cores, and several gigabytes of disk write capacity. Running unconstrained virtual devices on a single workstation or server leads to thread starvation, hypervisor lockups, and degraded screen streaming performance.

This document establishes the resource governance framework, concurrency ceilings, memory boundaries, and disk containment strategies enforced by KELVRA Device Lab.

---

## 2. Workstation Sizing & Concurrency Ceilings

To prevent host resource exhaustion, the maximum concurrent running emulators (`MAX_CONCURRENT_EMULATORS`) is budgeted based on host hardware capacity:

| Workstation Spec | Physical RAM | CPU Cores | Recommended Max Emulators | Headless Mode Required |
|---|---|---|---|---|
| **Entry Development Laptop** | 16 GB | 8 Cores / 16 Threads | 1 - 2 | Yes (`-no-window`) |
| **Dedicated Test Bench** | 32 GB | 12 - 16 Cores | 3 - 4 | Recommended |
| **Lab Rackmount Server** | 64+ GB | 24 - 32 Cores | 6 - 8 | Mandatory |

### Enforced Concurrency Guard
When an operator or automated test requests `launch_avd()`:
1. `AvdManager` tallies the count of currently active sessions (`LAUNCHING`, `BOOTING`, or `RUNNING`).
2. If `active_count >= MAX_CONCURRENT_EMULATORS` (default: 4), the launch request is rejected with `429 Too Many Requests` or `503 Service Unavailable`.
3. The response includes an actionable diagnostic detailing which instances are holding compute leases.

---

## 3. Host Memory Allocation Bounds
Each AVD definition requires careful memory sizing:
- **Guest RAM (`hw.ramSize`)**: Bound to a default of `2048 MB` (2 GB). Minimum: `1024 MB`, Maximum: `4096 MB`.
- **Heap Size (`vm.heapSize`)**: Typically `256m` to `512m` depending on Android API level.
- **Host Overhead**: The QEMU hypervisor, SwiftShader renderer, and ADB daemon add an additional ~500 MB to ~800 MB overhead per running process.

Total host memory footprint per instance is approximately `hw.ramSize + 768 MB`.

---

## 4. Virtual Disk Footprint & Pruning
An idle AVD occupies approximately 1.5 GB of disk space. After extended test executions, logcat generation, and APK installations, `userdata.img` can swell past 10 GB.

### Disk Containment Strategies:
1. **Copy-on-Write (CoW)**: Virtual devices link against common base system images in the SDK. The base system image is read-only and shared across all instances.
2. **Ephemeral Cold Boot Option**: The operator can launch with `-wipe-data` or create temporary throwaway virtual devices that are deleted upon test suite completion.
3. **Snapshot Containment**: Disabling quickboot snapshots (`-no-snapshot`) prevents growing RAM state dumps on disk when reproducible cold booting is desired.

---

## 5. CPU Scheduling & Thread Priority
To ensure live screen streaming (Phase 10) and ADB input dispatch remain sub-30ms responsive:
1. Emulators run with normal process priority, while the Device Lab FastAPI/Uvicorn server and video encoding threads run at high scheduling priority.
2. Background test automation batches are throttled to ensure hypervisor threads do not starve audio/video streaming loops.
3. Suppressing boot animations (`-no-boot-anim`) and audio emulation (`-no-audio`) reduces CPU churn by up to 25% during test execution.
