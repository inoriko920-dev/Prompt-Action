# STEP 08 — PENGATURAN IMPLEMENTATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 07 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 08 membangun Settings UI + validation + persistence layer. Settings aplikasi adalah konfigurasi operasional dan tidak boleh mengubah System V, Snapshot S, Revision R, history, atau isi Prompt.

## Gate sebelum mulai

1. STEP 00–07 wajib PASS.
2. Verifikasi live repo / branch / HEAD saat eksekusi.
3. Master visual `05-Pengaturan.jpg` harus dapat dibuka.
4. Design System STEP 03 harus stabil.
5. Canonical data STEP 02 dan corpus Prompt/legacy tetap protected/read-only.
6. Jika current settings rusak, jangan menebak nilai lama; gunakan safe handling + error/degraded state.

## Tujuan

- halaman Pengaturan sesuai master visual putih-biru;
- typed settings model + defaults + validator;
- draft state vs persisted state;
- atomic persistence + rollback-on-write-failure;
- folder Root / Prompt / Backup + second-copy location;
- backup policy settings tanpa menjalankan backup engine final;
- GitHub repo/branch config tanpa credential di file settings;
- Light theme, UI scale, tree density;
- Advanced: Buka Log, Reset Layout, Export Diagnostics dengan sanitization;
- T01–T50 + evidence.

## Batas domain

Settings boleh mengubah konfigurasi operasional saja. Settings **dilarang** mengubah System V, Snapshot S, Prompt Revision R, PRIMARY/SYNC change, active revision, isi Prompt, checksum Prompt, dan revision history.

## Struktur target

```text
src/prompt_action/settings/
  models.py
  defaults.py
  validator.py
  repository.py
  sanitization.py
  diagnostics.py

src/prompt_action/ui/viewmodels/settings_view_model.py
src/prompt_action/ui/qml/pages/SettingsPage.qml
src/prompt_action/ui/qml/settings/*.qml

tests/step08/**
scripts/dev/test_step08.ps1
docs/evidence/step08/**
```

## Settings model minimum

```text
general:
  root_dir
  prompts_dir
  backup_dir

backup:
  backup_on_release
  write_sha256
  verify_after_write
  second_copy_enabled
  second_copy_dir

github:
  repository
  branch

appearance:
  theme
  ui_scale
  tree_density

advanced:
  diagnostics_dir
  log_level

meta:
  schema_version
  saved_at
  app_version
```

## Persistence contract

- UI mengedit **draft settings**.
- Belum ada file ditulis sebelum `Simpan Pengaturan`.
- Save flow: validate all → temp write → flush/fsync bila relevan → atomic replace → reload/verify.
- Jika write gagal, settings lama wajib tetap utuh.
- `Kembalikan/Batal` membuang draft dan reload persisted settings.
- Jangan partial-save per field pada V1.

## Path validation

Blocking/warning minimum:

- path kosong;
- Prompt folder tidak readable;
- Backup folder tidak writable;
- second-copy folder sama dengan primary backup folder;
- folder berada di runtime temp;
- path dengan spasi/non-ASCII wajib didukung;
- network/removable path boleh tetapi readiness check tidak boleh freeze UI.

STEP 08 **tidak memindahkan file** saat user mengganti path. Perubahan settings hanya mengganti target konfigurasi.

## Backup policy

Recommended V1:

- Backup setiap release: ON;
- SHA256: LOCKED ON;
- Verify ZIP after write: LOCKED ON;
- Second copy: ON jika location valid.

Toggle di STEP 08 hanya menyimpan policy. Backup ZIP/SHA/verifier final baru STEP 11.

## GitHub settings

- Repository memakai format `owner/name`.
- Branch wajib non-empty.
- Jangan simpan PAT/token/password/cookie/OAuth secret di `settings.json`, log, atau diagnostics.
- `Buka Repository` boleh aktif jika URL aman dapat dibentuk.
- `Tes Koneksi` wajib capability-gated sampai service nyata tersedia; jangan fake success.
- GitHub bukan satu-satunya backup.

## Tampilan

- Theme V1: `Light — Prompt Action Blue`.
- Dark mode belum scope.
- UI Scale default 100%; value di luar range aman harus reject/clamp secara eksplisit.
- Tree Density: `Comfortable` default, `Compact` opsional.
- Jika perubahan membutuhkan restart, tampilkan `restart required` secara jelas.

## Advanced

### Buka Log
Membuka folder log STEP 01; jika tidak ada, tampilkan error tanpa crash.

### Reset Layout
Hanya mereset preference layout/window/density/scale. Tidak boleh menyentuh versioning, Prompt files, backup artifacts, atau GitHub config.

### Export Diagnostics
Boleh berisi app/OS/Qt versions, feature flags, sanitized settings, path readiness, error summary. Harus menghapus token/password/auth header/cookie/environment secret dan tidak mengekspor isi Prompt penuh.

## ViewModel minimum

```text
SettingsPageState:
  persisted_settings
  draft_settings
  is_dirty
  validation_errors[]
  validation_warnings[]
  save_state: IDLE | VALIDATING | SAVING | SUCCESS | ERROR
  github_capability
  path_capabilities
  restart_required
  can_save
  can_revert
  last_saved_at
```

## Action contract

- Pilih Folder → picker → validate → update draft only.
- Toggle policy → draft only.
- Simpan Pengaturan → validate all → atomic persist → reload verify.
- Kembalikan → discard draft.
- Tes Koneksi → real capability-gated service only.
- Buka Repository → safe derived URL.
- Reset Layout → confirmation + layout-only reset.
- Export Diagnostics → sanitize + write export.

## Scope terlarang

- mengubah canonical version history;
- mengedit/migrasi isi Prompt;
- full backup ZIP/SHA final (STEP 11);
- restore/rollback (STEP 12);
- GitHub refresh/sync engine final (STEP 13);
- portable final packaging (STEP 15);
- menyimpan credential di repo/settings/log/diagnostics.

## Test wajib T01–T50

Coverage minimum: route + visual parity; settings load/default/draft/dirty/revert/save; atomic write success/failure; schema parse handling; spaces/Unicode/external/internal paths; read/write permissions; second-copy validation; backup policy locked requirements; GitHub repo/branch validation + honest capability gating; no secrets in settings/log/diagnostics; Light theme/UI scale/tree density; Reset Layout scope; Export Diagnostics sanitization; responsive 1920×1080, 1600×900, 1366×768; DPI 100/125/150/175; keyboard focus/tab order; no regression STEP 04–07; protected canonical/Prompt files unchanged.

## Acceptance Gate

PASS hanya jika:

1. STEP 00–07 PASS;
2. visual sesuai master + Design System;
3. draft vs persisted state benar;
4. validation benar dan tidak silent-fix;
5. atomic persistence lulus dan failure tidak merusak file lama;
6. credential tidak disimpan;
7. capability gating GitHub/backup jujur;
8. blocking T01–T50 lulus;
9. tidak ada regression Dashboard/History/Per Prompt/Backup UI;
10. canonical data + Prompt files tidak berubah;
11. evidence lengkap + final HEAD tercatat.

Jika satu blocking item gagal: **FAIL/BLOCKED**. Jangan lanjut STEP 09 dengan catatan “nanti diperbaiki”.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.
Kerjakan STEP 08 — PENGATURAN IMPLEMENTATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 08 dan master plan. Kerjakan sendiri secara SERIAL.

Sebelum coding: verifikasi STEP 00–07 PASS, live repo/branch/HEAD, master visual 05-Pengaturan.jpg, dan pastikan canonical version data + corpus Prompt tetap protected/read-only.

Scope: Settings model/defaults/validator/atomic repository; halaman Pengaturan; folder Root/Prompt/Backup + second copy; backup policy tanpa backup engine final; GitHub repo/branch + capability-gated status/test; Light theme, UI scale, tree density; Buka Log, Reset Layout, Export Diagnostics dengan sanitization; draft/dirty/save/revert; T01–T50 + evidence.

Larangan: jangan ubah System/Snapshot/Revision atau isi Prompt/legacy; jangan membuat ZIP/SHA final (STEP 11); jangan restore/rollback (STEP 12); jangan membuat GitHub sync final (STEP 13); jangan simpan credential; jangan tampilkan status Terhubung/success tanpa bukti service nyata.

Save wajib atomic; jika gagal settings lama tetap utuh. Jika current settings rusak, gunakan safe handling, jangan menebak atau overwrite otomatis. Setelah selesai keluarkan PASS/FAIL/BLOCKED. Jika prerequisite tidak PASS: STOP.
```

## Next Step

Setelah STEP 08 PASS → **STEP 09 — SEARCH / COMPARE / DOWNLOAD INTEGRATION**.
