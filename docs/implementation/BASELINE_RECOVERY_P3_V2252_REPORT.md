# Baseline Recovery — Prompt 3 v22.5.2

Status: **PASS**

## Final validated state
- Scope: correct S001/P3/R1 baseline identity only.
- Recovery commit: `310e56440dd06ce7f3cd5ad8bd4f639e0489d23d`.
- Recovery CI run: `37198932300` — SUCCESS.
- Recovery artifact: `baseline-reconcile-p3-v2252-evidence` (`11302491451`).
- Artifact digest: `sha256:0ea9b660e7888b29645c96ef53571a5bac66e1f5a36846310ed7c364062b8493`.
- Incorrect previous P3 SHA-256: `de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8` (legacy v22.5.1).
- Correct P3 SHA-256: `0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1` (official pre-normalization v22.5.2 release).
- Recovered P3 size: `22320` bytes.
- Recovery proof: preserved V22.6.1 draft differed only by its version label; replacing that single label with V22.5.2 reproduced the historical release SHA-256 exactly.
- Normalization: `v22.5.2 -> V1 / S001 / P3 / R1`.
- No R2, S002, or new System was created.

## Backup reconciliation
`B001` was regenerated deterministically for the corrected S001 baseline.

- B001 SHA-256: `f04e1b69c2613bf238c547bfab9cc81ab5708c100843e13b6750ea950f33d8a6`.
- primary verification: PASS.
- second-copy verification: PASS.
- ZIP CRC/path/manifest verification: PASS.
- S001 final state: `COMPLETE / B001`.
- app_data_revision remains `2` because this was a baseline-reconciliation correction, not a new release.

## Regression proof
The recovery workflow passed:
- reconciliation script;
- STEP 09.5 bootstrap verifier;
- STEP 09.5 regression tests;
- STEP 10 preflight;
- STEP 10 regression tests;
- git diff safety;
- atomic generated-state commit.

## Handoff
Baseline recovery is complete. STEP 11 remains a separate future gate and is not part of this integration branch.
