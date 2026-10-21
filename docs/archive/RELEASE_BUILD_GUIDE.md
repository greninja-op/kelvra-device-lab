# KELVRA Device Lab — Release Build Guide

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/RELEASE_BUILD_GUIDE.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Prerequisites

### Host Environment Requirements
- **Python:** 3.10 or higher (Verified on Python 3.13.7 64-bit on Windows 11).
- **Core Build Tools:** `pip`, `setuptools>=61.0.0`, `wheel`.
- **System Platform Tools (Optional for physical hardware access):**
  - Android SDK Platform Tools (`adb.exe` on system PATH, version 1.0.41+).
  - Apple Mobile Device Support (AMDS service active on TCP `127.0.0.1:27015` or iTunes for Windows).

---

## 2. Source Tree Verification

Ensure working directory is at the root of `Kelvra/KELVRA Device Lab/`:
```bash
cd "Kelvra/KELVRA Device Lab"
```

Verify directory structure:
```
Kelvra/KELVRA Device Lab/
├── pyproject.toml
├── requirements.txt
├── run_standalone.py
├── run_standalone.bat
├── run_standalone.sh
├── .env.example
├── src/
├── static/
├── tests/
├── artifacts/
└── docs/
```

---

## 3. Dependency Installation

### Standard Production Dependencies
Install required runtime libraries:
```bash
pip install -r requirements.txt
```

### Development & Test Dependencies
For running the regression suite:
```bash
pip install pytest pytest-asyncio
```

---

## 4. Building the Release Distribution

To generate a clean, self-contained Python wheel:
```bash
python -m pip wheel . -w dist --no-deps --no-build-isolation
```

The resulting wheel is deposited into `dist/`:
- **Artifact Path:** `dist/kelvra_device_lab-1.0.0-py3-none-any.whl`
- **Size:** Approximately 127 KB
- **Contents:** `src/` modules, `static/` HTML/CSS/JS assets, `pyproject.toml` metadata, CLI scripts.

To verify package contents without extraction:
```bash
python -c "import zipfile; zf = zipfile.ZipFile('dist/kelvra_device_lab-1.0.0-py3-none-any.whl'); print('\n'.join(zf.namelist()))"
```

---

## 5. Running the Application

### Option A: Direct Python Script Launcher
```bash
python run_standalone.py
```

### Option B: Windows Batch Launcher
```cmd
run_standalone.bat
```

### Option C: POSIX Shell Launcher
```bash
chmod +x run_standalone.sh
./run_standalone.sh
```

### Option D: Installed CLI Script
After installing the wheel or editable package (`pip install -e .`):
```bash
kelvra-device-lab
```

### Option E: Uvicorn Directly
```bash
python -m uvicorn src.server:app --port 8098 --host 127.0.0.1
```

Once running, the Web Control Room is accessible at `http://127.0.0.1:8098/` and REST API documentation at `http://127.0.0.1:8098/docs`.

---

## 6. Running Verification Tests

To execute the complete 155-test standalone regression suite:
```bash
pytest -q
```
Expected output: `155 passed in ~30s`.
