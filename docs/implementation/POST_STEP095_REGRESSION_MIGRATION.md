# Post-STEP 09.5 Regression Contract Migration

Status: **MIGRATED — FINAL PR CI RUNNING**

## Why this migration exists
STEP 09.5 intentionally materialized the official Prompt Revision bytes and created verified bootstrap backup `B001`. Later baseline reconciliation also corrected Prompt 3 to the hash-exact official pre-normalization `v22.5.2` bytes.

Several older STEP 02–09 regression tests were written before those approved state transitions. They incorrectly treated mutable canonical metadata, `file_available=false`, missing backup state, or exact pre-materialization JSON hashes as permanent invariants.

## Migration rule
The regression suite now protects the durable contracts instead:
- canonical domain validation must pass;
- materialized Prompt Revision files must exist and match canonical SHA-256;
- Prompt 3 baseline must match the recovered official v22.5.2 hash;
- S001/B001 backup state must be truthfully reported as verified/SAFE;
- immutable UI/reference assets remain byte-pinned where appropriate;
- synthetic failure cases still test `BACKUP_REQUIRED`, missing files, hash mismatch, invalid graphs, and unsafe states explicitly;
- later approved steps may evolve mutable metadata without making earlier tests stale.

## Final migration corrections
- STEP 02 isolated fixtures now copy every canonical `file_available=true` Prompt Revision and use the live app-data revision rather than hard-coded pre-materialization revision numbers.
- STEP 03 pins immutable UI reference assets only; mutable baseline/canonical JSON is no longer frozen to STEP 02 byte hashes.
- STEP 04 degraded-state tests now explicitly mark the test Prompt source unavailable instead of relying on a legacy `change_role` side effect.
- STEP 05 asserts the verified `S001 / COMPLETE / B001` state and protects the reconciled B001/P3 hashes.
- STEP 09 preflight protects canonical validity, V1/S001 identity, recovered P3 hash, reconstruction policy, search readiness, and capability gates instead of obsolete JSON byte hashes.
- STEP 09.5 and STEP 10 regression workflows now validate the reconciled PR HEAD directly and prove before/after production hashes are unchanged; they no longer restore `origin/main` as a hidden pre-bootstrap fixture.

## Safety
This migration changes regression expectations, fixture construction, and CI validation strategy only. It does not create a new Prompt Revision, Snapshot, System, or release. Production canonical state remains `V1 / S001 / COMPLETE / B001`.

Full STEP 01–10 CI on PR #11 is required before integration into `main`.
