# Android Virtual Device (AVD) Configuration & Hardware Specification

## 1. Overview
An Android Virtual Device (AVD) defines an emulated hardware profile, software platform image, and storage subsystem operated by QEMU under the Android Emulator.

This document describes the key hardware parameters, ABI compatibility constraints, GPU rendering tiers, and storage layouts configured and inspected by KELVRA Device Lab.

---

## 2. Hardware Specification Parameters

| Property Key | Type | Default Value | Description |
|---|---|---|---|
| `hw.device.name` | String | `pixel_7` | Device profile definition (specifies screen geometry and density) |
| `hw.cpu.arch` | String | `x86_64` | Target processor architecture (`x86_64`, `x86`, `arm64-v8a`) |
| `abi.type` | String | `x86_64` | Android runtime application binary interface |
| `hw.ramSize` | Integer (MB) | `2048` | System RAM assigned to the guest Linux kernel |
| `sdcard.size` | String | `512M` | Size of the virtual external storage FAT32 image |
| `hw.lcd.width` | Integer | (From profile) | Native horizontal display resolution in pixels |
| `hw.lcd.height` | Integer | (From profile) | Native vertical display resolution in pixels |
| `hw.lcd.density` | Integer (DPI) | (From profile) | Display density classification (e.g. 420, 480, 560) |
| `hw.keyboard` | Boolean (`yes`/`no`) | `yes` | Hardware QWERTY keyboard emulation |
| `hw.dPad` | Boolean (`yes`/`no`) | `no` | Emulated directional pad |
| `hw.gpu.enabled` | Boolean (`yes`/`no`) | `yes` | Hardware OpenGL ES acceleration |
| `hw.gpu.mode` | String | `auto` | GPU mode (`auto`, `host`, `swiftshader_indirect`) |

---

## 3. CPU Architectures & Host Hypervisor Matrix

| Host Architecture | Guest AVD ABI | Hypervisor Support | Performance Tier | Recommended Use |
|---|---|---|---|---|
| **x86_64 (Windows/Linux)** | `x86_64` | HAXM / WHPX / KVM | High (Near-native virtualized execution) | Default choice for workstation test benches |
| **x86_64 (Windows/Linux)** | `arm64-v8a` | Dynamic binary translation | Low (Emulated via QEMU TCG, CPU intensive) | Testing ARM-specific native libraries only |
| **ARM64 (Apple Silicon)** | `arm64-v8a` | Hypervisor.framework | High (Near-native virtualized execution) | macOS native test runners |
| **ARM64 (Apple Silicon)** | `x86_64` | Rosetta / Rosetta 2 | Moderate | Legacy compatibility |

Device Lab automatically validates that system images match the host virtualization capabilities to avoid launching sluggish translated images on x86_64 workstations.

---

## 4. Graphics & Display Rendering Subsystem
Device Lab operators frequently run virtual devices in headless or automated server environments where physical displays and dedicated GPUs may not exist. The emulator graphics pipeline is configured via launch options:

- **Host GPU (`-gpu host`)**: Passthrough to the workstation's physical GPU (Direct3D 11, Metal, or OpenGL). Highest fidelity, 60 FPS streaming, but requires an active desktop session and display driver.
- **SwiftShader (`-gpu swiftshader_indirect`)**: Google's CPU-based software renderer. Compatible with headless cloud CI, headless workstation services, and remote headless sessions. Guarantees deterministic rendering without GPU driver crashes.
- **Auto (`-gpu auto`)**: Allows the emulator runtime to detect hardware availability and fall back gracefully.

---

## 5. Storage Partitioning & Disks
An AVD instance folder contains several virtual disk images:
- `system.img.qcow2`: Copy-on-write overlay referencing the read-only SDK base system image.
- `userdata.img`: Ext4 image housing user applications, runtime data, and `/data` partition.
- `sdcard.img`: FAT32 external storage image for simulated media and downloads.
- `snapshots/`: Quickboot snapshots capturing memory states for sub-second resumption (`default_boot`).

When `-wipe-data` is specified during launch, `userdata.img` is cleared and formatted from baseline defaults, preventing inter-test contamination.
