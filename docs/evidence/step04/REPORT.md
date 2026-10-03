# STEP 04 Evidence Report

Status: **PASS**

## Canonical source

The Dashboard evidence was generated from validated canonical state, not sample UI values.

- Active System: `V1`
- Active Snapshot: `S001`
- Active Prompt count: `8`
- Backup health: `PERLU BACKUP`
- Latest change title: `Baseline sistem aktif`
- Baseline PRIMARY: none
- Baseline SYNC: none
- Recovery health: `REQUIRED`

## Evidence provenance

Workflow run `37106329477`, job `111155472297`, head `063d42eec213f9438fe7cf2faf00dbb4db4234b8` concluded SUCCESS.

GitHub Actions artifact:
- `step04-dashboard-evidence`
- artifact ID `11267679510`
- size `123798` bytes
- SHA-256 `54eed1998d87453457d63dec644143525b8ce43aab4c1d63963b1013ece345fb`
- independent downloaded ZIP SHA-256 matched exactly.

The artifact contains:
- `ci-step04-preflight/preflight.json`
- `ci-step04-evidence/capture.json`
- master `01-Dashboard.jpg`
- six required Dashboard screenshots.

## Screenshot set

- `dashboard-1600x900.png` — 1600×900
- `dashboard-1920x1080.png` — 1920×1080
- `dashboard-1366x768.png` — 1366×768
- `dashboard-loading.png` — 1600×900
- `dashboard-invalid.png` — 1600×900
- `dashboard-backup-required.png` — 1600×900

The binary screenshots remain in the CI artifact; this folder records their canonical metadata and review result without duplicating generated binary CI output in source history.

## Review result

Composition, state semantics, responsive behavior, and capability gating are accepted for STEP 04. Hosted Qt offscreen screenshots use the same tofu/box glyph limitation already documented in STEP 03; there are no QML warnings. The 1366×768 Dashboard remains scrollable and its Backup action buttons remain inside the card after narrow-layout hardening.
