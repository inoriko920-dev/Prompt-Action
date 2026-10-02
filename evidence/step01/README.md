# STEP 01 Evidence

Final STEP 01 gate: **PASS**.

## Acceptance-policy override

On 2026-10-02 the project owner explicitly removed the requirement for a local Windows 11 non-admin run and accepted successful GitHub Windows CI as sufficient evidence for STEP 01.

This does **not** claim that a local Windows 11 test happened. T09 is now recorded as **WAIVED / NON-BLOCKING BY OWNER**. The optional Windows 11 verifier remains available only as diagnostic tooling.

## Accepted Windows CI

- tested helper/foundation commit: `9a361df400258df150f9db809fa0c402a09a8c2e`
- workflow run: `37018351536`
- job: `110874729579`
- result: PASS
- runner: Microsoft Windows Server 2025
- Python: `3.13.16` x64
- PySide6 / Qt: `6.11.2`
- STEP 01 tests: PASS
- module smoke: PASS
- screenshot/log capture: PASS
- verifier script syntax/privacy guard: PASS
- Windows Server identity/rejection guard: PASS

## CI artifacts

### `step01-windows-evidence`

- artifact ID: `11232441027`
- SHA256: `a5cf7c37a058a1319ac54489bae77077915bb422aace9572c9b91e1b5384fc51`

### `step01-windows11-verifier-bundle`

- artifact ID: `11232401037`
- SHA256: `b2dbf20b4f52598b5c36a4a823677dc73f8a9613fdb8028a6b25497999363257`

The second artifact is optional verification tooling only, not a final portable release and no longer a blocking acceptance requirement.

## Final test matrix

- T01 PASS — import package
- T02 PASS — module entry point
- T03 PASS — exact window title
- T04 PASS — QML root load
- T05 PASS — invalid QML gives exit 21 + log
- T06 PASS — different cwd
- T07 PASS — path with spaces
- T08 PASS — Unicode path
- T09 **WAIVED / NON-BLOCKING BY OWNER** — local Windows 11 run no longer required
- T10 PASS — runtime write
- T11 PASS — read-only simulation
- T12 PASS — clean exact-lock install on Windows CI
- T13 PASS — repeated start/close
- T14 PASS — relocation with spaces/Unicode from unrelated cwd
- T15 PASS — hardened Windows CI smoke

Acceptance result: **STEP 01 PASS**.

## Optional local verifier

`scripts/dev/STEP_01_VERIFY_WINDOWS11.bat` and `verify_step01_windows11.ps1` remain in the repo for optional target-machine diagnostics. Their result is no longer required to merge STEP 01 or begin STEP 02.
