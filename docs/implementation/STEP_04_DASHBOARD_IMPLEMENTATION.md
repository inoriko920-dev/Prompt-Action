# STEP 04 — DASHBOARD IMPLEMENTATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00, STEP 01, STEP 02, dan STEP 03 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> Master image Dashboard adalah kontrak komposisi dan visual. Nilai `V1 / S004 / R3` pada gambar hanyalah contoh data. Production Dashboard **dilarang** meng-hardcode nilai tersebut.

## Gate sebelum mulai

1. STEP 00 PASS.
2. STEP 01 PASS.
3. STEP 02 PASS.
4. STEP 03 PASS.
5. Verifikasi live repo / branch / HEAD pada saat eksekusi.
6. Master reference `01-Dashboard` dapat dibuka.
7. Canonical data valid; jika invalid/corrupt, STOP = `BLOCKED`.

## Tujuan

Menghasilkan Dashboard produksi awal yang:

- membaca state nyata dari canonical `VersionEngine`;
- memakai design system dan shell STEP 03;
- menampilkan System, Snapshot, Prompt aktif, dan backup health;
- merangkum perubahan terakhir dengan PRIMARY/SYNC;
- menampilkan prompt aktif secara data-driven;
- menampilkan backup/recovery state yang jujur;
- menyediakan navigation/action intent yang valid;
- tidak memiliki side effect domain pada load/render;
- lulus visual regression terhadap master Dashboard.

## Scope boleh

- `DashboardPage.qml`
- komponen khusus Dashboard
- Dashboard ViewModel/read model
- adapter/query service dari VersionEngine
- navigation/action capability wiring
- state loading/empty/invalid/degraded/error/healthy
- tests + screenshot evidence STEP 04

## Scope dilarang

- final Sejarah Sistem / Per Prompt / Backup / Pengaturan;
- membuat revision atau snapshot baru;
- backup engine final / restore / rollback;
- GitHub runtime write/sync;
- mengubah corpus prompt/legacy/UI reference;
- hardcode sample `V1/S004/R3` sebagai runtime data;
- fake success pada tombol backup.

## Struktur target

```text
src/prompt_action/ui/qml/pages/DashboardPage.qml
src/prompt_action/ui/qml/dashboard/DashboardKpiRow.qml
src/prompt_action/ui/qml/dashboard/RecentChangeCard.qml
src/prompt_action/ui/qml/dashboard/ActivePromptGrid.qml
src/prompt_action/ui/qml/dashboard/BackupStatusCard.qml
src/prompt_action/ui/qml/dashboard/QuickActions.qml
src/prompt_action/presentation/dashboard_view_model.py
src/prompt_action/presentation/dashboard_models.py
tests/step04/**
docs/evidence/step04/**
```

## Master visual contract

Pertahankan:

- sidebar/topbar dari STEP 03;
- 4 KPI card: System Aktif, Snapshot Aktif, Prompt Aktif, Backup;
- Perubahan Terakhir di area tengah kiri;
- Status Backup di area tengah kanan;
- Prompt Aktif grid;
- Aksi Cepat di bagian bawah;
- white-blue visual language, spacing, card hierarchy, typography, radius, status semantics.

Dilarang menambah chart, avatar/bell, atau redesign yang membuat UI tampak seperti produk lain.

## Dashboard read model

QML tidak membaca JSON mentah. Presentation layer harus memberi state yang siap-render.

```text
DashboardState
- load_state: loading | ready | empty | invalid | error
- system_label
- snapshot_label
- active_prompt_count
- backup_health
- latest_change
- active_prompts[]
- backup_checklist[]
- recovery_health
- action_capabilities
- diagnostics[]
```

Fallback harus jujur: jika System tidak tersedia, tampilkan `—`/empty/invalid state; jangan otomatis menampilkan V1.

## KPI contract

- System Aktif → canonical active system.
- Snapshot Aktif → canonical active snapshot.
- Prompt Aktif → jumlah resolved active prompt revisions.
- Backup → `AMAN | PERLU BACKUP | UNKNOWN | ERROR` berdasarkan evidence.

`AMAN` hanya boleh tampil jika seluruh requirement recovery current snapshot tervalidasi.

## Perubahan Terakhir

```text
LatestChange
- snapshot_id
- display_title
- occurred_at
- primary_change
- sync_changes[]
- reason_summary
- can_open_snapshot
```

Aturan:

- baseline tanpa perubahan tidak boleh diberi PRIMARY palsu;
- sync kosong → jangan dummy row;
- timestamp tidak ada → jangan buat tanggal contoh;
- `Lihat Snapshot` mengirim navigation intent ke Sejarah Sistem + snapshot id.

## Prompt Aktif grid

Harus data-driven, bukan 8 card hardcoded.

```text
ActivePromptItem
- prompt_id
- short_label
- display_name
- active_revision_label
- status
- file_available
- integrity_state
```

Klik prompt mengirim route intent ke Per Prompt + `prompt_id`. Integrity problem harus terlihat sebagai warning/error state.

## Backup / Recovery card

STEP 04 hanya membaca evidence. Backup engine final ada pada STEP 11.

Checklist:

- Full Backup
- SHA256
- Verifikasi ZIP
- Salinan Kedua

Capability contract:

```text
can_download_full_backup
can_open_backup_page
can_request_backup
backup_engine_available
reason_if_disabled
```

`Buat Backup Sekarang` boleh terlihat tetapi harus disabled + reason jika engine belum tersedia. Dilarang fake success.

## Quick Actions

- `Buka Prompt Aktif` → route intent ke Per Prompt (STEP 06).
- `Lihat Perubahan Terakhir` → Sejarah Sistem + snapshot (STEP 05).
- `Buat Backup Sekarang` → capability gated (STEP 11).
- `Lihat Snapshot` → Sejarah Sistem detail intent (STEP 05).
- `Download Full Backup` → enabled hanya jika evidence + path valid.

Semua tombol harus: aksi nyata, navigation intent valid, atau disabled reason.

## UI states wajib

- LOADING — tidak boleh menampilkan sample numbers.
- READY / HEALTHY — canonical data.
- EMPTY — guidance tanpa mengarang baseline.
- INVALID DATA — blocking banner + diagnostic.
- DEGRADED — sebagian data tampil, capability tertentu disabled.
- ERROR — visible error + retry bila aman.
- BACKUP REQUIRED — amber, bukan green.

Dashboard refresh harus idempotent dan tidak menulis domain history.

## Architecture

```text
VersionEngine / DataRepository
        ↓
DashboardQueryService (optional)
        ↓
DashboardViewModel / DashboardState
        ↓
DashboardPage.qml
        ↓ user intent
NavigationService / ActionService
```

- QML = presentation/simple formatting.
- Domain rules tetap di Python/domain service.
- File I/O dilarang dari QML.
- ViewModel tidak boleh menulis `version_history` pada Dashboard load.

## Responsive / DPI / accessibility

- target 1920×1080 dan 1600×900;
- usable di 1366×768;
- uji scaling 100%, 125%, 150%, 175%;
- focus ring visible;
- status tidak hanya dibedakan warna;
- long text wrap/elide terkendali;
- jangan mengecilkan font ekstrem demi layout.

## Test plan T01–T35

- T01 Dashboard route opens
- T02 no hardcoded V1/S004 fixture in production
- T03 KPI system from engine
- T04 KPI snapshot from engine
- T05 prompt count correct
- T06 backup healthy mapping
- T07 backup required mapping
- T08 unknown backup mapping
- T09 baseline no fake primary
- T10 primary change render
- T11 sync changes 0/1/many
- T12 prompt grid 8 items
- T13 dynamic prompt count
- T14 integrity warning item
- T15 Lihat Snapshot intent
- T16 prompt click intent
- T17 recent-change action intent
- T18 backup button disabled capability
- T19 download only valid file
- T20 loading no sample values
- T21 empty state
- T22 invalid-data blocking state
- T23 degraded state
- T24 error + retry
- T25 refresh idempotent
- T26 no domain write on load
- T27 1600×900 visual baseline
- T28 1920×1080 visual baseline
- T29 1366×768 usability
- T30 DPI 125%
- T31 DPI 150%
- T32 keyboard tab/focus
- T33 long text/wrap
- T34 restart retains correct read state
- T35 regression STEP 01–03 smoke

## Evidence minimum

```text
docs/evidence/step04/
  REPORT.md
  TEST_RESULTS.md
  screenshots/
    dashboard-1600x900.png
    dashboard-1920x1080.png
    dashboard-1366x768.png
    dashboard-loading.png
    dashboard-invalid.png
    dashboard-backup-required.png
  visual_diff/  # optional
  logs/         # sanitized
```

## Blocking failures

- STEP 00–03 belum PASS;
- canonical invalid tetapi UI terlihat healthy;
- production Dashboard memakai sample/hardcode;
- action aktif tanpa effect/intent;
- Dashboard load menulis domain history;
- visual master berubah besar tanpa approval;
- clipping target viewport utama;
- backup button fake success;
- protected prompt/legacy/UI reference berubah;
- blocking test gagal.

## Acceptance Gate

PASS hanya jika:

1. data widget berasal dari canonical read model;
2. health semantics jujur;
3. navigation/capability contract bekerja;
4. visual parity diterima;
5. target viewport + keyboard/DPI minimum lulus;
6. evidence lengkap;
7. regression STEP 01–03 hijau;
8. live final HEAD + diff summary dicatat.

Jika blocking failure ada: `FAIL/BLOCKED`. Jangan lanjut STEP 05 dengan alasan nanti diperbaiki.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.

Kerjakan STEP 04 — DASHBOARD IMPLEMENTATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 04, master implementation plan, STEP 02 canonical data/version engine, STEP 03 design system, dan master reference 01-Dashboard. Kerjakan sendiri secara SERIAL.

Sebelum coding, verifikasi STEP 00, STEP 01, STEP 02, dan STEP 03 benar-benar PASS serta verifikasi live repo/branch/HEAD. Jangan mengandalkan SHA planning bila repo berubah.

Implementasikan hanya Dashboard: KPI System/Snapshot/Prompt/Backup, Perubahan Terakhir dengan PRIMARY/SYNC, Prompt Aktif grid, Status Backup/Recovery, Quick Actions, DashboardViewModel/read model, loading/empty/invalid/degraded/error states, navigation/action capability wiring, tests, dan visual evidence.

Jangan hardcode V1/S004/R3 dari gambar. Nilai pada gambar hanya sample. Data runtime wajib berasal dari canonical VersionEngine. Jangan implementasikan halaman Sejarah Sistem, Per Prompt, Backup, Pengaturan secara final; jangan membuat revision/snapshot; jangan membuat backup engine final; jangan GitHub runtime write; jangan mengubah corpus prompt/legacy/UI reference.

Button yang engine-nya belum tersedia harus capability-gated/disabled dengan alasan; dilarang fake success. Jalankan T01–T35, buat screenshot evidence untuk target viewport/state, cek regression STEP 01–03, lalu keluarkan laporan PASS/FAIL/BLOCKED. Jika prerequisite atau canonical data tidak valid: STOP.
```
