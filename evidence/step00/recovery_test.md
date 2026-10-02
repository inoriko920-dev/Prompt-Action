# STEP 00 — Recovery Test

Audited repository baseline: `main` HEAD `350e5428afe8ec435f52f12189faf7ef0e9b4ea0`.

## 1. Canonical UI Reference Recovery Package

Package:

`docs/UI_REFERENCE_PACKAGE_V1/Prompt-Action-UI-Reference-Materialized-V1.zip`

Observed size: `125042` bytes.

Companion SHA256:

`2797cf5993ba6e38532d028135f5f8ab12f99bc55ed0b643b441e57ca5eeebb0`

Successful `Materialize UI Reference Package` workflow proves:

- five Base64 image inputs decoded;
- five outputs recognized as JPEG image data;
- all five reported as `320x180`;
- generated DOCX files validated as DOCX/ZIP containers;
- materialized ZIP generated from the materialized reference directory;
- SHA256 generated and committed successfully.

Result: `PASS_FOR_CLAIMED_UI_REFERENCE_SCOPE`.

## 2. Verified V22.5.1 Rescue ZIP

User-supplied package:

`V22_5_1_Update_1B_Dialog_Campuran,_Audit_Jangkar_Aksi_Terlewat,(1).zip`

Size: `69158` bytes  
SHA256: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`

### Archive integrity

`unzip -t` result: **PASS — No errors detected**.

Extracted to a clean staging directory only.

Top-level package:

`V22.5.1 Prompt Per Jangkar dan Per Narasi (Update 1B Dialog-Campuran, Audit Jangkar Aksi Terlewat, Prompt 2 Per Kamera, Output JSON)`

Files: `16`  
Nested archive: `0`

### Version identity

`Indeks-Versi-V22.5.1.json` states:

- version `V22.5.1`;
- date `2026-09-01`;
- based_on `V22.5`;
- active workflow `1A, 1B, 1B1, 1B2, 2, 3, 4, 5`.

`03-Sumber-Pedoman-Pembaruan-V22.5.1.txt` records the V22.5.1 update sources and states that Prompt 1A was unchanged.

`01-Audit-Sinkronisasi-V22.txt` states `LOLOS SINKRONISASI INTERNAL` and checks the V22.5.1 workflow.

### Internal SHA256 manifest

`Manifest-SHA256-V22.5.1.txt` declares coverage of every package file except itself.

Independent verification:

- expected manifest entries: 15;
- actual non-manifest files: 15;
- missing: 0;
- extra: 0;
- mismatch: 0;
- result: `MANIFEST_MATCH = TRUE`.

### Eight required prompt sources

All required files are present and readable in full:

| Prompt | Bytes | SHA256 | Result |
|---|---:|---|---|
| 1A | 5401 | `65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5` | PASS |
| 1B | 43390 | `7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf` | PASS |
| 1B1 | 25510 | `a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6` | PASS |
| 1B2 | 19437 | `12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576` | PASS |
| 2 | 15810 | `d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98` | PASS |
| 3 | 23652 | `de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8` | PASS |
| 4 | 6514 | `a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0` | PASS |
| 5 | 6107 | `bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786` | PASS |

All eight decode as UTF-8 with no NUL bytes and no Unicode replacement-character errors.

### Preservation/repeatability

- original SHA256 before extraction: `f7ac13dd...cfdb2`;
- preservation-copy SHA256: identical;
- original SHA256 after audit: identical;
- complete 16-file extracted hash map recomputed twice: identical.

Result: `PASS`.

Classification: `VERIFIED_RESCUE_ZIP`; prompt files are `VERIFIED_SOURCE via verified rescue ZIP`.

## 3. Old UI Reference Package

`Prompt-Action-UI-Reference-Package-V1.zip`

Canonical README classifies it as an old experimental artifact.

Result: `EXCLUDE_FROM_BASELINE`.

## 4. zz_BOOTSTRAP / zz_REBUILD

These encoded chunks remain untouched as historical/recovery evidence.

Their exact decoded provenance is still `VERSION_UNKNOWN`, but they are no longer required to satisfy the STEP 00 V22.5.1 source gate because a separate verified rescue ZIP now provides the complete required legacy/prompt corpus.

Result: `EVIDENCE_ONLY / PRESERVE`.

## 5. Full STEP 00 Recovery Scope

Required scope is now proven by the combination of:

- canonical UI recovery package + successful workflow/checksum evidence;
- verified V22.5.1 rescue ZIP;
- verified internal manifest;
- all eight required prompt source files;
- preservation and repeatability evidence.

Final recovery result: **PASS**.

## 6. Safety conclusion

No original rescue file, prompt source, UI reference, workflow, bootstrap chunk or rebuild chunk was edited/deleted. No missing prompt was synthesized or reconstructed.
