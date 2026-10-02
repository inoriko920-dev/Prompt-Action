# STEP 12 — RECOVERY / RESTORE / ROLLBACK

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 11 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 12 membuktikan bahwa Full Backup STEP 11 benar-benar dapat dipakai untuk memulihkan Prompt Action. Restore dan rollback tidak boleh menghapus history. Rollback selalu membuat Snapshot baru.

## Gate sebelum mulai

1. STEP 00–11 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo / branch / HEAD pada saat eksekusi.
3. Tidak boleh ada release/backup transaction unresolved.
4. Current Snapshot wajib COMPLETE sebelum rollback normal.
5. Backup source wajib memiliki ZIP + manifest + SHA256 + verification PASS atau diverifikasi ulang sebelum restore.
6. Source backup tidak boleh berada di destination staging yang akan dihapus/ditimpa.
7. Symlink/junction/reparse escape dari recovery root dilarang.
8. Jika live workspace masih sehat, activation wajib membuat Pre-Restore Safety Copy.
9. Jika source wajib tidak dapat diverifikasi: STOP = `BLOCKED`.

## Prinsip utama

- `RESTORE ≠ ROLLBACK`.
- Restore memulihkan state dari Full Backup terverifikasi.
- Rollback membuat Snapshot baru yang composition-nya menunjuk Revision/Snapshot lama.
- Revision dan Snapshot lama immutable.
- Restore tidak boleh silent-heal atau merge data live rusak dengan backup.
- Verify/dry-run tidak boleh memutasi live state.

## Mode operasi

- `VERIFY ONLY` — cek source backup tanpa activation.
- `RESTORE DRY-RUN` — staging + validation + restore plan, tanpa live mutation.
- `RESTORE ACTIVATE` — activation source verified.
- `ROLLBACK RELEASE` — membuat Snapshot baru dari Revision/Snapshot lama.
- `EMERGENCY RECOVERY` — recovery saat live canonical state tidak bisa boot.

## State recovery

```text
IDLE
→ VERIFYING_SOURCE
→ EXTRACTING_STAGING
→ VALIDATING_STAGING
→ PLAN_READY
→ PREPARING_SAFETY_COPY
→ ACTIVATING
→ POST_ACTIVATION_VALIDATE
→ COMPLETED

Failure paths:
→ FAILED_SAFE
→ ROLLBACK_ACTIVATION
→ RECOVERY_REQUIRED
```

## Restore wajib

1. Pilih source backup.
2. Hitung SHA256 ulang dan cocokkan manifest.
3. Buat recovery transaction + isolated staging.
4. Safe-extract ZIP; tolak absolute path, `../`, UNC, symlink/reparse escape, case collision, duplicate conflicting path, dan zip-bomb pattern.
5. Verifikasi manifest + hash seluruh required file.
6. Jalankan canonical validator STEP 02 pada staging.
7. Pastikan semua Prompt Revision yang dirujuk tersedia dan hash cocok.
8. Susun `RestorePlan` + current-vs-target diff.
9. User melihat dry-run dan wajib konfirmasi eksplisit.
10. Buat Pre-Restore Safety Copy.
11. Activate secara transactional dengan recovery journal.
12. Jalankan full post-activation validation.
13. PASS → `COMPLETED`; fail → rollback Safety Copy; jika rollback juga gagal → `RECOVERY_REQUIRED`.

## Recovery staging

```text
runtime/recovery/<transaction-id>/
  source/
  extracted/
  reports/
  activation/
  journal.json
  restore-plan.json
```

## Atomic activation journal

```text
PREPARING
→ SAFETY_COPY_READY
→ LIVE_QUIESCED
→ ACTIVATION_STAGED
→ SWITCHING
→ SWITCHED
→ VALIDATING
→ COMPLETED

Failure:
→ ROLLING_BACK_ACTIVATION
→ ROLLED_BACK_SAFE
atau → RECOVERY_REQUIRED
```

Jika startup menemukan journal pada state `SWITCHING`, `SWITCHED`, `VALIDATING`, atau `ROLLING_BACK_ACTIVATION`, normal boot tidak boleh lanjut sampai recovery diselesaikan deterministically.

## Rollback versioning

Rollback tidak rewind history.

```text
Current: System V1 / S004
P3 R3

User memilih kembali ke Prompt 3 R2.

Hasil resmi:
System V1 / S005
PRIMARY CHANGE: Rollback Prompt 3 R3 → R2
P3 R2
STATUS: BACKUP_REQUIRED

R3 tetap ada.
S004 tetap ada.
```

Aturan:

- target Revision/Snapshot harus official, file tersedia, dan hash valid;
- rollback selalu menghasilkan **next Snapshot**;
- nomor Revision tidak diturunkan/ditulis ulang;
- jika rollback membutuhkan sync file aktual pada Prompt lain, Prompt tersebut harus mendapat Revision baru;
- hasil rollback berstatus `BACKUP_REQUIRED` dan wajib melewati STEP 11 sebelum `COMPLETE`;
- tidak boleh menghapus Revision yang tidak lagi active.

## Primary vs second copy

- Primary valid → verify ulang lalu boleh restore.
- Primary missing/corrupt tetapi second copy valid → boleh emergency restore dari second copy setelah full verify ulang.
- Primary dan second copy hash berbeda → `BLOCKED`, jangan pilih otomatis.
- Keduanya corrupt → `BLOCKED`.

## UI tambahan

- Restore Backup Dialog
- Restore Dry-Run
- Recovery Progress
- Recovery Success
- Recovery Failed
- Rollback Dialog
- Recovery Required Screen

`Aktifkan Restore` hanya enabled jika dry-run PASS dan user memberi konfirmasi eksplisit.

## Service/API minimum

```text
RecoveryService.verify_source(path) -> RecoveryVerification
RecoveryService.prepare_restore(path) -> RestorePlan
RecoveryService.activate_restore(plan_id, confirmation) -> RecoveryResult
RecoveryService.resume_or_recover(transaction_id) -> RecoveryResult
RollbackService.plan_revision(prompt_id, revision_id, reason) -> RollbackPlan
RollbackService.plan_snapshot(snapshot_id, reason) -> RollbackPlan
RollbackService.commit(plan_id, confirmation) -> NewSnapshotResult
```

QML dilarang menulis canonical JSON, menghitung trust status, menghapus/copy recovery folders, atau menyusun next Snapshot/Revision number sendiri.

## Blocking security rules

- Zip Slip / `../` → reject.
- Absolute path / drive prefix / UNC → reject.
- Symlink/junction/reparse escape → reject.
- Case collision Windows → reject.
- Zip bomb → enforce size/count/compression limits.
- Required file missing → BLOCKED.
- Hash mismatch → BLOCKED.
- Source backup tidak boleh dimodifikasi.

## Test wajib

T01–T80 mencakup primary/second-copy verification, SHA mismatch, manifest missing, path/archive attack, staging validation, Safety Copy, crash injection, journal recovery, emergency recovery, rollback Revision/Snapshot, no-history-rewrite, BACKUP_REQUIRED setelah rollback, UI gating, disk-full/permission/AV lock, large-backup streaming, sanitization, protected-file diff, dan live HEAD evidence.

## Acceptance Gate

PASS hanya jika:

1. restore hanya menerima source verified;
2. safe extraction fail-closed;
3. dry-run tidak memutasi live state;
4. Safety Copy dibuat sebelum activation bila live masih terbaca;
5. activation journal dapat dipulihkan setelah crash;
6. post-activation full validation PASS sebelum success;
7. failure dapat rollback safe atau secara jujur masuk `RECOVERY_REQUIRED`;
8. rollback tidak menghapus/menulis ulang history lama;
9. rollback menghasilkan Snapshot baru `BACKUP_REQUIRED`;
10. UI tidak fake-success;
11. T01–T80 + evidence lengkap;
12. protected data tetap utuh.

Jika satu blocking acceptance item gagal: **STEP 12 = FAIL/BLOCKED. Jangan lanjut STEP 13.**

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.

Kerjakan STEP 12 — RECOVERY / RESTORE / ROLLBACK untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 12 dan execution spec STEP 00–11. Kerjakan sendiri secara SERIAL.

Sebelum coding, buktikan STEP 00–11 PASS, verifikasi live repo/branch/HEAD, pastikan tidak ada unresolved release/backup transaction, dan pastikan backup source dapat diverifikasi.

Implementasikan RecoveryService, safe extraction, isolated staging, full staging validation, Restore Dry-Run, Restore Plan, Pre-Restore Safety Copy, activation journal + crash recovery, post-activation validation, rollback-to-safety-copy, emergency recovery dari primary/second copy, RollbackService untuk Revision/Snapshot lama, dan UI recovery sesuai Design System.

Rollback wajib membuat Snapshot baru BACKUP_REQUIRED. Jangan extract langsung ke live folder, jangan overwrite/delete Revision/Snapshot lama, jangan rewind Snapshot number, jangan silent-heal data rusak, dan jangan lanjut jika hash/manifest/canonical graph invalid.

Jalankan T01–T80, simpan evidence, lalu keluarkan PASS / FAIL / BLOCKED. Jika satu blocking test gagal: jangan lanjut STEP 13.
```

## Handoff

STEP 13 baru boleh dimulai setelah STEP 12 PASS.

Roadmap setelah STEP 12:
- STEP 13 — GitHub Refresh / Sync
- STEP 14 — Hardening & Full Testing
- STEP 15 — Portable Windows Build
- STEP 16 — Final Acceptance & Release
