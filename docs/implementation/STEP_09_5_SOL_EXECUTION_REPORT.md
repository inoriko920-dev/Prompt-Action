# STEP 09.5 — Baseline Materialization & Bootstrap

Status: **PASS**

## Purpose
One-time bootstrap that resolves the V1/S001 gate before STEP 10. Exact bytes only; no Prompt reconstruction.

## Verified source
- Rescue SHA-256: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`
- 16 archive members; 8 unique Prompt mappings; unsafe paths 0; nested archives 0.
- All 8 Prompt byte streams match the STEP 00 protected SHA-256 map.
- P1B2 recovery used the exact partial ZIP prefix plus an exact historical compressed tail, accepted only after final size, CRC, UTF-8, and protected SHA-256 verification.
- `integrity.prompt_bytes_reconstructed` remains `false`.

## Materialized baseline
- Active system: `V1`
- Active snapshot: `S001`
- Snapshot status: `COMPLETE`
- Backup ID: `B001`
- `app_data_revision`: `1 -> 2`
- All 8 R1 files are materialized at canonical project-relative paths with their protected hashes unchanged.
- No V2, S002, or R2 was created.

## Cross-platform byte integrity
`prompts/**/*.txt` is marked `-text` in `.gitattributes` so Git cannot convert LF/CRLF during Windows checkout. This keeps SHA-256 verification byte-exact across CI and local Windows use.

## Backup
- Primary: `backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip`
- SHA-256: `caa83d4bbeffe73f60325526a0676e36e317f96c961c1a19f0f6008a2b9ec7f5`
- Second copy: `backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip`
- Primary and second copy have the same verified SHA-256.
- ZIP reopen, CRC/path audit, manifest entry hashes, safe extraction, canonical embedding, and second-copy verification: PASS.

## Validation
Windows GitHub CI on Python 3.13.16 completed successfully:
- STEP 09.5 final bootstrap verifier: PASS.
- STEP 09.5 T01–T40: **40/40 PASS**.
- STEP 03–08 visual/state evidence regeneration: PASS.
- STEP 01–09 regression: PASS using the preserved pre-bootstrap canonical fixture, then restoring the live STEP 09.5 production state before final verification.
- Module integration smoke: PASS.
- Final STEP 09.5 verifier after restoration: PASS.

## Result
STEP 09.5 is complete. V1/S001 is now a materialized, backed-up, byte-verified baseline and satisfies the prerequisite for STEP 10 — Revision + Snapshot Release Workflow.
