# KELVRA Device Lab — Licensing, Attribution & Distribution Review

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/LICENSING_AND_ATTRIBUTION.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Authority:** Open-Source Licensing Compliance & Intellectual Property Governance
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Upstream License Inventory

| Component / Dependency | Upstream Project | License Type | Distribution Model in Device Lab | Compliance Requirements |
|---|---|---|---|---|
| **FastAPI** | tiangolo/fastapi | MIT | Direct Python Dependency (`requirements.txt`) | Retain copyright notice. |
| **Uvicorn** | encode/uvicorn | BSD-3-Clause | Direct Python Dependency (`requirements.txt`) | Retain BSD copyright notice. |
| **Pillow** | python-pillow/Pillow | HPND (MIT-like) | Direct Python Dependency (`requirements.txt`) | Retain historical license text. |
| **scrcpy-server.jar** | Genymobile/scrcpy | Apache 2.0 | Bundled Pre-Compiled Binary (Release 1.x) | Retain Apache 2.0 license text, NOTICE file, and Genymobile copyright notice. |
| **ADB (adb.exe)** | Google AOSP | Apache 2.0 / SDK License | Host-Provided (Not Bundled) | External toolchain; zero redistribution risk. |
| **Android Emulator** | Google Android SDK | Proprietary SDK Terms | Host-Provided (Not Bundled) | Never bundled; user must install via Android Studio / SDK Manager. |
| **pymobiledevice3** | doronz88/pymobiledevice3 | GPLv3 (Copyleft) | Isolated Subprocess CLI / Worker | Strict process boundary required. Must NOT import into KELVRA core in-process. |
| **Maestro** | mobile-dev/maestro | Apache 2.0 | External Toolchain (CLI Runner) | Retain Apache 2.0 notice if bundled. |

---

## 2. Critical Legal & Licensing Boundaries

### 2.1 The GPLv3 Copyleft Boundary (`pymobiledevice3`)
- **Risk Analysis:** `pymobiledevice3` is licensed under the GNU General Public License v3.0 (GPLv3). If Python code directly imports `pymobiledevice3` modules (`import pymobiledevice3`) inside a proprietary or permissively licensed application, the entire application risks being classified as a derivative work under GPLv3, triggering source disclosure obligations.
- **Architectural Mitigation:**
  1. KELVRA Device Lab core (`src/server.py`, `src/device_manager.py`) **never** executes an in-process import of `pymobiledevice3`.
  2. All interactions with `pymobiledevice3` are executed via **command-line subprocess invocation** (`pymobiledevice3.exe ...`) consuming standard JSON output.
  3. Under established software engineering precedent and FSF GPL guidance, communicating with a separate standalone binary over standard pipes/JSON constitutes a standard inter-process boundary, preserving KELVRA's permissive/proprietary licensing independence.

### 2.2 Google Android SDK Licensing & Redistribution
- **Risk Analysis:** Google distributes `platform-tools` (containing `adb.exe`) and `emulator` under the Android Software Development Kit License Agreement. Section 3 strictly restricts redistributing the SDK or its binary components without an explicit OEM distribution agreement.
- **Architectural Mitigation:**
  1. KELVRA Device Lab **never bundles or redistributes** Google's proprietary binaries (`adb.exe`, `emulator.exe`, system images).
  2. Device Lab operates strictly as an orchestrator pointing to the developer's locally installed SDK on `PATH` or `ANDROID_HOME`.
  3. If ADB is missing, Device Lab renders clear instructional guidance directing the developer to download Android Platform Tools from Google's official developer portal.

### 2.3 Apache 2.0 Compliance (`scrcpy-server.jar`)
- **Compliance Policy:** When bundling `scrcpy-server.jar` in Release 1.x:
  1. Retain the full Apache 2.0 license file inside `licenses/LICENSE-scrcpy.txt`.
  2. Provide prominent attribution in `README.md` and documentation: *"Includes pre-compiled server components from scrcpy by Romain Vimont / Genymobile (Apache License 2.0)"*.
  3. Include a link to the official upstream source repository (`https://github.com/Genymobile/scrcpy`).

---

## 3. Commercial Use & Trademark Considerations

- **Permissive Licenses (MIT, Apache 2.0, BSD-3):** Explicitly permit commercial use, internal modification, and private distribution without royalty obligations.
- **Trademark Respect:**
  - "Android" is a trademark of Google LLC.
  - "Apple", "iPhone", "iPad", and "iOS" are trademarks of Apple Inc.
  - Device Lab documentation uses these marks purely for factual descriptive compatibility purposes, in full compliance with standard nominative fair-use principles.
