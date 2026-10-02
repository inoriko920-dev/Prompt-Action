# STEP 11 — BACKUP ENGINE & RELEASE COMPLETION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 10 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 11 menyelesaikan release yang dibuat STEP 10. Snapshot baru tetap `BACKUP_REQUIRED` sampai Full Backup ZIP, manifest, SHA-256, primary verification, dan second-copy verification seluruhnya PASS. Baru setelah itu canonical status boleh berubah menjadi `COMPLETE`.

## Gate sebelum mulai

1. STEP 00–10 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo / branch / HEAD saat eksekusi; SHA planning bukan current truth bila repo berubah.
3. Current Snapshot wajib tepat `BACKUP_REQUIRED`.
4. Canonical data harus valid dan tidak ada release/backup transaction unresolved.
5. Semua Prompt Revision yang direferensikan current Snapshot harus tersedia sebagai regular file dan SHA-256 cocok canonical metadata.
6. Primary + second-copy destination harus valid, writable, aman, dan mempunyai ruang cukup.
7. Jika satu input wajib tidak dapat diverifikasi: STOP = `BLOCKED`.

## Tujuan

- manifest-driven Full Backup ZIP writer;
- backup manifest machine-readable;
- ZIP SHA-256 + `.sha256` sidecar;
- verification lengkap sebelum release COMPLETE;
- safe extraction staging untuk integrity test tanpa restore;
- second copy + independent recomputed hash;
- backup transaction journal + crash recovery;
- progress/cancel/retry tanpa UI freeze;
- historical verification/retention semantics;
- atomic `BACKUP_REQUIRED -> COMPLETE`.

## Scope

Boleh:
- backup planner/writer;
- manifest writer;
- SHA writer;
- verifier;
- second-copy service;
- backup journal;
- backup progress/cancel/retry;
- write backup record;
- transition target Snapshot ke `COMPLETE` bila semua blocking evidence PASS.

Terlarang:
- restore/activate extracted files sebagai live data;
- rollback Snapshot (STEP 12);
- membuat Revision/Snapshot baru (STEP 10);
- overwrite/delete official Revision/Snapshot/history;
- mengarang `AMAN`, `VALID`, atau `PASS` dari filename saja;
- menyimpan token/PAT/password/secret ke backup atau log.

## Release completion state machine

```text
STEP 10 success
    -> Snapshot = BACKUP_REQUIRED

STEP 11:
PLANNING
-> WRITING_ZIP
-> ZIP_WRITTEN
-> WRITING_HASH
-> VERIFYING_PRIMARY
-> COPYING_SECONDARY
-> VERIFYING_SECONDARY
-> COMMITTING_METADATA
-> COMPLETE

failure/cancel before metadata commit:
-> FAILED / CANCELLED / RECOVERY_REQUIRED
-> Snapshot remains BACKUP_REQUIRED
```

## Full Backup Set

Wajib termasuk:
- canonical version data + schema/version marker;
- official Prompt Revision files yang diperlukan untuk recovery library + history;
- Legacy baseline bila canonical recovery contract membutuhkannya;
- changelog/release metadata;
- recovery guide;
- backup manifest.

Tidak boleh termasuk:
- runtime logs/temp/cache;
- `.venv`;
- `.git`;
- generated cache;
- token/PAT/password/credential/secret;
- second-copy folder itu sendiri.

Backup STEP 11 adalah backup data/version history Prompt Action. Source code aplikasi tetap diproteksi melalui Git/GitHub + backup repo terpisah.

## Naming

```text
backups/
  V1/
    S005/
      Prompt-Action-V1-S005-FULL-BACKUP.zip
      Prompt-Action-V1-S005-FULL-BACKUP.zip.sha256
      Prompt-Action-V1-S005-backup-record.json
```

Second copy menggunakan struktur logical yang sama di root kedua. Historical backup dilarang silent-overwrite. Partial artifact menggunakan suffix transaction seperti `.partial-<transaction-id>` dan tidak pernah dianggap final.

## Deterministic ZIP writer

1. Bangun entry list dari manifest plan; jangan blind `zip entire folder`.
2. Semua ZIP entry relative-only, `/` separator, tanpa drive letter, UNC, `..`, absolute path, duplicate normalized path, atau reserved device path.
3. Sort entry deterministic.
4. Reject symlink/reparse/shortcut special source yang keluar allowed root.
5. Streaming read source + SHA-256 cross-check canonical metadata.
6. Fixed compression method/level + documented timestamp policy.
7. ZIP central directory harus berhasil dibaca ulang sebelum final promotion.
8. Final artifact hanya dipromosikan setelah writer close/flush dan pre-verification sukses.

## Backup manifest

Minimum field:

```json
{
  "manifest_schema": "prompt-action-backup/v1",
  "system_version": "V1",
  "snapshot_id": "S005",
  "snapshot_status_at_start": "BACKUP_REQUIRED",
  "created_at_utc": "...",
  "app_version": "...",
  "canonical_metadata_sha256": "...",
  "entries": [
    {
      "path": "prompts/V1/Prompt-3/Prompt-3_V1_R4.txt",
      "size": 18422,
      "sha256": "...",
      "logical_type": "PROMPT_REVISION"
    }
  ],
  "prompt_composition": {"P1A":"P1A-R1", "P3":"P3-R4"},
  "excluded_classes": [],
  "verification_policy": "...",
  "transaction_id": "..."
}
```

## SHA-256 contract

- hitung ZIP SHA hanya setelah final ZIP stabil;
- sidecar berasal dari final ZIP, bukan partial;
- second copy harus dibaca ulang dan dihitung SHA-nya secara independen;
- primary ZIP SHA harus sama dengan second-copy ZIP SHA;
- jika primary berubah setelah verification, backup menjadi `INVALID/DEGRADED`, bukan tetap `AMAN` dari cache.

## Verification pipeline

Blocking sebelum `COMPLETE`:

1. reopen ZIP;
2. central directory readable, tidak truncated/encrypted;
3. audit semua entry path;
4. validate manifest schema/System/Snapshot/required logical classes;
5. streaming read semua entry dan bandingkan size + SHA manifest;
6. validasi prompt composition + Revision hashes ke canonical Snapshot;
7. extract ke fresh staging memakai safe extractor;
8. hitung ulang hash extracted files;
9. parse canonical JSON dari extraction;
10. pastikan required TXT dapat dibaca UTF-8;
11. pastikan recovery guide ada;
12. copy ke second location;
13. recompute second-copy SHA dari destination bytes;
14. recheck primary + secondary tepat sebelum metadata completion.

> `VERIFY != RESTORE`. Extract staging hanya integrity test. STEP 11 dilarang mengganti current live root/current Snapshot/live Prompt files dengan hasil ekstraksi. Restore/activation adalah STEP 12.

## Second copy policy

- destination harus berbeda secara logical dari primary;
- canonicalize path dan reject alias/symlink/nested unsafe target yang kembali ke primary;
- copy via partial -> flush -> final promote;
- recompute SHA dari destination bytes;
- jika second copy unavailable/gagal/hash mismatch, Snapshot tetap `BACKUP_REQUIRED`;
- tidak ada tombol “Anggap Aman”.

## Backup transaction journal

State:
- `PLANNING`
- `WRITING_ZIP`
- `ZIP_WRITTEN`
- `VERIFYING_PRIMARY`
- `COPYING_SECONDARY`
- `VERIFYING_SECONDARY`
- `COMMITTING_METADATA`
- `COMPLETE`
- `FAILED`
- `CANCELLED`
- `RECOVERY_REQUIRED`

Journal minimum menyimpan transaction ID, snapshot ID, expected canonical hash, planned artifact paths, current phase, timestamp, dan last verified hashes. Restart dengan journal non-terminal wajib menjalankan recovery gate. Auto-resume hanya jika live Snapshot + canonical hash masih sama dan artifact state dapat dibuktikan; state ambigu menjadi `RECOVERY_REQUIRED`.

## Atomic BACKUP_REQUIRED -> COMPLETE

```text
preconditions:
  current_snapshot.id == transaction.snapshot_id
  current_snapshot.status == BACKUP_REQUIRED
  canonical_hash == transaction.expected_canonical_hash
  primary_zip.verify == PASS
  primary_zip.sha256 == second_copy.sha256
  backup_manifest.verify == PASS

atomic metadata write:
  append/update backup_record(Sxxx)
  snapshot.status = COMPLETE
  snapshot.backup_record_id = <id>
  temp write -> flush/fsync -> atomic replace
  re-read canonical metadata
  full domain validation

if re-read fails:
  RECOVERY_REQUIRED
  NEVER report COMPLETE in UI
```

## UI integration

`Buat Backup Baru` enabled hanya jika current Snapshot = BACKUP_REQUIRED, gate valid, destination valid, dan tidak ada active transaction. `Verifikasi Backup` adalah read-only verifier untuk artifact existing dan tidak membuat Snapshot baru. Status Recovery tetap BACKUP_REQUIRED selama transaction dan baru menjadi COMPLETE/AMAN setelah metadata completion PASS. Hash/copy/extract harus berjalan di worker/background job.

## Security rules

- Zip Slip protection;
- no absolute/drive/UNC/`..` entry;
- no path containment escape;
- reject unsafe symlink/reparse source;
- pre-backup secret scanner;
- no trust pada manifest tanpa byte verification;
- TOCTOU source hash recheck;
- no prompt content/token/secret di log.

## Failure rules

- disk full -> partial cleanup/quarantine; Snapshot BACKUP_REQUIRED;
- permission denied -> no completion;
- source hash changed -> fail;
- corrupt/truncated ZIP -> fail;
- manifest invalid -> fail;
- entry hash mismatch -> artifact INVALID;
- unsafe ZIP path -> security fail before extraction;
- second copy unavailable/mismatch -> no completion;
- metadata commit crash -> journal recovery; no false COMPLETE;
- cancel before commit -> Snapshot BACKUP_REQUIRED;
- filename collision -> no silent overwrite.

## Historical backup / retention

- setiap Snapshot COMPLETE memiliki backup record;
- filename existence saja bukan proof VALID;
- retention tidak boleh menghapus current primary + last verified second copy bersamaan;
- deleted historical artifact harus menjadi unavailable/retired, bukan tetap VALID;
- historical rebuild hanya jika exact source bytes masih tersedia dan cocok canonical history;
- rebuild menghasilkan artifact instance baru, tidak rewrite Snapshot history.

## Test wajib T01-T75

Wajib mencakup gate BACKUP_REQUIRED, backup set/exclusions/secret scanner, deterministic ZIP, unsafe path rejection, disk/permission/hash-change failure, manifest validation, ZIP corruption/truncation, Zip Slip prevention, safe extraction, sidecar SHA, second-copy verification, journal crash injection, atomic metadata transition, UI progress/cancel, two-instance locking, historical retention/rebuild, Unicode/spaces/long-path Windows 11, bounded-memory streaming, no secret logging, Prompt/Revision immutability, dan end-to-end `BACKUP_REQUIRED -> ZIP+SHA+VERIFY+SECOND_COPY -> COMPLETE`.

## Evidence wajib

- live repo/branch/HEAD before & after;
- target System/Snapshot + proof initial BACKUP_REQUIRED;
- backup transaction ID + journal lifecycle;
- final manifest;
- primary ZIP path/size/SHA/report;
- second-copy path/size/recomputed SHA/report;
- safe-extraction verification report;
- before/after canonical metadata diff;
- screenshots before/progress/after;
- T01-T75 matrix;
- file inventory/hash proof Prompt/Revision existing tidak berubah.

## Acceptance Gate

PASS hanya jika STEP 00-10 PASS, backup plan aman, Full Backup ZIP + SHA valid, primary verification PASS, second copy + independent hash PASS, crash/journal recovery PASS, Snapshot berubah ke COMPLETE hanya setelah seluruh evidence PASS, no-restore boundary terjaga, T01-T75 PASS, dan evidence lengkap. Jika satu blocking item gagal: **FAIL/BLOCKED** dan jangan lanjut STEP 12.

## Prompt eksekusi untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 11 — BACKUP ENGINE & RELEASE COMPLETION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 11, master implementation plan, dan execution specs STEP 00-10. Kerjakan sendiri secara SERIAL.

Sebelum implementasi, buktikan STEP 00-10 PASS, verifikasi live repo/branch/HEAD, dan pastikan current Snapshot tepat BACKUP_REQUIRED dengan canonical data + Prompt Revision hashes valid serta tidak ada unresolved transaction. Jika satu input wajib tidak dapat diverifikasi: STOP = BLOCKED.

Implementasikan manifest-driven Full Backup ZIP writer, backup manifest, ZIP SHA256 sidecar, safe path + secret scanner, verification pipeline lengkap, safe extraction staging, second-copy writer + independently recomputed SHA256, backup transaction journal + crash recovery, progress/cancel/retry, capability CREATE_BACKUP + VERIFY_BACKUP, historical verification/retention, dan atomic backup-record commit + transition BACKUP_REQUIRED -> COMPLETE hanya setelah primary + second-copy verification PASS.

Dilarang restore/activate extracted data atau rollback Snapshot, membuat Revision/Snapshot baru, overwrite history, menganggap ZIP exists = AMAN, atau menyimpan secret dalam backup/log.

Jalankan T01-T75 termasuk failure/crash injection. Simpan manifest, SHA256, verification evidence primary+secondary, journal lifecycle, screenshot, test matrix, git diff, dan before/after canonical metadata. Hasil akhir PASS/FAIL/BLOCKED. Jangan lanjut STEP 12 jika STEP 11 belum PASS.
```
