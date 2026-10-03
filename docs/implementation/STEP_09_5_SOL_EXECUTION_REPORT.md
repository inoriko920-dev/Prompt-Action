# STEP 09.5 — Baseline Materialization & Bootstrap

Status: **VALIDATING**

## Purpose
One-time bootstrap that resolves the V1/S001 gate before STEP 10. Exact bytes only; no Prompt reconstruction.

## Verified source
- Rescue SHA-256: `f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2`
- 16 archive members; 8 unique Prompt mappings; unsafe paths 0; nested archives 0.
- All 8 Prompt hashes matched STEP 00 protected hashes before materialization.

## Atomic canonical boundary
Allowed changes only: `app_data_revision 1 -> 2`, R1 `file/file_available`, add `B001`, link S001 to B001, and `S001 BACKUP_REQUIRED -> COMPLETE`. No V2, S002, or R2 is created.

## Backup
- Primary: `backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip`
- SHA-256: `0893ffbfcd28616673cfddc7ac8e4f655337b176794c2119f485cafc0559db02`
- Second copy: `backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip`
- Verification: ZIP reopen/path audit/manifest hashes/safe extraction/second-copy hash PASS in staging.

## Gate
T01–T40 plus full STEP 01–09 regression must pass on Windows GitHub CI before this report may be changed to PASS.
