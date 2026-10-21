# KELVRA Device Lab — Design Acceptance Criteria

## Document Metadata
- **Document Path:** `Kelvra/KELVRA Device Lab/docs/DESIGN_ACCEPTANCE_CRITERIA.md`
- **Subsystem:** KELVRA Device Lab (`:8098`)
- **Authority:** KELVRA Bench Design Contract & Phase 6 UX Specifications
- **Status:** Verified Design Acceptance Criteria
- **Emoji Prohibition Compliance:** 100% verified (0 raw Unicode emojis)

---

## 1. Objective Acceptance Gates

Every visual layout and UI interaction in KELVRA Device Lab must satisfy the following 15 objective, verifiable criteria before being certified for release:

| ID | Category | Observable Criterion | Verification Method |
| :--- | :--- | :--- | :--- |
| **DS-AC-01** | **Design Tokens** | Every surface, border, and text element uses exact CSS variables from `docs/DESIGN_TOKENS.md` (`#262624`, `#1E1E1C`, `#1A1918`, `#F5F1EA`, `#A39E93`, `#D97757`). No foreign hex codes exist. | Automated CSS token audit / regex sweep. |
| **DS-AC-02** | **Typography** | Titles and device names render in `Lora` (500 weight); interface controls render in `Inter`; metrics, FPS counters, and logs render in `JetBrains Mono` with `font-variant-numeric: tabular-nums`. | Computed font-family inspection in headless Chromium. |
| **DS-AC-03** | **Aspect Ratio** | The live device viewing canvas preserves the device's native aspect ratio (e.g. 20:9 for POCO X6 Pro) with clean container pillarbox/letterbox gutters without stretching or distortion. | Pixel dimension ratio assertion against `adb shell wm size`. |
| **DS-AC-04** | **Zero-Emoji Rule** | Zero raw Unicode emojis (`[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]`) exist anywhere in HTML, CSS, JavaScript, logs, or UI strings. All glyphs are 1.8px outlined vector SVGs. | Automated regex test suite sweep across all frontend assets. |
| **DS-AC-05** | **Status Taxonomy** | Status is communicated via solid 8px flat dots (`●`) paired with explicit text (`idle`, `working`, `blocked`, `review`, `complete`, `error`). No glowing shadows or color-only status. | Visual regression inspection & DOM assertion. |
| **DS-AC-06** | **Touch Feedback** | Registered touch/click events on the canvas render an immediate terracotta ripple (`rgba(217, 119, 87, 0.40)`) that expands and fades out within 200ms. | DOM animation lifecycle inspection. |
| **DS-AC-07** | **Touch Targets** | All buttons, tab headers, hardware navigation controls, and context triggers have a minimum interactive hit-box of 44px x 44px. | Element boundingClientRect dimension verification. |
| **DS-AC-08** | **Keyboard Nav** | Complete workflow (fleet browsing -> device selection -> teleoperation -> log inspection) is operable via keyboard alone with visible terracotta focus rings (`#D97757`). | Headless Playwright keyboard tab-sequence traversal test. |
| **DS-AC-09** | **Logcat Virtualization**| The logcat feed maintains exactly 50 physical DOM nodes regardless of log volume, sustaining 60 FPS scrolling during 1,000 lines/sec bursts without DOM bloat. | DOM child element count assertion (`nodeCount === 50`). |
| **DS-AC-10** | **Lease Exclusivity** | Active single-writer lease ownership is prominently indicated via a terracotta status badge (`SessionIndicatorPill`) with a live countdown timer in tabular numerals. | DOM element presence and content verification. |
| **DS-AC-11** | **Actionable Errors** | Error and unauthorized states provide specific, actionable physical instructions (e.g. "Accept 'Allow USB debugging' prompt on phone") without suggesting security bypasses. | Copy review against `docs/CONNECTION_WORKFLOW_UX.md`. |
| **DS-AC-12** | **Contrast Ratios** | All text-to-background combinations achieve WCAG 2.1 AA (min 4.5:1 for body) and AAA (min 7.0:1 for headings). | Automated axe-core / Lighthouse accessibility audit. |
| **DS-AC-13** | **Reduced Motion** | Enabling `@media (prefers-reduced-motion: reduce)` immediately eliminates all transitions and ripples, snapping values and dialogs instantly into place. | CSS computed transition duration assertion (`duration <= 0.01ms`). |
| **DS-AC-14** | **Responsive Scaling** | Layout gracefully resizes from 4K (2560px) down to minimum usable window (768px width x 600px height) without horizontal scrollbars or clipped teleoperation controls. | Viewport resizing suite in Playwright across 5 breakpoint tiers. |
| **DS-AC-15** | **Bench Parity** | Device Lab visually matches KELVRA Bench (`kelvra-bench`) when placed side-by-side; shared components and tokens share identical design DNA. | Dual-view screenshot perceptual hash diff (< 2% variance). |
