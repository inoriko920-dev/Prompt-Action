# STEP 01 Evidence

Final STEP 01 gate: **BLOCKED — DO NOT START STEP 02**.

All implementation and automated compatibility evidence is complete except the required **local Windows 11 non-admin** validation.

## Verified Windows CI

- tested implementation commit: `c9da53c4c16248256783468aeb04d53b16913866`
- workflow run: `37016217751`
- job: `110867609593`
- runner: Microsoft Windows Server 2025 `10.0.26100`
- Python: `3.13.16` x64
- PySide6 / Qt: `6.11.2`
- pytest: `9.1.1`
- STEP 01 tests: `9 passed`
- module smoke: PASS
- screenshot/log capture: PASS

## Artifact

- artifact name: `step01-windows-evidence`
- artifact ID: `11230425186`
- ZIP size: `2525` bytes
- SHA256: `24ef2d1d1da1efef4607016c692ec1f568acade63d85efe39e99376722853efc`

Verified artifact contents:

- `minimal-window.png` — 1280×720 RGB, 4409 bytes
- `startup-success.log` — `startup.ready` + normal exit 0
- `startup-failure.log` — intentional missing-QML fatal case
- `environment.json` — Python/runtime/backend and exit evidence
- raw success runtime log
- raw failure runtime log

## Test matrix

- T01 PASS — import package
- T02 PASS — module entry point
- T03 PASS — exact window title
- T04 PASS — QML root load
- T05 PASS — invalid QML gives exit 21 + log
- T06 PASS — different cwd
- T07 PASS — path with spaces
- T08 PASS — Unicode path
- T09 **BLOCKED** — local Windows 11 non-admin execution not available in this environment
- T10 PASS — runtime write
- T11 PASS — read-only simulation
- T12 PASS — clean exact-lock install on Windows CI
- T13 PASS — repeated start/close
- T14 PASS — relocation with spaces/Unicode from unrelated cwd
- T15 PASS — Windows CI smoke

## Gate closer

Run `scripts/dev/verify_step01_windows11.ps1` from a **standard-user (non-admin) PowerShell session on Windows 11**. The script rejects non-Windows-11 or elevated sessions and verifies exact Python/PySide6 versions, the full test suite, and local evidence capture.

Until that proof exists, STEP 01 must remain BLOCKED and STEP 02 must not start.
