# STEP 10 — REVISION & SNAPSHOT RELEASE WORKFLOW

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 09 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 10 adalah mutation gate pertama. Release resmi membuat Revision baru + Snapshot baru, tetapi hasil commit wajib berstatus `BACKUP_REQUIRED`. `COMPLETE` hanya boleh diberikan setelah STEP 11 berhasil membuat dan memverifikasi backup.

## Gate sebelum mulai

1. STEP 00–09 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo / branch / HEAD saat eksekusi; planning SHA bukan current truth jika repo berubah.
3. Canonical version data STEP 02 harus valid dan tidak boleh mempunyai cycle, duplicate ID, orphan, hash mismatch, atau unresolved transaction.
4. Current snapshot wajib `COMPLETE`. Jika masih `BACKUP_REQUIRED` / `INVALID`, STOP.
5. Tidak boleh ada transaction `IN_PROGRESS` / `RECOVERY_REQUIRED`.
6. Primary Prompt harus mempunyai active revision + file fisik valid.
7. Semua Sync Prompt yang benar-benar berubah wajib mempunyai TXT baru valid.
8. Existing Revision, Snapshot, Legacy, dan UI reference tetap immutable/protected.

## Versioning contract

- System V tetap sama untuk release biasa.
- Snapshot S naik satu untuk setiap official release.
- Revision R naik **hanya** untuk Prompt yang file aktualnya berubah.
- Next official Revision = `max official R + 1`, bukan `current R + 1` jika history pernah rollback.
- Tepat satu `PRIMARY CHANGE` per release.
- `SYNC CHANGE` hanya untuk Prompt lain yang file aktualnya berubah demi kompatibilitas dengan PRIMARY.
- Prompt yang tidak berubah mempertahankan Revision sebelumnya di composition map.
- Draft tidak memakai nomor R resmi.
- Hasil STEP 10 selalu `BACKUP_REQUIRED`.

## Release Wizard

1. **Primary Revision** — pilih Prompt, lihat active Revision, pilih TXT baru, isi summary + reason.
2. **Sync/Affected** — pilih Prompt lain yang ikut berubah dan berikan TXT baru + sync reason.
3. **Review & Compare** — tampilkan from→to R, next Snapshot, diff ringkas, warning whitespace/line-ending-only.
4. **Confirm Release** — explicit confirmation atas file + metadata yang akan dibuat.
5. **Result** — success hanya setelah canonical metadata dibaca ulang dan tervalidasi.

Prompt Action tetap **Version Manager + Prompt Library + Backup Manager**, bukan full prompt editor.

## File Revision contract

- Input: regular `.txt` file.
- UTF-8 wajib valid.
- Canonical filename dibuat aplikasi, mis. `Prompt-3_V1_R5.txt`.
- Source filename user tidak dipercaya sebagai canonical path.
- Existing canonical target = blocking error; jangan overwrite.
- Hitung SHA-256 exact bytes staging dan final.
- SHA sama dengan active Revision = reject `NO_OP_PRIMARY` / invalid Sync.
- Whitespace/line-ending-only change harus diberi warning kuat.

## Primary vs Sync

- Exactly one Primary.
- Primary harus benar-benar berubah.
- Sync hanya mendapat R baru jika file benar-benar berubah.
- Prompt yang hanya “terpengaruh secara konsep” tetapi file tidak berubah tidak naik Revision.
- Independent unrelated changes sebaiknya release terpisah.
- Release label mengikuti Primary, mis. `S005 — Update Prompt 3`.

## Allocation

```text
next_snapshot = max(snapshot_number in active System) + 1
next_revision(prompt) = max(official_revision_number for prompt in active System) + 1
```

Precondition sebelum commit:

```text
expected_system_id == live.system_id
expected_current_snapshot_id == live.current_snapshot_id
expected_canonical_hash == sha256(live canonical metadata)
```

Jika live state berubah setelah wizard dibuka: `STATE_CHANGED_RELOAD_REQUIRED`.

## Snapshot composition

```text
base = composition(current_snapshot)
new = copy(base)
for changed_prompt in [PRIMARY + SYNC]:
    new[changed_prompt.prompt_id] = changed_prompt.new_revision_id

assert all required prompts have exactly one revision
assert all referenced revisions exist + hash valid
assert unchanged prompts retain previous revision
create snapshot(next_snapshot, composition=new, status=BACKUP_REQUIRED)
```

## Preflight blocking checks

- canonical valid;
- current snapshot = COMPLETE;
- no unresolved transaction;
- release lock available;
- exactly one Primary;
- Primary/Sync TXT readable + UTF-8;
- Primary/Sync files actually changed;
- target Revision filename not already present;
- target Snapshot ID not already present;
- sufficient disk space;
- settings/root path valid;
- live canonical hash still equals expected state.

## Transaction architecture

Filesystem tidak menyediakan atomic rename untuk banyak file sekaligus. Gunakan:

```text
release_txn/<txn_id>/
  journal.json
  staged/
  candidate_version_history.json
  release_manifest.json
  changelog.md
```

Transaction phase minimum:

- `PREPARING`
- `STAGED`
- `PLACING_FILES`
- `FILES_PLACED`
- `COMMITTING_METADATA`
- `COMMITTED`
- `ABORTED`
- `RECOVERY_REQUIRED`

### Commit order

1. Acquire exclusive release lock.
2. Re-read canonical metadata + expected state/hash.
3. Create journal `PREPARING`.
4. Copy Primary + Sync ke staging; verify SHA.
5. Build candidate Revision records, Snapshot, manifest, changelog.
6. Validate candidate canonical data.
7. Journal → `STAGED`.
8. Place immutable Revision files dengan create-new semantics.
9. Re-hash final files.
10. Journal → `FILES_PLACED`.
11. Write candidate canonical ke temp file di filesystem yang sama lalu atomic `os.replace`.
12. Re-open + validate canonical; current snapshot harus S baru dengan `BACKUP_REQUIRED`.
13. Confirm manifest + changelog.
14. Journal → `COMMITTED`; release lock; refresh UI.
15. Show success hanya setelah post-commit verification lulus.

## Release journal

Journal adalah recovery evidence, bukan official history. Jika startup menemukan journal yang belum `COMMITTED` / `ABORTED`, app harus menampilkan `RECOVERY_REQUIRED` dan memblokir mutation baru.

## Release state machine

```text
UI_DRAFT
→ PREFLIGHT_OK
→ TRANSACTION_STAGED
→ FILES_PLACED
→ SNAPSHOT_COMMITTED (BACKUP_REQUIRED)
→ [STEP 11] BACKUP_CREATED
→ [STEP 11] BACKUP_VERIFIED + SECOND_COPY
→ COMPLETE
```

V1 direkomendasikan membolehkan hanya **satu unfinished release**. Release baru diblok selama current snapshot `BACKUP_REQUIRED`.

## Crash recovery

- Crash sebelum STAGED → abort + cleanup staging.
- Crash setelah STAGED → resume/abort aman.
- Partial final placement → journal menunjukkan exact file/hash; snapshot belum boleh terlihat.
- Semua files placed sebelum metadata → resume metadata commit.
- Canonical temp write gagal → canonical lama harus tetap utuh.
- Crash setelah atomic metadata replace → startup re-read canonical dan tidak membuat Snapshot duplikat.
- Post-commit canonical ambigu/invalid → `RECOVERY_REQUIRED`; jangan “force success”.

## Concurrency

- Exclusive release lock wajib.
- Dua instance tidak boleh release bersamaan.
- Stale lock harus diverifikasi terhadap process + journal; jangan dihapus hanya karena usia.
- Search / Compare / Download boleh tetap read-only selama canonical konsisten.
- Settings mutation yang mengubah data root diblok selama transaction aktif.

## UI setelah release sukses

- **Per Prompt:** Revision baru menjadi ACTIVE sesuai current snapshot.
- **Sejarah Sistem:** Snapshot baru muncul.
- **Dashboard:** Snapshot Aktif / Perubahan Terakhir / Prompt Aktif refresh dari canonical.
- **Backup:** current snapshot = `BACKUP_REQUIRED`.
- **Topbar:** Snapshot berubah; backup health tidak boleh hijau/AMAN.

## No-op dan duplicate content

- Exact SHA sama dengan active Revision → reject.
- Normalized text sama tetapi byte berbeda → warning + explicit technical reason.
- Isi sama dengan old non-active Revision → warning bahwa kemungkinan intent sebenarnya rollback.
- Kembali ke isi lama tanpa perubahan adalah rollback STEP 12, bukan Tambah Revisi.

## Security / integrity

- Internal filename dibangun dari stable IDs.
- Final path harus tetap di configured Prompt root.
- `..`, alternate data stream, absolute injection, UNC/reparse escape ditolak.
- SHA-256 exact bytes staging + final.
- Revision resmi tidak boleh overwrite.
- Credential/token dilarang masuk journal, manifest, changelog, atau log.

## Service architecture

```text
src/prompt_action/
  services/
    release_planner.py
    release_service.py
    revision_allocator.py
    snapshot_allocator.py
    release_recovery.py
  data/
    transaction_journal.py
    atomic_writer.py
    release_repository.py
  ui/
    viewmodels/release_wizard_view_model.py
    qml/dialogs/AddRevisionDialog.qml
    qml/dialogs/ReleaseReviewDialog.qml
    qml/dialogs/ReleaseProgressDialog.qml
    qml/dialogs/ReleaseResultDialog.qml
  tests/step10/
  tests/fixtures/step10/
```

## API minimum

```text
plan_release(...) -> ReleasePlan
validate_plan(plan, expected_state) -> ValidationReport
commit_release(plan, explicit_confirmation_token) -> ReleaseResult
inspect_pending_transaction() -> RecoveryState | None
recover_transaction(txn_id, strategy) -> RecoveryResult
```

`plan_release` read-only. `commit_release` harus idempotency-aware.

## Error codes minimum

- `RELEASE_BUSY`
- `PREVIOUS_BACKUP_INCOMPLETE`
- `RECOVERY_REQUIRED`
- `NO_OP_PRIMARY`
- `INVALID_SYNC`
- `STATE_CHANGED_RELOAD_REQUIRED`
- `REVISION_TARGET_EXISTS`
- `SNAPSHOT_ID_CONFLICT`
- `HASH_MISMATCH`
- `CANONICAL_COMMIT_FAILED`
- `POST_COMMIT_INVALID`
- `INSUFFICIENT_SPACE`
- `PATH_POLICY_BLOCKED`
- `USER_CANCELLED`

## Test wajib

STEP 10 mempunyai **T01–T70**, meliputi:

- gate, version allocation, Primary/Sync invariants;
- no-op/UTF-8/filename/hash checks;
- snapshot composition;
- release lock + concurrency;
- transaction journal + crash recovery;
- atomic canonical write;
- post-commit UI refresh;
- whitespace/duplicate-content warning;
- path traversal/reparse safety;
- permission/read-only/disk-space failures;
- async/cancel behavior;
- proof bahwa old Revision/Snapshot tidak berubah;
- fixture-only tests tanpa mencemari corpus produksi.

## Acceptance Gate

STEP 10 PASS hanya jika:

1. STEP 00–09 PASS.
2. Release Wizard selesai dan bukan full text editor.
3. Primary/Sync rules sesuai contract.
4. Next R / next S deterministic dan monotonic.
5. Immutable Revision file creation + hash verification bekerja.
6. Snapshot composition hanya mengubah Prompt yang benar-benar berubah.
7. Journal + lock + optimistic concurrency bekerja.
8. Crash recovery/failure injection utama lulus.
9. Pre-commit failure menjaga canonical lama.
10. Post-commit Snapshot selalu `BACKUP_REQUIRED`.
11. Release berikutnya diblok sampai current Snapshot `COMPLETE`.
12. T01–T70 lulus.
13. Existing history tidak berubah/ditimpa.
14. Evidence lengkap + final live HEAD dicatat.

Jika satu blocking item gagal: **STEP 10 = FAIL/BLOCKED**. Jangan lanjut STEP 11.

## Prompt eksekusi untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 10 — REVISION & SNAPSHOT RELEASE WORKFLOW untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 10, execution spec Markdown, master plan, dan aturan versioning. Kerjakan sendiri secara SERIAL.

Sebelum coding, buktikan STEP 00–09 PASS, verifikasi live repo/branch/HEAD, current snapshot COMPLETE, canonical data valid, tidak ada unresolved transaction, dan protected corpus tetap valid. Jika tidak: STOP = BLOCKED.

Implementasikan Release Wizard Tambah Revisi berbasis import TXT, exactly one PRIMARY + optional SYNC yang benar-benar berubah, next R=max official+1, next S=max+1, candidate composition, SHA-256, no-op detection, explicit review/confirm, exclusive lock, optimistic concurrency, staging, transaction journal, recoverable file placement, immutable Revision files, atomic canonical replacement, release manifest, changelog, post-commit verification, dan UI refresh.

Snapshot hasil commit wajib BACKUP_REQUIRED. Jangan implementasikan Full Backup engine final (STEP 11), restore/rollback (STEP 12), atau System V2 otomatis. Jangan overwrite/delete history. Jangan membuat release dummy di corpus produksi hanya untuk test.

Jalankan T01–T70 pada fixture terisolasi + failure injection, simpan evidence, buktikan old official files/history tidak berubah, lalu keluarkan PASS/FAIL/BLOCKED. Jika blocking failure: STOP.
```

## Handoff ke STEP 11

STEP 11 menerima:

- release transaction yang reliable;
- current snapshot `BACKUP_REQUIRED`;
- manifest + exact file hashes;
- tidak ada concurrent/unresolved transaction;
- canonical composition valid untuk dibackup.

STEP 10 berhenti setelah official release tercatat secara konsisten sebagai `BACKUP_REQUIRED`. STEP 11 yang membuat ZIP, SHA256, verification, second copy, lalu mengubah snapshot ke `COMPLETE`.