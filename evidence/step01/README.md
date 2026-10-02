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
- T09 **BLOCKED** — local Windows 11 non-admin execution not yet supplied
- T10 PASS — runtime write
- T11 PASS — read-only simulation
- T12 PASS — clean exact-lock install on Windows CI
- T13 PASS — repeated start/close
- T14 PASS — relocation with spaces/Unicode from unrelated cwd
- T15 PASS — Windows CI smoke

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
8. writes OS/runtime/result metadata without recording the Windows account name;
9. hashes every evidence file with SHA256;
10. creates `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip` plus its `.sha256.txt` file.

The verifier deliberately does **not** record the Windows username, email address, API key, token, or credential.

If the exact Python runtime is missing, the script stops with a clear message instead of silently using another version.

## Files to return to SOL

After a PASS, provide these two generated files:

- `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip`
- `evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip.sha256.txt`

SOL must verify the ZIP/hash/result evidence before changing STEP 01 from BLOCKED to PASS.

Until that proof exists, STEP 01 remains BLOCKED and STEP 02 must not start.
