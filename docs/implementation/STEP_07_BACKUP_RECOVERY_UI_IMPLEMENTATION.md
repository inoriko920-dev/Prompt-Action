# STEP 07 — BACKUP & RECOVERY UI IMPLEMENTATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 06 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 07 membangun UI + read-only presentation/query layer untuk Backup & Recovery. Backup ZIP writer, SHA writer, verifier final, restore/rollback, dan recovery engine mutating baru dibangun pada STEP 11–12.

## Gate sebelum mulai

1. STEP 00–06 wajib PASS.
2. Verifikasi live repo / branch / HEAD saat eksekusi.
3. Canonical version data + backup metadata wajib valid menurut STEP 02.
4. Master visual `04-Backup-Recovery.jpg` wajib dapat dibuka.
5. Jika artifact/status tidak dapat diverifikasi secara deterministic, jangan mengarang status sehat; tampilkan `BLOCKED`, `DEGRADED`, `UNKNOWN`, `BACKUP_REQUIRED`, atau `INVALID` sesuai bukti.

## Prinsip utama

- Mockup adalah kontrak visual, bukan sumber data.
- `AMAN`, `VALID`, `PASS`, `Salinan Kedua Tersedia` hanya boleh muncul jika bukti canonical + artifact mendukung.
- QML dilarang menghitung recovery health sendiri.
- Filename dilarang dipakai sebagai sumber kebenaran hubungan snapshot ↔ backup.
- Current snapshot backup dan selected history backup adalah dua konteks berbeda.
- Tidak ada fake success untuk capability yang belum tersedia.

## Scope boleh

- `src/prompt_action/ui/qml/pages/BackupRecoveryPage.qml`
- `src/prompt_action/ui/qml/backup/**`
- `src/prompt_action/viewmodels/backup_recovery_viewmodel.py`
- `src/prompt_action/presentation/backup_recovery_state.py`
- `src/prompt_action/services/backup_query_service.py`
- `tests/step07/**`
- `docs/evidence/step07/**`
- `scripts/dev/test_step07.ps1`

## Scope terlarang

- backup ZIP writer/creator final;
- SHA256 writer final untuk release baru;
- ZIP extraction / recovery engine;
- restore / rollback mutating operation;
- snapshot/revision release writer;
- GitHub sync engine;
- portable release final;
- mutasi corpus prompt/legacy.

## Recovery state contract

- `SAFE`: semua blocking requirement terbukti terpenuhi.
- `BACKUP_REQUIRED`: release/snapshot resmi ada tetapi backup final belum lengkap/terverifikasi.
- `INVALID`: checksum mismatch, ZIP invalid, metadata/artifact conflict, atau kerusakan nyata.
- `DEGRADED`: sebagian dapat dibaca, tetapi ada pemeriksaan non-blocking/permission/capability yang tidak tersedia.
- `UNKNOWN`: bukti belum cukup.
- `EMPTY`: belum ada backup resmi.
- `LOADING`: query/check sedang berjalan.

Prioritas status:

```text
INVALID > BACKUP_REQUIRED > DEGRADED > UNKNOWN > SAFE
```

`UNKNOWN` tidak pernah dianggap `SAFE`.

## Kelengkapan Recovery

Checklist wajib data-driven, bukan delapan label hardcoded. Baseline requirement:

- Prompt aktif tersimpan;
- Revision lama tersimpan;
- VERSION_DATA tersimpan;
- Changelog tersimpan;
- Full Backup ZIP;
- SHA256;
- ZIP terverifikasi;
- salinan kedua sesuai policy.

State item:
`PASS`, `FAIL`, `MISSING`, `UNKNOWN`, `NOT_REQUIRED`, `CHECKING`.

## Backup artifact presentation model

Minimal field:

```text
backup_id
system_id
snapshot_id
created_at
file_name
relative_path
size_bytes
expected_sha256
actual_sha256
checksum_state
zip_verification_state
second_copy_state
artifact_state
recovery_state
```

Relasi resmi berasal dari metadata/canonical repository, bukan parsing filename.

## Backup Terbaru

Backup Terbaru = artifact resmi paling relevan untuk **current snapshot** menurut canonical query. Bukan file dengan modified-time paling baru di folder.

Display minimum:

- filename;
- System / Snapshot;
- waktu pembuatan;
- ukuran;
- SHA256 state;
- ZIP verification state;
- second-copy state.

## Capability gating

- **Download Full Backup**: enabled hanya jika artifact existing/readable dan safe copy/export service tersedia.
- **Download SHA256**: enabled jika sidecar/checksum export tersedia.
- **Verifikasi Backup**: disabled sampai verifier STEP 11 tersedia.
- **Buka Recovery Guide**: enabled hanya jika guide benar-benar tersedia.
- **Buka Folder Backup**: enabled hanya jika folder valid.
- **Buat Backup Baru**: wajib disabled sampai STEP 11.

Tidak boleh ada dummy toast `berhasil` untuk capability yang belum tersedia.

## Riwayat Backup

Read-only audit list. Kolom baseline:

- Snapshot;
- Tanggal;
- Ukuran;
- Status;
- Aksi.

Selecting history row **tidak mengubah current snapshot / active revision / hero recovery state**. History selection hanya untuk inspeksi kecuali user masuk historical context secara eksplisit dan UI memberi label jelas.

## BackupRecoveryState

```text
load_state
current_system_id
current_snapshot_id
recovery_state
recovery_message
completeness_items[]
latest_backup
history_rows[]
selected_history_backup_id
warning_banner
capabilities
error_state
```

ViewModel melakukan mapping domain → presentation; QML hanya render state.

## Required state matrix

UI minimal harus membuktikan:

- healthy / SAFE;
- BACKUP_REQUIRED;
- checksum mismatch / INVALID;
- unreadable ZIP;
- second-copy missing;
- verifier unavailable / UNKNOWN or DEGRADED;
- no backup / EMPTY;
- malformed metadata / BLOCKED or INVALID.

## Responsive & accessibility

Target:

- 1920×1080 @100%;
- 1600×900 @100%;
- 1366×768 @100%;
- DPI 125%, 150%, 175%;
- minimum sekitar 1180×720 dengan scroll bila perlu.

Status tidak boleh hanya dibedakan lewat warna; gunakan icon + label. Disabled control harus menjelaskan alasan melalui tooltip/help text.

## Security & path safety

- jangan masukkan API key/token/credential ke backup metadata/log/UI;
- open file/folder memakai validated path dari service;
- jangan follow symlink/junction secara sembrono;
- UI STEP 07 tidak boleh delete/overwrite artifact;
- permission error harus terlihat sebagai `UNREADABLE`/error, bukan crash.

## Performance

- jangan hash ZIP besar di QML/UI thread;
- pemeriksaan berat harus async/background + `CHECKING` state;
- 100+ history rows harus tetap usable;
- refresh harus mempertahankan selected backup jika id masih valid.

## Test wajib T01–T48

Mencakup route/nav, seluruh hero state, completeness item states, current-snapshot binding, filename-not-truth, missing/unreadable artifact, checksum PASS/FAIL, verifier state, second copy, history ordering/selection/detail/performance, capability gating, path/permission handling, refresh, keyboard/accessibility, responsive + DPI, no hashing on UI thread, protected source unchanged, dan visual regression.

## Blocking failure

STEP 07 FAIL/BLOCKED jika antara lain:

- hero AMAN muncul tanpa bukti lengkap;
- QML hardcode/menghitung recovery health;
- current vs selected history tercampur;
- checksum mismatch tetap dianggap VALID;
- tombol STEP 11 memberi fake success;
- artifact missing tetapi download enabled tanpa guard;
- UI freeze karena hashing besar;
- prompt/legacy/canonical history termutasi;
- visual menyimpang jauh dari master tanpa approval;
- test blocking gagal.

## Evidence wajib

- before/after branch + HEAD;
- screenshot master vs implementation 1920×1080, 1600×900, 1366×768;
- screenshot `SAFE`, `BACKUP_REQUIRED`, `INVALID`, `EMPTY`, `UNKNOWN`;
- T01–T48 result;
- capability matrix aktual;
- performance evidence;
- git diff summary protected source;
- known limitations STEP 11/12.

## Acceptance Gate

PASS hanya jika:

1. STEP 00–06 PASS;
2. visual sesuai master + design system;
3. recovery status data-driven dan konservatif;
4. completeness checklist auditable;
5. latest backup + history benar secara semantic;
6. capability gating jujur;
7. required states tersedia;
8. responsive/DPI/accessibility lulus;
9. UI thread tidak diblok operasi berat;
10. T01–T48 lulus atau deviation non-blocking disetujui Astra;
11. protected source tidak berubah;
12. evidence + final HEAD lengkap.

## Prompt eksekusi untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 07 — BACKUP & RECOVERY UI IMPLEMENTATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 07, master implementation plan, execution specs STEP 00–06, canonical data STEP 02, design system STEP 03, dan master visual 04-Backup-Recovery.

Kerjakan sendiri secara SERIAL. Sebelum coding, verifikasi STEP 00 sampai STEP 06 benar-benar PASS dan verifikasi live repo/branch/HEAD. Jangan mengandalkan SHA planning bila repo berubah.

Scope hanya UI/presentation/read-only query Backup & Recovery. Jangan implementasikan backup ZIP writer final, SHA writer final, restore/rollback, recovery extraction, GitHub sync, atau portable release. Verifikasi Backup dan Buat Backup Baru wajib disabled/tergate sampai STEP 11 tersedia; jangan membuat fake success.

Status AMAN/VALID/PASS hanya boleh muncul dari bukti canonical + artifact yang benar-benar mendukung. Jika checksum mismatch, artifact missing/unreadable, metadata conflict, atau bukti tidak cukup, tampilkan INVALID / BACKUP_REQUIRED / DEGRADED / UNKNOWN sesuai contract. Jangan menebak dari filename atau mockup.

Jalankan T01–T48, simpan seluruh evidence, capability matrix, visual comparison, git diff, dan final HEAD. Pastikan protected prompt/legacy/canonical source tidak berubah. Keluarkan laporan PASS / FAIL / BLOCKED. Jika prerequisite atau input wajib tidak dapat diverifikasi: STOP.
```

## Handoff

STEP 08 — Pengaturan baru boleh dieksekusi setelah STEP 07 PASS.
