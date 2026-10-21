# KELVRA Device Lab — Upstream Dependency & Supply Chain Policy

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DEPENDENCY_POLICY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 4 — Upstream Repository Research, Technical Evaluation & Component Selection
- **Authority:** Supply Chain Security & Dependency Governance
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Upstream Dependency Principles

To ensure reproducibility, eliminate supply chain attack surfaces, and maintain workspace isolation:
1. **Isolated Virtual Environments:** All Device Lab dependencies reside in its dedicated project virtual environment; dependencies are **never** installed into the parent `Kelvra/` or `PLANNING/` roots.
2. **Deterministic Version Pinning:** Every dependency in `requirements.txt` must be pinned to an exact semantic version (e.g. `fastapi==0.115.0`), accompanied by cryptographic SHA-256 hashes (`--hash=sha256:...`).
3. **Approved Upstream Registries Only:** Dependencies are consumed exclusively from authoritative official sources (PyPI for Python wheels, official GitHub Release tags for verified binary assets).
4. **Least Dependency Footprint:** Preference is always given to standard library capabilities (`sqlite3`, `asyncio`, `subprocess`, `urllib`) over introducing third-party packages.

---

## 2. Binary Verification & Checksum Policy

When third-party binary artifacts (such as `scrcpy-server.jar`) are introduced in Release 1.x:
1. **Official Release Origin:** Binaries must be downloaded directly from the official upstream GitHub release assets published by the verified project maintainer (`Genymobile/scrcpy/releases`).
2. **Cryptographic Checksum Gate:** Every binary asset must have its SHA-256 checksum recorded in `docs/DEPENDENCY_POLICY.md` and verified during build/test execution:
   ```python
   EXPECTED_SCRCPY_SHA256 = "a1b2c3d4e5f6..." # Verified upstream release checksum
   ```
3. **Fail-Closed Execution:** If a binary hash mismatch is detected, Device Lab halts execution immediately and refuses to push the payload to connected mobile devices.

---

## 3. Vulnerability Monitoring & Patching Workflow

1. **Automated Audits:** Device Lab dependencies are audited against the National Vulnerability Database (NVD) and GitHub Advisory Database using `pip-audit`.
2. **Triage Severity SLA:**
   - *Critical (CVSS >= 9.0):* Immediate patch or dependency replacement within 24 hours.
   - *High (CVSS 7.0–8.9):* Remediation within 7 days.
   - *Medium / Low:* Evaluated during regular milestone phase updates.
3. **Replacement & Removal Strategy:** If an upstream dependency is deprecated, compromised, or abandons maintenance:
   - Device Lab's adapter boundaries (`BaseDeviceProvider`, `ScreenStreamer`) allow the underlying library to be replaced with zero changes to the public REST API or UI layer.
