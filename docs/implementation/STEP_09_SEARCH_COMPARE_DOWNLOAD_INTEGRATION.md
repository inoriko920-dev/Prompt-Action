# STEP 09 — SEARCH / COMPARE / DOWNLOAD INTEGRATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 08 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 09 adalah integration layer lintas halaman. Search, Compare, dan Download wajib memakai service, path policy, filename policy, capability registry, dan error model yang sama. STEP ini tidak membuat Revision/Snapshot baru, tidak membuat backup baru, dan tidak melakukan restore/rollback.

## Gate sebelum mulai

1. STEP 00–08 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo / branch / HEAD saat eksekusi; SHA planning bukan current truth bila repo berubah.
3. Canonical version data STEP 02 harus valid dan read-only untuk operasi STEP 09.
4. Dashboard, Sejarah Sistem, Per Prompt, Backup, Settings, dan Design System harus stabil.
5. Jika file target tidak tersedia, tidak dapat dibuka, atau integrity-nya tidak valid: action terkait harus `BLOCKED`/disabled; jangan membuat file pengganti.

## Tujuan

- Global search deterministic dan data-driven.
- Compare Revision untuk dua revision dari Prompt yang sama.
- Compare Snapshot berdasarkan canonical composition map.
- Download exact verified bytes untuk Prompt/backup/SHA/changelog/recovery guide.
- Shared `FilenamePolicy` + `PathSafetyPolicy`.
- Shared `CapabilityService` untuk enabled/disabled action.
- Shared progress/cancellation/error model.
- Tidak mengubah `System V / Snapshot S / Revision R`.

## Scope boleh

- `src/prompt_action/services/search/**`
- `src/prompt_action/services/compare/**`
- `src/prompt_action/services/download/**`
- shared `CapabilityService`, `FilenamePolicy`, `PathSafetyPolicy`
- UI integration pada Topbar, Dashboard, History, Per Prompt, Backup
- tests/evidence STEP 09

## Scope terlarang

- membuat Revision/Snapshot baru;
- `Tambah Revisi` — tetap STEP 10;
- membuat/verifikasi backup final — STEP 11;
- restore/rollback — STEP 12;
- mengubah corpus Prompt/legacy;
- mengubah canonical history;
- mengarang source file yang hilang.

## Global Search

Search hanya mengindeks entitas canonical/approved metadata:

- Prompt: `prompt_id`, nama, deskripsi;
- Revision: `revision_id`, change summary, reason, filename;
- Snapshot: `snapshot_id`, primary/sync change, summary;
- System;
- Backup metadata;
- Changelog metadata.

Full-text seluruh isi Prompt TXT **tidak wajib** untuk V1.

### Search contract

- Unicode-normalize + trim whitespace secara konsisten.
- Case-insensitive untuk label/identifier user-facing.
- Exact stable-ID match punya ranking tertinggi.
- Prefix/phrase > generic contains.
- Query kosong = `IDLE`, bukan tampilkan seluruh database.
- Result cap wajib ada.
- Query async/debounced/cancellable.
- Ranking deterministic; tidak random dan tidak membutuhkan AI.

Contoh ranking:

1. exact stable ID;
2. exact label/name;
3. prefix;
4. phrase/token;
5. secondary metadata;
6. tie-break dengan entity type + stable ID.

### Search UI state

`IDLE / SEARCHING / RESULTS / EMPTY / ERROR / DEGRADED`

Keyboard minimum: Arrow Up/Down, Enter, Esc; shortcut global boleh `Ctrl+K`/`Ctrl+F` jika tidak konflik.

## Compare Revision

- hanya dua Revision dari Prompt yang sama;
- source text harus berasal dari file fisik verified;
- hash mismatch / missing file = `BLOCKED`;
- baseline line-based diff; word-level highlight boleh ditambahkan;
- preserve original text;
- EOL normalization boleh untuk compare teknis tetapi harus dapat dijelaskan;
- whitespace-only change tidak boleh diam-diam dihapus;
- binary/non-text jangan dipaksa ke text diff;
- compare read-only, tidak membuat revision baru.

API contoh:

```text
RevisionCompareService.compare(prompt_id, left_revision_id, right_revision_id)
    -> RevisionCompareResult
```

## Compare Snapshot

Snapshot compare menjawab perubahan **state sistem** A → B, bukan hanya satu file.

Output minimum:

- System identity;
- Prompt revision map;
- Primary Change;
- Sync Changes;
- added/removed jika domain memang mengizinkan;
- backup metadata delta;
- human-readable summary dari canonical metadata.

UI minimum:

- `S003 vs S004`;
- ringkasan jumlah Prompt berubah/tetap;
- table per Prompt `from R -> to R`;
- badge `PRIMARY / SYNC`;
- deep-link ke Per Prompt;
- tidak ada mutation action.

## Download Service

Download berarti menyalin file yang **sudah ada dan terverifikasi**.

Artifact yang boleh:

- Prompt Revision TXT;
- Active Prompt TXT;
- existing Full Backup ZIP;
- SHA256 sidecar;
- Recovery Guide;
- Changelog.

### Integrity gate sebelum download

1. resolve entity dari stable ID, bukan raw path UI;
2. resolved source wajib berada dalam allowed roots;
3. file harus ada dan regular file;
4. jika canonical menyimpan SHA256, hash wajib cocok;
5. mismatch = `BLOCKED`;
6. copy ke temp destination;
7. finalize secara atomic;
8. optional re-hash destination untuk artifact penting.

## Path Safety Policy

Wajib menangani:

- path traversal `../`;
- symlink/junction escape;
- absolute path injection;
- overwrite conflict;
- Windows reserved names;
- long path;
- Unicode;
- destination network/removable yang unavailable.

Source roots hanya dari approved roots seperti:

```text
prompt_root
backup_root
docs_root
approved_changelog_root
```

UI tidak boleh memberikan raw source path sebagai otoritas.

## Filename Contract

Rekomendasi:

```text
Prompt-3_V1_R3.txt
Prompt-Action-V1-S004-FULL-BACKUP.zip
Prompt-Action-V1-S004-FULL-BACKUP.zip.sha256
Compare_V1_S003_vs_S004.txt              # optional export
Compare_Prompt-3_V1_R2_vs_R3.txt         # optional export
```

Snapshot tidak dimasukkan ke nama file Prompt Revision.

## Download UX

- Ready → Save dialog/default valid download folder;
- Existing destination → Replace / Keep Both / Cancel;
- Source missing → blocked;
- Hash mismatch → blocked;
- Destination unwritable → pilih folder lain;
- Large file → progress;
- Cancel → temp partial wajib dibersihkan;
- Success → final path + optional Open Folder.

Atomic pattern:

```text
destination/.tmp-<uuid>
    <- stream copy
verify optional destination hash
close/fsync
rename temp -> final
cleanup temp on error/cancel
```

## Capability Registry

Satu registry dipakai seluruh halaman.

- `SEARCH`: search service initialized;
- `COMPARE_REVISION`: dua revision valid, same Prompt, source verified;
- `COMPARE_SNAPSHOT`: dua snapshot valid + canonical map loaded;
- `DOWNLOAD_PROMPT`: selected revision file valid;
- `DOWNLOAD_BACKUP`: artifact exists dan policy mengizinkan;
- `DOWNLOAD_SHA`: sidecar exists;
- `OPEN_CHANGELOG`: file/ref exists;
- `ADD_REVISION`: **false sampai STEP 10**;
- `CREATE_BACKUP`: **false sampai STEP 11**;
- `RESTORE`: **false sampai STEP 12**.

Disabled button yang tidak obvious wajib punya `reason`/tooltip.

## Shared service API

```text
GlobalSearchService.search(query, filters, cancel_token) -> SearchResultPage
RevisionCompareService.compare(prompt_id, left_rid, right_rid) -> RevisionCompareResult
SnapshotCompareService.compare(left_sid, right_sid) -> SnapshotCompareResult
DownloadService.prepare(entity_ref) -> DownloadPlan
DownloadService.execute(plan, destination, conflict_policy, cancel_token) -> DownloadResult
CapabilityService.get(action, context) -> Capability(enabled, reason)
```

## Error family

- `SEARCH_*`: index invalid, cancelled, query error;
- `COMPARE_*`: file missing, hash mismatch, cross-prompt;
- `DOWNLOAD_*`: source missing, hash mismatch, destination unwritable;
- `PATH_*`: escape, invalid name, too long;
- `CAPABILITY_*`: dependency unavailable.

UI menampilkan pesan ringkas/actionable; log menyimpan detail teknis tanpa credential.

## Performance / cancellation

- index/query Search tidak boleh block UI thread;
- debounce sekitar 120–250 ms;
- stale query result harus dibuang;
- compare file besar async + cancellable;
- ZIP download streaming, jangan load seluruh file ke RAM;
- satu destination file tidak ditulis paralel dua job;
- cancel/failure wajib cleanup temp.

## State matrix utama

| Source State | Search | Compare | Download |
|---|---|---|---|
| VALID | Ya | Ya | Ya |
| HISTORY_ONLY | Ya | Metadata-only jika eksplisit | Tidak bila file tidak ada |
| MISSING | Metadata dapat tampil dengan warning | BLOCKED | BLOCKED |
| HASH_MISMATCH | Tampil sebagai problem | BLOCKED | BLOCKED |
| UNKNOWN | Boleh terlihat dengan warning | BLOCKED default | BLOCKED default |

## Test wajib T01–T60

### Search / navigation

- T01 exact Prompt ID;
- T02 exact Snapshot ID;
- T03 exact Revision ID;
- T04 case-insensitive name;
- T05 prefix;
- T06 phrase/token;
- T07 empty query → idle;
- T08 result cap;
- T09 deterministic ranking;
- T10 keyboard navigation;
- T11 cancel stale query;
- T12 index invalid → degraded/error;
- T13 deep-link Prompt;
- T14 deep-link Snapshot;
- T15 deep-link Backup.

### Compare

- T16 same Prompt R1 vs R2;
- T17 swap sides;
- T18 cross-Prompt rejected;
- T19 missing revision file blocked;
- T20 hash mismatch blocked;
- T21 line diff;
- T22 word highlight consistency;
- T23 whitespace-only change visible/flagged;
- T24 EOL-only handling;
- T25 snapshot composition compare;
- T26 PRIMARY delta;
- T27 SYNC delta;
- T28 same snapshot;
- T29 cross-System warning;
- T30 compare no mutation.

### Download / safety

- T31 exact-byte Prompt download;
- T32 active Prompt resolves active pointer;
- T33 missing source blocked;
- T34 hash mismatch blocked;
- T35 ZIP streaming;
- T36 SHA sidecar;
- T37 changelog;
- T38 path traversal rejected;
- T39 symlink/junction escape rejected;
- T40 absolute source injection rejected;
- T41 overwrite prompt;
- T42 Keep Both naming;
- T43 destination unwritable;
- T44 Unicode destination;
- T45 spaces;
- T46 long path;
- T47 cancel cleans temp;
- T48 failure cleans temp;
- T49 large ZIP no RAM spike;
- T50 Open Folder safe.

### Capability / UI / audit

- T51 disabled reason;
- T52 ADD_REVISION still disabled;
- T53 CREATE_BACKUP still disabled;
- T54 RESTORE still disabled;
- T55 no canonical mutation;
- T56 UI 1366×768;
- T57 DPI 150%;
- T58 keyboard/focus;
- T59 logs sanitized;
- T60 protected corpus unchanged.

## Blocking failure

- Search mengarang entity.
- Compare memakai file alternatif karena source asli hilang.
- Download berjalan saat hash mismatch.
- Path escape bisa membaca source di luar allowed root.
- Partial temp menjadi file final setelah failure/cancel.
- UI menyatakan sukses padahal output tidak ada.
- ADD_REVISION / CREATE_BACKUP / RESTORE enabled sebelum step pemiliknya.
- Search/Compare/Download memodifikasi Prompt/legacy/canonical history.
- Credential masuk index/log/export.

## Acceptance Gate

1. STEP 00–08 PASS.
2. Global Search deterministic dan navigation valid.
3. Revision compare read-only + integrity-aware.
4. Snapshot compare mencerminkan canonical composition map.
5. Download exact-byte + integrity gate bekerja.
6. Path safety / overwrite / cancellation aman.
7. Capability registry konsisten lintas halaman.
8. T01–T60 lulus sesuai blocking policy.
9. Visual integration tidak merusak master UI.
10. Protected source + canonical history tidak berubah.
11. Evidence lengkap + final live HEAD tercatat.

## Evidence wajib

```text
evidence/step09/
  head_before.txt
  head_after.txt
  test_results.md
  screenshots/
  search_cases.json
  compare_cases/
  download_cases/
  path_safety_cases.md
  performance.md
  protected_diff.txt
  final_report.md
```

## Prompt eksekusi untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 09 — SEARCH / COMPARE / DOWNLOAD INTEGRATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 09 dan master plan. Kerjakan sendiri secara SERIAL.

Sebelum coding, verifikasi STEP 00 sampai STEP 08 benar-benar PASS dan baca live repo/branch/HEAD. Jangan mengandalkan SHA planning jika repo sudah berubah.

Scope STEP 09 hanya: GlobalSearchService + index/query/ranking/navigation; RevisionCompareService; SnapshotCompareService; DownloadService; FilenamePolicy; PathSafetyPolicy; CapabilityService; shared error/progress/cancel model; dan integrasi action pada Dashboard, Sejarah Sistem, Per Prompt, Backup, serta topbar search.

Jangan membuat Revision/Snapshot baru. Jangan membuat backup baru. Jangan restore/rollback. ADD_REVISION tetap STEP 10, CREATE_BACKUP/VERIFY final tetap STEP 11, RESTORE tetap STEP 12. Jangan ubah corpus Prompt/legacy atau canonical history.

Search harus deterministic dan tidak mengarang entity. Compare Revision harus memakai dua file verified dari Prompt yang sama. Compare Snapshot harus memakai canonical composition map. Download harus copy exact verified bytes, memblokir missing/hash mismatch, memakai allowed roots, menolak path traversal/symlink escape, dan membersihkan partial file saat cancel/error.

Jalankan T01–T60, simpan evidence lengkap, screenshot state utama, bukti integrity/path-safety, dan final diff. Jika gate input tidak terpenuhi: STOP = BLOCKED. Keluarkan laporan final PASS/FAIL/BLOCKED.
```
