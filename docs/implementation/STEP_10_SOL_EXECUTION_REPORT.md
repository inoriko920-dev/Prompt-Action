# STEP 10 — Revision + Snapshot Release Workflow

Status: **VALIDATING**

## Scope
Implement the mutation workflow that creates a new Prompt Revision and a new Snapshot inside the active System without creating a new System or backup. STEP 10 must leave the new Snapshot in `BACKUP_REQUIRED`; STEP 11 owns backup completion.

## Entry gate
- STEP 09.5 report: PASS.
- Active baseline: V1 / S001 / COMPLETE / B001.
- `app_data_revision`: 2.
- All eight active Prompt files are physically present and byte-verified.
- No unresolved release transaction may exist.

## Implemented core
- `revision_allocator.py`: max official R + 1, gaps never reused.
- `snapshot_allocator.py`: max official S + 1 with S001–S999 policy.
- `atomic_writer.py`: fsync + atomic replace helpers.
- `transaction_journal.py`: durable release phases and unresolved-transaction gate.
- `release_repository.py`: project path policy, exact hashes, immutable `O_EXCL` placement, free-space check, exclusive release lock.
- `release_planner.py`: COMPLETE gate, active-source verification, no-op detection, PRIMARY/SYNC validation, warning generation, target allocation, deterministic confirmation token.
- `release_service.py`: staged-byte verification, immutable file placement, candidate canonical validation, optimistic concurrency, atomic canonical commit, rollback/recovery boundary.
- `release_recovery.py`: inspect, abort, and resume paths for interrupted transactions.

## Safety model
History is append-only. Existing revision files are never overwritten. Candidate bytes are SHA-256 verified before staging, after staging, after placement, and after canonical commit. Canonical metadata is committed only after new immutable revision files exist and validate. Ambiguous post-commit outcomes become `RECOVERY_REQUIRED` rather than being guessed.

## Test gate
`tests/step10` defines T01–T70, including allocator, planner, no-op, PRIMARY/SYNC, hash drift, immutable target, exclusive lock, journal, happy-path commit, crash injection, rollback, resume, abort, and the `BACKUP_REQUIRED` hand-off to STEP 11.

This report remains VALIDATING until STEP 10 CI and prior-step regression are green at the final branch head.
