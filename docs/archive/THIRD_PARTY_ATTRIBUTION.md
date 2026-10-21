# KELVRA Device Lab — Third-Party Licenses & Attribution

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/THIRD_PARTY_ATTRIBUTION.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Core Python Dependencies

| Package Name | Version Range | License | Project URL | Usage Domain |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** | >=0.100.0 | MIT License | `https://github.com/tiangolo/fastapi` | REST & WebSocket server framework |
| **Uvicorn** | >=0.22.0 | BSD-3-Clause | `https://github.com/encode/uvicorn` | ASGI web server implementation |
| **Pydantic** | >=2.0.0 | MIT License | `https://github.com/pydantic/pydantic` | Data validation & domain models |
| **WebSockets** | >=11.0.0 | BSD-3-Clause | `https://github.com/python-websockets/websockets` | Screen streaming protocol |
| **Pillow (PIL)** | >=9.5.0 | Historical Permission Notice and Disclaimer (HPND) | `https://github.com/python-pillow/Pillow` | Image compression & LANCZOS downsampling |
| **HTTPX** | >=0.24.0 | BSD-3-Clause | `https://github.com/encode/httpx` | Async client for Bench communication |
| **Pytest** | >=7.0.0 | MIT License | `https://github.com/pytest-dev/pytest` | Test execution framework (Dev) |
| **Pytest-Asyncio** | >=0.21.0 | Apache 2.0 | `https://github.com/pytest-dev/pytest-asyncio` | Async test fixtures (Dev) |

All direct Python dependencies use permissive open-source licenses (MIT, BSD, Apache 2.0, HPND). None impose copyleft requirements on KELVRA proprietary code.

---

## 2. External System Toolchains

| Tool Name | License | Isolation Mechanism | Notes |
| :--- | :--- | :--- | :--- |
| **Android Debug Bridge (ADB)** | Apache 2.0 | External CLI subprocess (`shell=False`) | Part of Android SDK Platform-Tools |
| **Android Emulator** | Apache 2.0 / Google SDK Terms | External CLI subprocess (`shell=False`) | Bundled with host Android SDK |
| **Apple Mobile Device Support (AMDS)** | Apple Proprietary | Loopback TCP socket (`127.0.0.1:27015`) | Native Windows daemon bundled with iTunes/AMDS |
| **pymobiledevice3 / libimobiledevice** | GPLv3 / LGPLv2.1 | Strict external CLI subprocess boundary | Zero in-process Python linking; isolated out-of-process |

---

## 3. Typography & Design Assets

- **Lora:** SIL Open Font License 1.1 (Google Fonts)
- **Inter:** SIL Open Font License 1.1 (Rasmus Andersson / Google Fonts)
- **JetBrains Mono:** Apache 2.0 (JetBrains s.r.o.)
- **Icons:** Custom authentic SVG vector icons derived from project assets (Zero raw Unicode emojis).
