# KELVRA Device Lab — Packaging and Installation

## Document Information
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/PACKAGING_AND_INSTALLATION.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Version:** v1.0.0
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Packaging Architecture

KELVRA Device Lab uses a multi-modal deployment architecture:

1. **Standalone Directory Distribution:**
   - The repository or release folder contains `pyproject.toml`, `requirements.txt`, launchers (`run_standalone.py`, `run_standalone.bat`, `run_standalone.sh`), `src/`, `static/`, and an initialized `artifacts/` folder.
   - Ideal for local development, bench pairing, and developer workstation laboratories.

2. **Python Wheel Distribution (`.whl`):**
   - Standard PEP 517/621 wheel package generated into `dist/`.
   - Bundles all core Python logic (`src/`), static web assets (`static/`), and CLI entry points (`kelvra-device-lab`).
   - Clean separation: test suites (`tests/`), git metadata (`.git/`), and personal configuration (`.env`) are excluded.

---

## 2. Installation Procedures

### 2.1 From Python Wheel
To install the pre-built release wheel into a Python virtual environment:
```bash
pip install dist/kelvra_device_lab-1.0.0-py3-none-any.whl
```
This automatically registers the `kelvra-device-lab` command on the system PATH.

To launch the service:
```bash
kelvra-device-lab
```

### 2.2 From Source in Editable Mode
For active development and debugging:
```bash
cd "Kelvra/KELVRA Device Lab"
pip install -e . --no-deps --no-build-isolation
```

### 2.3 Standalone Portable Installation (No Pip Install)
Users who prefer not to install the package into global or virtual environments can run directly:
- **Windows:** Double-click `run_standalone.bat`.
- **Linux / macOS:** Execute `./run_standalone.sh`.
- **Cross-Platform:** Execute `python run_standalone.py`.

---

## 3. Directory Layout and Storage Partitions

When installed and running, the service manages three primary filesystem domains:

1. **Application Code Domain (Read-Only at Runtime):**
   - `src/`: Core Python modules and FastAPI router.
   - `static/`: HTML, CSS, JavaScript, and SVG vector assets.

2. **Configuration Domain (Read-Only at Runtime):**
   - `.env`: Environment variables overriding server port, host, ADB paths, and streaming parameters.
   - Defaults: Host `127.0.0.1`, Port `8098`, Stream FPS `15`, Stream Quality `70`.

3. **Artifact Storage Domain (Read-Write with Bounded Quota):**
   - `artifacts/catalog.json`: Index of all generated test and media assets.
   - `artifacts/screenshots/`: Captured display frames.
   - `artifacts/recordings/`: Captured MP4 video sessions.
   - `artifacts/logs/`: Exported logcat captures.
   - `artifacts/reports/`: JSON workflow execution reports.
   - *Quota Enforcement:* Managed by `ArtifactManager` with a 500 MB default workstation quota and automatic LRU eviction of oldest assets when capacity threshold is reached.

---

## 4. Uninstallation & Cleanup

To uninstall the Python wheel:
```bash
pip uninstall kelvra-device-lab -y
```

To remove generated test artifacts and reset the catalog:
- Delete contents inside `artifacts/screenshots/`, `artifacts/recordings/`, `artifacts/logs/`, `artifacts/reports/`.
- Reset `artifacts/catalog.json` to `{}`.
