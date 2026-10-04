# Post-STEP 09.5 Regression Contract Migration

Status: **MIGRATED — AWAITING FULL PR CI**

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

## Safety
This migration changes regression expectations and fixture construction only. It does not create a new Prompt Revision, Snapshot, System, or release. Production canonical state remains `V1 / S001 / COMPLETE / B001`.

Full STEP 01–10 CI on PR #11 is required before integration into `main`.
