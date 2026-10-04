# Baseline Recovery — Prompt 3 v22.5.2

Status: **PASS (pending CI commit at generation time)**

- Scope: correct S001/P3/R1 baseline identity only.
- Incorrect P3 SHA: `de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8` (legacy v22.5.1).
- Correct P3 SHA: `0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1` (official v22.5.2 release).
- Recovery proof: preserved V22.6.1 draft differed only by its version label; replacing that single label with V22.5.2 reproduced the historical release SHA-256 exactly.
- No R2, S002, or new System was created.
- B001 was regenerated deterministically and both primary and second copy were independently hash-verified.
- Reconciled B001 SHA-256: `f04e1b69c2613bf238c547bfab9cc81ab5708c100843e13b6750ea950f33d8a6`.
- STEP 11 remains blocked until a future real STEP 10 release creates a current `BACKUP_REQUIRED` snapshot.
