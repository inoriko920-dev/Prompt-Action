# STEP 00 — Preservation Log

Audit date: 2026-10-02 (Asia/Jakarta)

## Preservation mode

The repository portion of STEP 00 used a dedicated branch `sol/step00-baseline-audit-20261002` created from audited `main` HEAD `350e5428afe8ec435f52f12189faf7ef0e9b4ea0`.

The supplied V22.5.1 rescue ZIP was handled in a separate local workroot:

```text
00_ORIGINAL_READONLY/
01_STAGING/
02_EVIDENCE/step00/
03_REPORT/
04_TEMP/
```

No destructive Git or filesystem operation was applied to the original rescue ZIP or repository evidence.

## Original rescue ZIP

Input:

`V22_5_1_Update_1B_Dialog_Campuran,_Audit_Jangkar_Aksi_Terlewat,(1).zip`

Observed size: `69158` bytes.

SHA256 before copy/extraction:

`f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`

A preservation copy was made before extraction. Its SHA256 is identical:

`f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`

SHA256 of the original after extraction/audit is also identical:

`f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`

Result: original remained byte-for-byte unchanged.

## Extraction discipline

- original ZIP copied before extraction;
- extraction performed only under staging;
- no extracted source file was edited, normalized, renamed or regenerated;
- all 16 extracted files were hashed;
- all 16 hashes were recomputed a second time and the complete maps were identical;
- no nested archive was found inside the V22.5.1 package.

## Repository evidence treated read-only

- `.github/workflows/**`
- `PLAN.md`
- `START_HERE.txt`
- `docs/VERSIONING_RULES.md`
- `docs/UI_REFERENCE_PACKAGE_V1/**`
- `zz_BOOTSTRAP/**`
- `zz_REBUILD/**`
- existing implementation specifications

STEP 00 outputs were added only on the dedicated SOL audit branch. `main` was not modified by the audit.

## Integrity observations

1. Canonical UI materialization workflow validates all five UI references as JPEG 320x180.
2. Canonical UI ZIP SHA256 remains `2797cf5993ba6e38532d028135f5f8ab12f99bc55ed0b643b441e57ca5eeebb0`.
3. Supplied V22.5.1 rescue ZIP passed `unzip -t` with no errors.
4. Its internal 15-entry SHA256 manifest matches all 15 non-manifest files exactly: no missing, extra or mismatched entries.
5. Eight required prompt files were read completely as UTF-8 without NUL bytes or decode replacement characters.
6. `zz_BOOTSTRAP` and `zz_REBUILD` remain untouched evidence-only artifacts; they were not needed to replace the verified rescue ZIP.
7. No prompt was reconstructed from docs/changelog/conversation.

## Preservation result

`PASS`
