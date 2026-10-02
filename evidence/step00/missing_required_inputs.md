# STEP 00 — Required Input Resolution

Audited repository baseline: `main` HEAD `350e5428afe8ec435f52f12189faf7ef0e9b4ea0`.

## Previous blocker — Legacy V22.5.1

**RESOLVED.**

User supplied:

`V22_5_1_Update_1B_Dialog_Campuran,_Audit_Jangkar_Aksi_Terlewat,(1).zip`

Verification:

- size: `69158` bytes;
- SHA256: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`;
- `unzip -t`: PASS, no errors;
- extracted files: 16;
- nested archive: none;
- index declares version `V22.5.1`, date `2026-09-01`, based_on `V22.5`;
- internal manifest: 15 entries covering every non-manifest file;
- independently recomputed result: 0 missing, 0 extra, 0 mismatch;
- original hash before/after audit: identical;
- preservation-copy hash: identical.

Classification: `VERIFIED_RESCUE_ZIP / VERIFIED_SOURCE`.

## Previous blocker — Eight baseline prompts

**RESOLVED 8/8.**

Verified source files:

- Prompt 1A — SHA256 `65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5`
- Prompt 1B — SHA256 `7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf`
- Prompt 1B1 — SHA256 `a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6`
- Prompt 1B2 — SHA256 `12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576`
- Prompt 2 — SHA256 `d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98`
- Prompt 3 — SHA256 `de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8`
- Prompt 4 — SHA256 `a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0`
- Prompt 5 — SHA256 `bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786`

All eight are non-empty, fully readable as UTF-8, contain no NUL bytes, and match the V22.5.1 manifest exactly.

Prompt 1A does not include an inline `V22.5.1` marker, but the V22.5.1 index includes active workflow `1A`, its SHA256 is covered by the package manifest, and the source/audit documents explicitly state that Prompt 1A was unchanged in this update.

## Remaining required inputs

None.

The repository-native master documents, five UI references, canonical UI package, verified V22.5.1 rescue source, eight prompt corpus, preservation proof and recovery verification are all available to STEP 00.

## Gate consequence

`MISSING_REQUIRED_INPUTS = 0`

STEP 00 may be set to `PASS`, subject to final consistency/re-check and Astra/user review.
