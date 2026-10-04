# KELVRA Device Lab — Acceptance Criteria Specification

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/ACCEPTANCE_CRITERIA.md`
- **Subsystem:** KELVRA Device Lab
- **Phase:** Phase 2 — Product Requirements, Feature Definition & Release Scope
- **Verification Standard:** Objective, measurable, observable pass/fail test conditions
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Verification Principles

Every acceptance criterion defined below must be objectively verifiable through automated tests, measurable telemetry, or deterministic manual inspection. Vague claims of "high performance" or "broad compatibility" are explicitly rejected.

Criteria are partitioned into:
1. **Functional Criteria (F-AC):** Observable behavioral capabilities.
2. **Performance Criteria (P-AC):** Measurable latency, throughput, and resource limits.
3. **Security & Boundary Criteria (S-AC):** Sandboxing, secret redaction, and permission enforcement.

---

## 2. Module A & B: Device Discovery & Fleet Management

### Functional Criteria
- **F-AC-01 (Device Enumeration):** When an Android device with USB debugging enabled is plugged into the host via USB, Device Lab must detect and display it in the Fleet Rail within <= 2.0 seconds of `adb devices` registering the device.
- **F-AC-02 (Hardware Classification):** The system must correctly classify hardware as `Physical` or `Virtual` based on `ro.kernel.qemu` or `ro.product.model` with 100% accuracy.
- **F-AC-03 (Metadata Accuracy):** The device card must accurately display the manufacturer, model name, Android OS version, SDK API level, and native resolution without truncation or formatting errors.
- **F-AC-04 (Unauthorized State Handling):** When an unauthorized device is connected, the UI must render an amber status dot (`#F59E0B`) and display clear guidance instructing the developer to accept the RSA fingerprint on the phone screen. When accepted, the UI must transition to `online` within <= 2.0 seconds without a page reload.

### Performance Criteria
- **P-AC-01 (Polling Overhead):** Background ADB fleet discovery polling must consume < 1% CPU on the host when no devices are connected or when connected devices are idle.

### Security Criteria
- **S-AC-01 (Zero Root Dependency):** Fleet discovery must operate entirely through non-root ADB user commands.

---

## 3. Module C: Device Screen Viewer

### Functional Criteria
- **F-AC-05 (Aspect Ratio Integrity):** When rendering any device resolution (e.g. 1080x2400, 1220x2712, 1600x2560), the screen stream must compute correct aspect-ratio pillarboxes or letterboxes. Zero image stretching, squishing, or distortion is permitted.
- **F-AC-06 (Orientation Tracking):** When the physical device rotates from portrait to landscape (or vice versa), the viewer must detect the change and reorient the display within <= 1.0 second.
- **F-AC-07 (Disconnect Recovery):** When the USB cable is unplugged during an active stream, the viewer must halt the stream immediately (< 500ms), display a "Device disconnected" overlay on the last valid frame, and release all background socket handles.

### Performance Criteria
- **P-AC-02 (Baseline Frame Rate):** The baseline JPEG WebSocket stream must sustain >= 15 FPS continuously over a 5-minute active UI interaction session on a 1080p display over USB 2.0/3.0.
- **P-AC-03 (Latency Bound):** Glass-to-glass teleoperation latency (from physical screen change to canvas render over localhost loopback) must not exceed 120ms average on the baseline streamer.

---

## 4. Module D: Remote Teleoperation & Input Injection

### Functional Criteria
- **F-AC-08 (Touch Tap Precision):** Clicking any pixel coordinate on the canvas must inject an Android touch tap at the corresponding normalized device screen coordinate with an accuracy tolerance of <= 3 physical pixels.
- **F-AC-09 (Drag & Swipe Gestures):** Clicking, dragging, and releasing must inject a smooth multi-point swipe sequence on the device, successfully scrolling Android scroll views and carousels.
- **F-AC-10 (Hardware Key Injection):** Clicking the Back button or right-clicking in the viewport must dispatch Android `KEYCODE_BACK`. Clicking Home must dispatch `KEYCODE_HOME`. Clicking App Switcher must dispatch `KEYCODE_APP_SWITCH`.
- **F-AC-11 (Physical Keyboard Typing):** With the viewport focused and an Android text field active, typing alphanumeric characters on the host physical keyboard must inject characters accurately into the device text field via ADB.

### Security Criteria
- **S-AC-02 (Input Injection Sanitization):** Text typing injection must strictly escape or reject shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `\n`) to prevent command injection into the ADB shell.

---

## 5. Module E & F: Application Management & Smoke Testing

### Functional Criteria
- **F-AC-12 (APK Installation):** Providing a valid Android APK file path must invoke `adb install -r -d` and report `Success` or structured error text within <= 15.0 seconds for APKs < 50 MB.
- **F-AC-13 (Package Launch & Termination):** Triggering application launch must dispatch the launcher activity and bring the package to the foreground within <= 2.0 seconds. Triggering force stop must terminate all package processes immediately.
- **F-AC-14 (Screenshot Assertion):** Triggering a screenshot capture must produce an uncompressed PNG file matching the device's native resolution within <= 800ms and return its absolute filesystem path.

### Security Criteria
- **S-AC-03 (Privileged Package Protection):** System application uninstallation or clearing must be hard-blocked by Device Lab.

---

## 6. Module H: Logs, Telemetry & Diagnostics

### Functional Criteria
- **F-AC-15 (Live Logcat Stream):** Logcat messages must stream over WebSockets with ring-buffered history (>= 2,000 lines). New log events must appear in the UI within <= 100ms of generation on device.
- **F-AC-16 (Filtering Responsiveness):** Applying a tag, severity, or regex filter must update the visible log list within <= 100ms without freezing the browser thread.
- **F-AC-17 (Hardware Telemetry Polling):** Telemetry panel must update CPU load, RAM usage, battery level, charging status, and battery temperature every 3 seconds. If temperature exceeds 42°C, an alert badge must appear.

### Security Criteria
- **S-AC-04 (Secret Redaction):** Logcat stream and export bundles must automatically redact strings matching standard API key formats, Bearer tokens, private keys, and passwords before transmission or storage.

---

## 7. Cross-Cutting Ergonomics & Zero-Emoji Enforcement

### Design & Rule Invariants
- **Z-AC-01 (Zero-Emoji Prohibition):** An automated regex sweep across all codebase files, templates, styles, and logs (`[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]`) must find **0 violations** (100% clean).
- **Z-AC-02 (Bench Design Alignment):** The UI must render using the frozen KELVRA Bench palette (`#262624`, `#1E1E1C`, `#1A1918`, `#2E2D2A`, `#D97757`), Lora serif headings, Inter sans labels, and JetBrains Mono tabular data.
- **Z-AC-03 (Reduced Motion):** When `@media (prefers-reduced-motion: reduce)` is active, touch ripples and sliding tab animations must be completely suppressed.
