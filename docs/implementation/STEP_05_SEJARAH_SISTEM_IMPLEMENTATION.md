# STEP 05 — SEJARAH SISTEM IMPLEMENTATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 04 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> Halaman Sejarah Sistem adalah read-only audit browser. Lineage Legacy → System → Snapshot wajib berasal dari canonical data STEP 02. Jangan membuat, menebak, atau memperbaiki history di presentation layer.

## Gate sebelum mulai

1. STEP 00–04 wajib PASS.
2. Verifikasi live repo / branch / HEAD saat eksekusi.
3. Pastikan canonical `version_history` valid.
4. Pastikan master reference `02-Sejarah-Sistem` dapat dibuka.
5. Jika graph cyclic, orphan, duplicate ID, atau reference wajib invalid: STOP = `BLOCKED`.

## Tujuan

- menampilkan lineage Legacy → System → Snapshot secara jujur;
- membedakan active/current snapshot dengan selected snapshot;
- menampilkan detail snapshot: PRIMARY CHANGE, SYNC CHANGE, tanggal, alasan, status, backup evidence;
- menyediakan action intents untuk detail, changed prompts, compare, backup, changelog;
- memiliki loading / empty / invalid / degraded / error / history-only states;
- lulus visual regression terhadap master history UI;
- tidak memiliki write side-effect saat browse/select.

## Scope boleh

- `SystemHistoryPage.qml`
- `SystemTree.qml`
- `SystemNode.qml`
- `SnapshotTimeline.qml`
- `SnapshotDetailCard.qml`
- `HistoryLegend.qml`
- `history_view_model.py`
- `history_models.py`
- `tests/step05/**`
- `docs/evidence/step05/**`

## Scope dilarang

- menulis/mengedit snapshot dari history page;
- membuat System V2 atau snapshot baru;
- mengubah Prompt Revision;
- menjalankan restore/rollback actual engine;
- fake backup availability;
- hardcode `S001/S002/S003/S004` dari mockup sebagai production data;
- mengarang legacy file yang tidak ada.

## Visual contract

Master UI `02-Sejarah-Sistem` mengunci design language, bukan jumlah node sample.

Komposisi:

- sidebar/topbar memakai STEP 03;
- kiri: Pohon Sistem / lineage;
- Legacy `V22.5.1` tampil muted/archive;
- `System V1` adalah generasi aktif;
- Snapshot berada di bawah System, bukan sejajar sebagai System version;
- current snapshot punya marker tetap;
- selected snapshot punya selection state terpisah;
- kanan: Detail Snapshot;
- legend membedakan Legacy / System / Snapshot / Active / Backup Valid.

## History read model

```text
HistoryState
  status: loading|ready|empty|invalid|degraded|error
  systems: list[SystemNodeView]
  legacy_nodes: list[LegacyNodeView]
  selected_snapshot_id: str|null
  selected_snapshot: SnapshotDetailView|null
  current_system_id: str|null
  current_snapshot_id: str|null
  validation_issues: list[IssueView]
  capabilities: HistoryCapabilities
  message: str|null
```

Minimum view objects:

- `LegacyNodeView`: id, label, availability, note, source_kind
- `SystemNodeView`: id, label, active, snapshots[]
- `SnapshotNodeView`: id, label, title, ordinal, active, status, backup_health
- `SnapshotDetailView`: id, system, primary_change, sync_changes, reason, created_at, backup, changelog_ref
- `HistoryCapabilities`: compare, download_backup, open_changelog, inspect_prompts

QML dilarang membaca JSON/file domain secara langsung.

## Lineage rules

- Legacy V22.5.1 hanya source baseline/archive; jangan ubah menjadi `System V0`.
- System V1 dimulai sebagai baseline Prompt Action.
- Snapshot order memakai canonical ordinal/sequence.
- Baseline S001 tidak dipaksa punya PRIMARY CHANGE jika schema menyatakan baseline.
- Snapshot release normal mengikuti invariant PRIMARY CHANGE dari STEP 02.
- SYNC CHANGE hanya prompt yang isi aktualnya berubah.
- System V2 hanya muncul bila benar-benar ada pada canonical data.
- History-only node tanpa physical file harus muted/unavailable, bukan downloadable.
- Jangan tampilkan chain lama V21.5→V22.x ke primary tree kecuali canonical active rules memang memasukkannya.

## Snapshot selection

Default selection:

1. current snapshot bila ada;
2. jika tidak, latest valid snapshot;
3. jika tidak ada, none/empty.

Selection hanya presentation state.

```text
select_snapshot(snapshot_id)
→ validate id exists
→ update selected_snapshot_id
→ build SnapshotDetailView
→ emit stateChanged
→ NO WRITE to version_history.json
```

Detail panel harus menunjukkan:

- System;
- Snapshot;
- status;
- PRIMARY CHANGE;
- SYNC CHANGE;
- tanggal;
- alasan;
- backup/integrity state.

## PRIMARY / SYNC presentation

- Baseline S001: label `BASELINE`, jangan membuat primary palsu.
- Prompt 3 only: PRIMARY Prompt 3; sync kosong.
- Prompt 3 + dependent changes: dependent prompt tampil sebagai SYNC.
- Prompt 2 + sync P4: nama snapshot tetap mengikuti Prompt 2.
- Revision unchanged tidak boleh ditampilkan sebagai changed.
- Unknown/corrupt references → integrity warning / invalid state.

## Backup evidence

History page hanya membaca evidence, tidak membuat backup.

Backup health yang didukung:

- `VALID`
- `MISSING`
- `INVALID`
- `UNKNOWN`
- `NOT_REQUIRED` hanya jika policy explicitly mengizinkan archival legacy.

`Download Snapshot Backup` hanya aktif jika artifact path resolved, file ada, dan integrity/policy valid.

SHA256 hanya boleh tampil `VALID` jika verification benar-benar dilakukan oleh engine/evidence layer.

Artifact hilang tidak boleh menghapus snapshot history; tampilkan `Missing Artifact`.

## Navigation & actions

| Aksi | Intent | Aturan |
|---|---|---|
| Klik snapshot | select snapshot | local UI state only |
| Buka Detail | open snapshot detail | no domain write |
| Lihat Prompt yang Berubah | route ke Per Prompt/change set | STEP 06 boleh placeholder sampai PASS |
| Compare previous | compare intent | full UX bisa disempurnakan STEP 09 |
| Download Snapshot Backup | artifact download | capability-gated |
| Lihat Changelog | open changelog | disable bila ref tidak ada |
| Back Dashboard | navigate dashboard | stable route contract |

Payload route memakai stable IDs, bukan indeks visual.

## State matrix

- `LOADING`: skeleton, actions disabled, no fake snapshot sample.
- `READY`: canonical nodes + valid capabilities.
- `EMPTY`: no fake nodes.
- `INVALID_GRAPH`: explicit blocking/error surface.
- `DEGRADED`: tree browseable dengan warnings; invalid artifacts disabled.
- `ERROR`: error + safe retry.
- `HISTORY_ONLY`: muted archival node; no file action jika unavailable.

Current snapshot harus tetap terlihat walaupun selected snapshot adalah snapshot lama.

## Graph integrity

Blocking:

- cycle;
- duplicate stable ID;
- invalid duplicate ordinal jika branching tidak didukung;
- snapshot reference ke unknown revision;
- impossible parent/reference chain.

Non-structural artifact loss dapat menjadi `DEGRADED` bila graph tetap valid.

QML tidak pernah memperbaiki graph.

## Responsive / DPI / accessibility

- visual acceptance utama: 1920×1080 dan 1600×900;
- 1366×768 tetap usable;
- minimum shell width mengikuti STEP 03;
- split panel boleh stack/collapse pada breakpoint terdokumentasi;
- scaling 100%, 125%, 150%, 175%;
- keyboard selection/focus harus usable;
- selected/current/legacy tidak hanya dibedakan warna;
- long Indonesian reason text harus wrap dengan aman.

## Performance

- history 100+ snapshot tidak boleh freeze;
- gunakan virtualized list/timeline bila diperlukan;
- detail hanya dibangun untuk current selection;
- jangan re-hash artifact besar setiap selection bila evidence/cache tersedia;
- validation/sort dilakukan saat refresh read model, bukan per frame.

## Test wajib T01–T40

- T01 route opens
- T02 no hardcoded snapshot sample
- T03 legacy node maps canonical
- T04 system node maps canonical
- T05 snapshot order correct
- T06 current snapshot highlighted
- T07 selected old snapshot distinct from current
- T08 baseline snapshot no fake primary
- T09 primary change render
- T10 sync 0/1/many
- T11 reason/date/status render
- T12 backup VALID mapping
- T13 backup MISSING mapping
- T14 backup INVALID mapping
- T15 history-only legacy state
- T16 select snapshot no write
- T17 unknown snapshot select handled
- T18 open detail intent
- T19 changed prompts intent
- T20 compare previous intent
- T21 download capability valid
- T22 download disabled missing artifact
- T23 changelog capability
- T24 loading no sample nodes
- T25 empty state
- T26 invalid cycle blocked
- T27 duplicate ID blocked
- T28 orphan revision blocked
- T29 degraded missing artifact browseable
- T30 refresh deterministic
- T31 large history 100+ snapshots
- T32 1920×1080 visual
- T33 1600×900 visual
- T34 1366×768 usable
- T35 DPI 125%
- T36 DPI 150%
- T37 keyboard selection/focus
- T38 long reason wrap
- T39 Dashboard→History navigation
- T40 regression STEP 01–04

## Evidence wajib

```text
docs/evidence/step05/
  REPORT.md
  TEST_RESULTS.md
  screenshots/
    history-1600x900.png
    history-1920x1080.png
    history-1366x768.png
    history-selected-old.png
    history-invalid-graph.png
    history-degraded-backup.png
  visual_diff/
  logs/
```

## Acceptance Gate

STEP 05 PASS hanya jika:

1. lineage seluruhnya berasal dari canonical data;
2. Legacy/System/Snapshot hierarchy benar;
3. current vs selected semantics benar;
4. PRIMARY/SYNC/detail jujur;
5. artifact capability evidence-driven;
6. browse/select tidak menulis domain;
7. visual parity diterima;
8. viewport/DPI/accessibility minimum lulus;
9. evidence lengkap;
10. regression STEP 01–04 hijau.

Blocking failure → `FAIL/BLOCKED`; jangan lanjut STEP 06.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.

Kerjakan STEP 05 — SEJARAH SISTEM IMPLEMENTATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 05, master implementation plan, STEP 02 canonical data/version engine, STEP 03 design system, STEP 04 Dashboard pattern, dan master reference 02-Sejarah-Sistem. Kerjakan sendiri secara SERIAL.

Sebelum coding, verifikasi STEP 00–04 benar-benar PASS dan verifikasi live repo/branch/HEAD. Jangan mengandalkan SHA planning jika repo sudah berubah.

Implementasikan hanya halaman Sejarah Sistem: canonical lineage Legacy→System→Snapshot, snapshot selection, detail panel, PRIMARY/SYNC changes, backup/artifact capability state, legend, navigation/action intents, loading/empty/invalid/degraded/error states, responsive/DPI/accessibility, tests, dan visual evidence.

Jangan hardcode S001/S002/S003/S004 dari gambar; itu hanya sample. Jangan menulis/mengubah version history saat page load/selection. Jangan membuat snapshot baru, revision baru, backup engine final, restore/rollback, GitHub runtime write, atau memodifikasi corpus prompt/legacy/UI reference. Graph invalid harus tampil invalid/BLOCKED; jangan diperbaiki diam-diam. Button artifact wajib capability-gated dan tidak boleh fake success.

Jalankan T01–T40, visual regression terhadap master 02-Sejarah-Sistem, regression STEP 01–04, simpan evidence, lalu keluarkan laporan PASS/FAIL/BLOCKED. Jika prerequisite/canonical graph tidak valid: STOP.
```
