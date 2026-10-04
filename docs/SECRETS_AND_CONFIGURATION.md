# KELVRA Device Lab — Secrets, Credentials & Configuration Governance

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/SECRETS_AND_CONFIGURATION.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 5 — Security Architecture, Authorization, Device Trust & Threat Modeling
- **Authority:** Secret Management & Configuration Hygiene
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Configuration Ownership & Storage Standards

Device Lab maintains a strict separation between runtime configuration, state memory, and secret credentials:

1. **`.env` (Project-Local Only):** Located strictly inside `Kelvra/KELVRA Device Lab/.env`. Contains local environment overrides (e.g. `PORT=8098`, `SCRATCH_DIR=scratch`). It is git-ignored and never committed.
2. **`.env.example` (Template Only):** Committed template documenting available configuration keys with dummy values. Never contains real API keys, passwords, or tokens.
3. **`session.env` & Shared Files:** Device Lab **never** reads, creates, or writes to shared root environment files (`Kelvra/.env`, `session.env`). Shared environment files are prohibited from being used as ad-hoc inter-process memory stores.
4. **Project Memory Belongs in Docs:** Operational project state is tracked exclusively in `docs/PROJECT_STATE.md` and session files (`Kelvra/sessions/SESSIONS.md`), never inside environment files.

---

## 2. Secrets Handling & Anti-Leakage Invariants

| Credential Class | Storage Location | Access Controls | In-Transit Protection | Logging Rules |
|---|---|---|---|---|
| **KELVRA Bench API Tokens (`kbt-`)** | In-memory header (`Authorization: Bearer kbt-...`) | Checked by auth gate; never stored on disk | Localhost HTTP / WS headers | Strictly redacted: replaced with `kbt-[REDACTED]` in all logs. |
| **Android ADB RSA Key (`adbkey`)** | OS User Profile (`~/.android/adbkey`) | Protected by host OS user permissions (`0600`) | Asymmetric challenge-response | Private key bytes are never read or logged by Device Lab. |
| **Apple Lockdown Pairing Records** | OS System Storage (`%ProgramData%\Apple\Lockdown`) | Protected by OS filesystem ACLs | SSL/TLS over USB | Pairing plist contents and certificates are never logged. |
| **Mobile App Credentials / Secrets** | Target mobile device storage | Sandboxed by Android/iOS kernel | USB transport | Screen/logcat streaming redacts detected tokens automatically. |
| **Signing Certificates / Keystores** | Developer build workspace | Git-ignored local files | N/A | Keystore passwords are never passed via command-line arguments. |

---

## 3. Configuration Modification Prohibitions

To protect concurrent IDE sessions (especially KELVRA Voice) and prevent configuration drift:
- Device Lab agents are **strictly prohibited** from performing blanket overwrites or deletions of configuration files.
- Environment variables are read lazily via standard `os.environ.get()` with safe, hardcoded defaults.
- All secrets encountered during runtime execution or diagnostic parsing are ephemeral and stored only in volatile memory with immediate garbage collection.
