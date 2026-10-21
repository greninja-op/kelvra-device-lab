# Android Virtual Device (AVD) Inventory & Discovery

## 1. Overview
Android Virtual Devices are represented on the host system as pairs of files and directories within the AVD Home directory (`~/.android/avd` or `ANDROID_AVD_HOME`):
1. A root definition file: `<name>.ini`
2. A device instance directory: `<name>.avd/` containing runtime disks, snapshots, and `config.ini`.

This document specifies the discovery, parsing, validation, and serialization pipeline used by KELVRA Device Lab to build an active in-memory AVD inventory.

---

## 2. Directory Layout & Storage Structure
```
~/.android/avd/
  ├── Pixel_7_API_34.ini
  ├── Pixel_7_API_34.avd/
  │   ├── config.ini
  │   ├── hardware-qemu.ini
  │   ├── sdcard.img
  │   ├── userdata.img
  │   └── snapshots/
  ├── Medium_Phone_API_33.ini
  └── Medium_Phone_API_33.avd/
      └── config.ini
```

### Root Definition File (`<name>.ini`)
The root `.ini` file acts as the primary pointer to the device payload directory. It typically contains two keys:
```ini
avd.ini.encoding=UTF-8
path=C:\Users\User\.android\avd\Pixel_7_API_34.avd
path.rel=avd/Pixel_7_API_34.avd
target=android-34
```

### Instance Configuration File (`config.ini`)
Inside `<name>.avd/config.ini`, the complete virtual hardware specification is defined:
```ini
AvdId=Pixel_7_API_34
PlayStore.enabled=false
abi.type=x86_64
hw.accelerometer=yes
hw.cpu.arch=x86_64
hw.device.name=pixel_7
hw.ramSize=2048
hw.sdCard=yes
image.sysdir.1=system-images/android-34/google_apis/x86_64/
sdcard.size=512M
skin.name=pixel_7
tag.display=Google APIs
tag.id=google_apis
```

---

## 3. Headerless INI Parsing Protocol
Android `.ini` files do **not** conform to the standard Windows INI specification because they lack section headers (`[SectionName]`). Standard parsers (such as Python's `configparser.ConfigParser`) throw `MissingSectionHeaderError` when reading these files directly.

Device Lab implements a specialized, headerless key-value parser (`_read_ini_properties`):
1. Reads lines using UTF-8 encoding (falling back to latin-1 on decode failure).
2. Strips leading and trailing whitespace.
3. Skips comment lines beginning with `#` or `;`.
4. Splits strictly on the first `=` delimiter into key and value.
5. Strips surrounding quotes if present.
6. Returns an in-memory dictionary of string properties.

---

## 4. Extraction & Normalization Pipeline
When `AvdManager.list_avds()` is invoked:
1. The AVD home directory is scanned for all `*.ini` files.
2. For each `.ini` file:
   - The base name without extension is extracted as candidate AVD name.
   - The file is parsed to extract the `path` attribute.
   - If `path` is relative, it is resolved against the parent directory of the `.ini` file.
   - If the target `.avd` directory does not exist or lacks `config.ini`, the candidate is flagged as corrupted or skipped with a warning log.
   - `config.ini` is parsed to extract hardware parameters:
     - Target API level (e.g. parsed from `image.sysdir.1` or root `target`).
     - CPU ABI (`abi.type` or `hw.cpu.arch`, e.g. `x86_64`, `arm64-v8a`).
     - RAM allocation (converted to integer megabytes).
     - SD Card size (parsed and normalized to MB).
     - Hardware profile name (`hw.device.name`).
     - Display skin (`skin.name`).
3. Active runtime state is merged from the `AvdManager._active_sessions` registry (e.g. `STOPPED`, `LAUNCHING`, `BOOTING`, `RUNNING`, `ERROR`).
4. An `AvdConfig` object is returned to the caller.

---

## 5. API Response Schema
The AVD inventory is exposed via `GET /api/avd/list`:
```json
[
  {
    "name": "Pixel_7_API_34",
    "device_profile": "pixel_7",
    "target": "android-34",
    "api_level": 34,
    "abi": "x86_64",
    "skin": "pixel_7",
    "sdcard_size_mb": 512,
    "ram_size_mb": 2048,
    "path": "C:\\Users\\User\\.android\\avd\\Pixel_7_API_34.avd",
    "status": "STOPPED",
    "port": null,
    "serial": null,
    "error_message": null,
    "device_id": null
  }
]
```
