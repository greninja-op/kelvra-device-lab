# KELVRA Device Lab — File & Package Security Standards

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/FILE_AND_PACKAGE_SECURITY.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** File Storage, Upload Handling & Artifact Sandboxing
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Storage Organization & Directory Jails

All files read, written, or staged by Device Lab are strictly confined to dedicated directories inside `Kelvra/KELVRA Device Lab/`:

```
Kelvra/KELVRA Device Lab/
├── artifacts/
│   ├── evidence/          # Checkpoint screenshots and test JSON reports
│   ├── diagnostics/       # Exportable redacted diagnostic bundles
│   └── recordings/        # Screen recording video files (Release 1.x)
├── data/                  # SQLite database (device_lab.db)
└── scratch/               # Temporary staged APKs and transient buffers
```

Any attempt to read, write, or stage files outside this dedicated tree is blocked immediately.

---

## 2. File Ingestion & Path Traversal Mitigations

### 2.1 Allowed File Types & Size Caps
- **Application Packages:** `.apk` (Android) and `.ipa` (iOS). Max size: `150 Megabytes`.
- **Test Automation Flows:** `.yaml`, `.yml` (Maestro flows). Max size: `2 Megabytes`.
- **All Other File Types:** Hard rejected (e.g. `.exe`, `.bat`, `.ps1`, `.sh`, `.vbs`, `.dll`, `.jar` uploads are forbidden).

### 2.2 Path Traversal & Normalization Policy
When receiving file uploads or processing target file paths:
1. **Filename Sanitization:** The original filename is stripped of directory components (`os.path.basename`) and sanitized to allow only alphanumeric characters, dots, and hyphens (`[a-zA-Z0-9_\.-]`).
2. **UUID Namespace Isolation:** Staged files are assigned a unique cryptographic UUID prefix:
   `scratch/staged_apk_<uuid>_<sanitized_filename>.apk`
3. **Canonical Path Resolution:** Target paths are resolved using `pathlib.Path.resolve()`. If the resolved absolute path does not start with the canonical root of the target directory jail, the operation is aborted with a `PathTraversalAttackError`.
4. **Symlink Rejection:** Symlinks encountered during file reads or archive extractions are rejected and not followed (`follow_symlinks=False`).

---

## 3. Untrusted Application Package (APK) Handling

Test builds uploaded to Device Lab may be experimental or malformed. To prevent compromise:
- **No Automatic Installation:** Uploading an APK merely stages the binary in the scratch jail. An APK is **never** installed automatically upon upload.
- **Explicit Installation Trigger:** Installation requires an explicit API call or confirmation modal verifying the package name and target device serial.
- **Pre-Install Signature & Manifest Verification:** Before dispatching `adb install`, Device Lab queries basic package metadata using `aapt` or native APK zip parsing:
  - Verifies that `AndroidManifest.xml` is present and well-formed.
  - Extracts package name, version code, and requested permissions.
  - Rejects corrupted or truncated archives.
- **Post-Install Scratch Cleanup:** Staged temporary APK files in `scratch/` are deleted automatically within 60 seconds of installation completion.

---

## 4. Evidence Artifacts & Secret Redaction in Exports

- **Evidence Storage:** Screenshots captured during manual teleoperation or test assertions are saved to `artifacts/evidence/<serial>/<timestamp>_<checkpoint>.png` with permissions set to current user only (`0600`).
- **Pre-Export Secret Scrubbing:** When a diagnostic bundle or logcat slice is exported:
  1. All text files are scanned by the streaming regex redaction engine (`docs/SECURITY_ARCHITECTURE.md`).
  2. Any occurrences of Bearer tokens, private keys, passwords, or API credentials are scrubbed and replaced with `[REDACTED_SECRET]`.
  3. The resulting sanitized archive is bundled as a standard `.zip` file inside `artifacts/diagnostics/`.
