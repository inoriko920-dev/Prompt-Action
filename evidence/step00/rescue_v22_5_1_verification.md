# STEP 00 — V22.5.1 Rescue ZIP Verification

## Input

User-supplied rescue ZIP:

`V22_5_1_Update_1B_Dialog_Campuran,_Audit_Jangkar_Aksi_Terlewat,(1).zip`

Observed size: `69158` bytes  
SHA256 before extraction: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`  
SHA256 after audit: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`

The original was copied to a read-only preservation area before extraction. Original and preservation copy hashes are identical.

## ZIP integrity

`unzip -t` completed with **No errors detected**.

Extracted top-level package:

`V22.5.1 Prompt Per Jangkar dan Per Narasi (Update 1B Dialog-Campuran, Audit Jangkar Aksi Terlewat, Prompt 2 Per Kamera, Output JSON)`

The package contains 16 files and no nested ZIP/7z/RAR/TAR/GZ archive.

## Version/provenance evidence

`Indeks-Versi-V22.5.1.json` states:

- version: `V22.5.1`;
- date: `2026-09-01`;
- based_on: `V22.5`;
- active workflow: `1A, 1B, 1B1, 1B2, 2, 3, 4, 5`.

`03-Sumber-Pedoman-Pembaruan-V22.5.1.txt` records the update sources and explicitly states that Prompt 1A was unchanged and that V22.5 foundations were retained.

`01-Audit-Sinkronisasi-V22.txt` records `LOLOS SINKRONISASI INTERNAL` and checks the active Prompt 1A–5 workflow.

This is a pre-existing rescue package, not a reconstruction produced by STEP 00.

## Internal manifest verification

`Manifest-SHA256-V22.5.1.txt` contains 15 SHA256 entries and states that the manifest covers every package file except itself.

Independent recomputation produced:

- manifest entries: `15`;
- actual non-manifest files: `15`;
- missing entries: `0`;
- extra files: `0`;
- hash mismatches: `0`;
- result: **MANIFEST_MATCH = TRUE**.

## Required prompt corpus

All required source files are present, non-empty, UTF-8 readable in full, contain no NUL bytes, and decode without replacement-character errors.

| Prompt | Bytes | SHA256 |
|---|---:|---|
| Prompt 1A | 5401 | `65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5` |
| Prompt 1B | 43390 | `7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf` |
| Prompt 1B1 | 25510 | `a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6` |
| Prompt 1B2 | 19437 | `12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576` |
| Prompt 2 | 15810 | `d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98` |
| Prompt 3 | 23652 | `de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8` |
| Prompt 4 | 6514 | `a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0` |
| Prompt 5 | 6107 | `bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786` |

Prompt 1A does not contain an inline `V22.5.1` string, but the package index identifies it as the active 1A in V22.5.1 and the source/audit documents explicitly state that Prompt 1A was unchanged in the V22.5.1 update. Its SHA256 is covered by the V22.5.1 manifest.

## Repeatability

All 16 extracted files were hashed twice from staging. The two complete hash maps were identical.

Result: `PASS`.

## Classification

Package: `VERIFIED_RESCUE_ZIP`  
Legacy scope: `V22.5.1` verified  
Prompt corpus: `8/8 VERIFIED_SOURCE via verified rescue ZIP`  
Reconstructed/decompiled content: **none**

## Gate effect

This rescue ZIP resolves the previous STEP 00 blockers for:

- T00-05 Legacy V22.5.1;
- T00-06 eight-prompt corpus;
- full-source portion of T00-07 recovery package verification;
- source portion of T00-08 manifest repeatability.
