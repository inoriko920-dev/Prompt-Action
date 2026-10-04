# STEP 10 — Revision + Snapshot Release Workflow

Status: **PASS**

## Validated implementation head
- Branch: `sol/step10-revision-snapshot-release-20261004`
- Validated implementation HEAD: `14e6c5ce1fda4344d1b27b4d5243d6fd1132c74f`
- GitHub Actions run: `37197473847`
- Result: **SUCCESS**
- Evidence artifact: `step10-revision-snapshot-release-evidence`
- Artifact SHA-256: `5fb14332528df451050135c124814ab6b630df12b98a631c7533e7f24596c671`

## Entry gate
- STEP 09.5: PASS.
- Active production baseline remains `V1 / S001 / COMPLETE / B001`.
- Production `app_data_revision` remains `2`.
- All eight active Prompt files remain physically present and byte-verified.
- No unresolved production release transaction exists.
- No release dummy was written to the production corpus.

## Implemented release core
- `revision_allocator.py`: next official Revision = max official R + 1; gaps are not reused.
- `snapshot_allocator.py`: next Snapshot = max official S + 1 under the S001–S999 policy.
- `atomic_writer.py`: fsync + same-filesystem atomic replace helpers.
- `transaction_journal.py`: durable transaction phases, unresolved-transaction gate, and protection against false `ABORTED` state while placed Revision files still exist.
- `release_repository.py`: project-relative path policy, exact SHA-256, immutable create-new placement, Windows binary exact-byte write, free-space check, and exclusive release lock.
- `release_planner.py`: `COMPLETE` gate, exact active-source verification, no-op rejection, PRIMARY/SYNC rules, historical/format warnings, deterministic R/S allocation, target collision checks, and explicit confirmation token.
- `release_service.py`: staging, staged-byte verification, candidate canonical validation, immutable placement, optimistic concurrency, atomic canonical commit, post-commit verification, manifest, changelog, and recovery boundary.
- `release_recovery.py`: inspect, resume, and abort for interrupted transactions, including post-commit ambiguity.

## Release Wizard UI
The STEP 10 mutation is exposed as an import-based wizard, not as a full text editor:
1. **Primary Revision** — select Prompt, import a new UTF-8 TXT, enter summary and required reason.
2. **Sync / Affected** — optionally import TXT files only for Prompt files that actually change.
3. **Review & Compare** — show PRIMARY/SYNC `from → to`, next Snapshot, canonical target, SHA-256, and warnings.
4. **Confirm Release** — explicit confirmation before mutation.
5. **Result** — success is shown only after post-commit verification and clearly reports `BACKUP_REQUIRED`.

Implemented UI files:
- `src/prompt_action/ui/viewmodels/release_wizard_view_model.py`
- `src/prompt_action/ui/qml/dialogs/AddRevisionDialog.qml`
- `src/prompt_action/ui/qml/dialogs/ReleaseReviewDialog.qml`
- `src/prompt_action/ui/qml/dialogs/ReleaseProgressDialog.qml`
- `src/prompt_action/ui/qml/dialogs/ReleaseResultDialog.qml`

`PerPromptViewModel` now enables **Tambah Revisi** only when the live canonical gate is safe. `MainWindow.qml` refreshes Dashboard, Sejarah Sistem, Per Prompt, and Backup from canonical data after a successful fixture/real release. Topbar System/Snapshot and backup health are bound to canonical dashboard state rather than placeholders.

## Transaction and recovery guarantees
- Existing Revision files are never overwritten.
- Candidate bytes are hashed before staging, after staging, after final placement, and during post-commit validation.
- Exact LF bytes are preserved on Windows by binary final placement.
- Canonical metadata is written only after all changed Revision files exist and validate.
- Snapshot produced by STEP 10 always starts as `BACKUP_REQUIRED` with `backup_id = null`.
- A subsequent release is blocked until STEP 11 changes the current Snapshot to `COMPLETE` after backup verification.
- A crash before commit cannot expose a new Snapshot.
- A crash after metadata replacement is resolved by re-reading canonical state rather than creating a duplicate Snapshot.
- A partial multi-file placement cannot be falsely finalized as `ABORTED`; remaining placed targets force `RECOVERY_REQUIRED`, and explicit abort removes exact-hash orphans before terminalizing.

## Automated verification
Final implementation run passed all blocking stages:
- Python 3.13.16 / exact dependency lock: PASS.
- STEP 10 core T01–T70 plus UI/hardening acceptance: **81 passed**.
- Isolated visual Release Wizard capture: PASS.
- Fixture result: `S002`, `P3 R2`, `app_data_revision = 3`, status `BACKUP_REQUIRED`, `backup_id = null`.
- QML warnings during capture: none.
- STEP 09.5 regression: PASS.
- STEP 03–08 visual evidence regeneration: PASS.
- STEP 01–09 regression against the pre-bootstrap fixture: PASS.
- Production baseline restoration and hash equality check: PASS.
- Full module integration smoke: PASS.

## Visual evidence
The CI artifact contains three 1600×900 screenshots:
- `screenshots/01-add-revision-input.png`
- `screenshots/02-release-review.png`
- `screenshots/03-release-result-backup-required.png`

`ui-release-proof.json` records:
- `fixture_only: true`
- `snapshot_id: S002`
- `snapshot_status: BACKUP_REQUIRED`
- `p3_active_revision: R2`
- `production_unchanged: true`
- `qml_warnings: []`

## Production preservation
All mutation tests and visual release evidence run only on isolated temporary copies of canonical metadata and Prompt files. The checked-in production baseline remains S001 COMPLETE. Existing official Revision/Snapshot history, legacy evidence, bootstrap backup, and protected prompt bytes were not overwritten or deleted.

## STEP 10 acceptance
1. STEP 00–09 / STEP 09.5 prerequisite gate: PASS.
2. Release Wizard complete and import-based, not a prompt text editor: PASS.
3. PRIMARY/SYNC contract: PASS.
4. Deterministic monotonic R/S allocation: PASS.
5. Immutable Revision placement + exact SHA-256: PASS.
6. Snapshot composition changes only actual changed Prompt files: PASS.
7. Journal + exclusive lock + optimistic concurrency: PASS.
8. Crash recovery and failure injection: PASS.
9. Pre-commit failure preserves old canonical state: PASS.
10. Post-commit Snapshot always `BACKUP_REQUIRED`: PASS.
11. Next release blocked until current Snapshot is `COMPLETE`: PASS.
12. T01–T70 plus additional UI/partial-placement tests: PASS.
13. Existing official history/corpus preserved: PASS.
14. Evidence artifact + live validated implementation HEAD recorded: PASS.

## Handoff
**STEP 10 is complete.** The implementation is ready for STEP 11 — Full Backup Engine & Verification. STEP 11 must consume a real release whose current Snapshot is `BACKUP_REQUIRED`, create the full backup ZIP + SHA-256 + verification + second copy, and only then transition that Snapshot to `COMPLETE`.
