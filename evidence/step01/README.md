# STEP 01 Evidence

Final STEP 01 gate: **BLOCKED — DO NOT START STEP 02**.

All implementation and automated compatibility evidence is complete except the required **local Windows 11 non-admin** validation.

## Latest verified Windows CI

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
- local Windows 11 gate script syntax/privacy guard: PASS
- Windows Server expected rejection: PASS

The workflow explicitly verifies that Windows Server CI is rejected by the local target verifier, so CI cannot be mistaken for the required Windows 11 T09 proof.

## CI artifacts

### `step01-windows-evidence`

- artifact ID: `11232441027`
- SHA256: `a5cf7c37a058a1319ac54489bae77077915bb422aace9572c9b91e1b5384fc51`

### `step01-windows11-verifier-bundle`

- artifact ID: `11232401037`
- SHA256: `b2dbf20b4f52598b5c36a4a823677dc73f8a9613fdb8028a6b25497999363257`

The second artifact is a verification source bundle only, not a final portable application release.

## Test matrix

- T01 PASS — import package
- T02 PASS — module entry point
- T03 PASS — exact window title
- T04 PASS — QML root load
- T05 PASS — invalid QML gives exit 21 + log
- T06 PASS — different cwd
- T07 PASS — path with spaces
- T08 PASS — Unicode path
- T09 **BLOCKED** — actual local Windows 11 non-admin execution not yet supplied
- T10 PASS — runtime write
- T11 PASS — read-only simulation
- T12 PASS — clean exact-lock install on Windows CI
- T13 PASS — repeated start/close
- T14 PASS — relocation with spaces/Unicode from unrelated cwd
- T15 PASS — hardened Windows CI smoke

## One-click gate closer on the target Windows 11 PC

Use:

`scripts/dev/STEP_01_VERIFY_WINDOWS11.bat`

Run it by normal double-click. **Do not use “Run as administrator”.**

The launcher calls `verify_step01_windows11.ps1`, which:

1. rejects anything other than Windows 11;
2. rejects an elevated/admin PowerShell token;
3. prepares/reuses the locked `.venv` using CPython `3.13.16` and PySide6 `6.11.2`;
4. runs the complete STEP 01 pytest suite;
5. launches Prompt Action through the native Windows Qt platform and requires exit `0`;
6. runs the intentional missing-QML case and requires exit `21`;
7. captures a native Windows minimal-window PNG;
8. redacts repository-root and user-profile paths from packaged text logs;
9. does not intentionally record Windows account name, email, API key, token, or credential;
10. hashes every evidence file with SHA256;
11. creates `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip` plus its `.sha256.txt` file.

If the exact Python runtime is missing, the script stops with a clear message instead of silently using another version.

## Files to return to SOL

After a PASS, provide these two generated files:

- `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip`
- `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip.sha256.txt`

SOL must verify the ZIP/hash/result evidence before changing STEP 01 from BLOCKED to PASS.

Until that proof exists, STEP 01 remains BLOCKED and STEP 02 must not start.
