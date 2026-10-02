# STEP 02 — CANONICAL DATA & VERSION ENGINE

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 dan STEP 01 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 02 membangun logika domain canonical. Jangan implementasikan UI final, backup engine final, GitHub runtime sync, atau portable release pada step ini.

## Gate sebelum mulai

1. STEP 00 harus PASS.
2. STEP 01 harus PASS.
3. Verifikasi live repo / branch / HEAD saat eksekusi; planning SHA bukan kebenaran mutlak bila repo berubah.
4. Corpus prompt/legacy + UI reference tetap protected/read-only.
5. Jika source wajib tidak dapat diverifikasi: STOP = `BLOCKED`.

## Tujuan

- satu canonical source of truth untuk metadata versioning;
- pemisahan `App Version` vs `System V` vs `Snapshot S` vs `Prompt Revision R`;
- typed domain model + invariant;
- validator syntax/schema/reference/graph/domain/file-integrity/policy;
- repository read/write atomic;
- version engine untuk query + release planning;
- SHA-256 linkage ke file prompt fisik;
- schema migration yang deterministic dan tidak menyentuh isi prompt;
- tests negatif untuk data rusak/kontradiktif.

## Scope boleh

- `src/prompt_action/domain/**`
- `src/prompt_action/data/**`
- `src/prompt_action/services/version_engine.py`
- `data/version_history.json`
- `data/schema/**`
- `data/migrations/**`
- `tests/step02/**`
- `scripts/dev/validate_data.ps1`
- docs/evidence STEP 02

## Scope terlarang

- Dashboard/Sejarah Sistem/Per Prompt/Backup/Pengaturan final;
- backup/restore engine final;
- GitHub runtime sync;
- portable release;
- mengubah teks Prompt 1A–5 atau legacy V22.5.1;
- membuat revision/file historis palsu;
- menyimpan absolute developer path dalam canonical history;
- menyamakan App Version dengan System/Snapshot/Revision;
- silent repair.

## Kamus domain

- **App Version**: versi executable, mis. `0.1.0-dev`.
- **System Version**: generasi workflow prompt, mis. `V1`, `V2`.
- **Snapshot**: keadaan resmi seluruh system pada titik release, mis. `S001`.
- **Prompt Revision**: revision file prompt tertentu, mis. `P3 R1 → R2`.
- **PRIMARY CHANGE**: prompt yang menjadi alasan utama release.
- **SYNC CHANGE**: prompt lain yang benar-benar berubah karena penyesuaian kompatibilitas.
- **Legacy Source**: sumber sebelum System V1, mis. `V22.5.1`.
- **Draft**: percobaan yang belum mengubah active state.
- **File Available**: file fisik ada dan integrity check PASS.
- **BACKUP_REQUIRED**: snapshot sudah tercipta tetapi backup wajib belum valid.
- **COMPLETE**: release resmi dan backup policy terpenuhi.

## Version separation

```text
APP VERSION                 CONTENT DOMAIN
0.1.0-dev                   System V1
                             ├─ S001 Baseline
                             ├─ S002 Update Prompt 3
                             └─ S003 Update Prompt 2

Prompt 3: R1 → R2 → R3
Prompt 2: R1 → R2
```

Perubahan Prompt 3 tidak otomatis menaikkan App Version. Bugfix executable juga tidak otomatis mengubah System V/S/R.

## Layout canonical

```text
data/
├─ version_history.json
├─ schema/
│  ├─ version_history.schema.json
│  └─ schema_version.txt
├─ fixtures/
└─ migrations/

prompts/
├─ V1/
│  ├─ Prompt-1A/
│  ├─ Prompt-1B/
│  ├─ Prompt-1B1/
│  ├─ Prompt-1B2/
│  ├─ Prompt-2/
│  ├─ Prompt-3/
│  ├─ Prompt-4/
│  └─ Prompt-5/
└─ legacy/V22.5.1/
```

`version_history.json` adalah canonical domain index, tetapi file prompt fisik tetap sumber konten. Metadata tidak pernah menggantikan file prompt yang hilang.

## Root schema minimum

```json
{
  "schema_version": 1,
  "app_data_revision": 1,
  "active_system": "V1",
  "active_snapshot": "S004",
  "legacy_sources": [],
  "systems": [],
  "snapshots": [],
  "prompts": {},
  "backups": [],
  "release_policy": {},
  "integrity": {}
}
```

## ID policy

- System: `V<integer>` → `V1`, `V2`.
- Snapshot: `S<3 digit>` → `S001`, `S002`, scoped per System.
- Prompt: stable ID (`P1A`, `P1B`, `P1B1`, `P1B2`, `P2`, `P3`, `P4`, `P5`) atau stable slug yang dikunci sekali.
- Revision: `R<integer>`, scoped per Prompt + System.
- Draft: stable draft ID, tidak memakai revision resmi sebelum release.

Jangan derive identity dari label UI. Label dapat berubah, stable ID tidak.

## System contract

```json
{
  "id": "V1",
  "parent_system": null,
  "status": "ACTIVE",
  "created_from_legacy": "V22.5.1",
  "first_snapshot": "S001",
  "latest_snapshot": "S004"
}
```

## Snapshot contract

```json
{
  "id": "S004",
  "system": "V1",
  "parent_snapshot": "S003",
  "status": "COMPLETE",
  "primary_change": {"prompt_id": "P3", "from": "R2", "to": "R3"},
  "sync_changes": [
    {"prompt_id": "P1B2", "from": "R2", "to": "R3"},
    {"prompt_id": "P4", "from": "R2", "to": "R3"}
  ],
  "prompt_state": {
    "P1A":"R1", "P1B":"R1", "P1B1":"R1", "P1B2":"R3",
    "P2":"R2", "P3":"R3", "P4":"R3", "P5":"R2"
  },
  "backup_id": "BKP-V1-S004"
}
```

Snapshot wajib menyimpan complete `prompt_state` agar rekonstruksi tidak bergantung pada replay changelog.

## Prompt & Revision contract

```json
"prompts": {
  "P3": {
    "display_name": "Prompt 3",
    "active_revision": "R3",
    "revisions": {
      "R3": {
        "parent": "R2",
        "snapshot": "S004",
        "status": "ACTIVE",
        "file": "prompts/V1/Prompt-3/Prompt-3_V1_R3.txt",
        "sha256": "<64 hex>",
        "file_available": true,
        "change_role": "PRIMARY",
        "summary": ["..."],
        "reason": "..."
      }
    }
  }
}
```

`file_available=true` hanya boleh jika file aktual ada dan hash cocok.

## Legacy contract

```json
{
  "id": "V22.5.1",
  "type": "LEGACY_SOURCE",
  "file_available": true,
  "source_path": "prompts/legacy/V22.5.1/",
  "sha256_manifest": "...",
  "used_to_seed": "V1/S001"
}
```

Riwayat lama yang hanya diketahui dari changelog boleh dicatat sebagai history-only `file_available=false`. Dilarang membuat file palsu untuk mengisi gap.

## Invariant wajib

- `INV-01` tepat satu ACTIVE System.
- `INV-02` active snapshot ada pada active system dan bukan Draft.
- `INV-03` setiap non-baseline snapshot punya parent valid.
- `INV-04` Snapshot ID monoton dalam System dan tidak reuse.
- `INV-05` Revision graph acyclic.
- `INV-06` prompt active_revision = active snapshot prompt_state.
- `INV-07` PRIMARY/SYNC `from` = parent snapshot state.
- `INV-08` PRIMARY/SYNC `to` = child snapshot state.
- `INV-09` prompt yang tidak PRIMARY/SYNC tidak boleh berubah revision antar snapshot.
- `INV-10` `file_available=true` ⇒ path ada + file regular + SHA valid.
- `INV-11` COMPLETE ⇒ backup valid sesuai policy.
- `INV-12` Draft tidak mengubah active pointers.
- `INV-13` System V2 tidak dibuat hanya karena prompt revision naik.
- `INV-14` App Version bukan pengganti System/Snapshot/Revision.
- `INV-15` canonical write tidak boleh mengubah prompt content implicit.

## State machine release

```text
DRAFT
  │ promote/release
  ▼
BACKUP_REQUIRED
  │ backup + SHA256 + verify + second-copy policy PASS
  ▼
COMPLETE

BACKUP_REQUIRED ──failure──> BACKUP_FAILED
BACKUP_FAILED ──retry PASS──> COMPLETE
```

Tidak boleh langsung `DRAFT → COMPLETE`.

## Validator layers

1. Syntax — JSON parse/encoding.
2. Schema — required/type/enum/pattern.
3. Reference — referenced IDs exist.
4. Graph — cycle/parent/order.
5. Domain invariant — PRIMARY/SYNC/state consistency.
6. File integrity — path/hash/availability.
7. Policy — backup/release rules.

`validate` harus read-only. Repair adalah operasi terpisah dan tidak boleh silent.

## Error model

Gunakan stable issue code + severity:

```text
BLOCKING / ERROR / WARNING / INFO
```

Contoh:

```text
code=INV-10
entity=P3:R3
path=prompts.P3.revisions.R3.file
message=file_available=true tetapi file tidak ditemukan
```

## Repository atomic write

Contract minimum:

```text
VersionRepository
  load() -> VersionState
  validate(state) -> ValidationReport
  save(state, expected_revision) -> SaveResult
  reload() -> VersionState
```

Write policy:

1. write temp file di folder sama;
2. flush/fsync bila layak;
3. validate payload temp;
4. atomic replace canonical;
5. conflict bila expected `app_data_revision` berubah;
6. failure tidak boleh merusak canonical lama.

Canonical history menggunakan relative path, bukan `C:\Users\...`.

## VersionEngine service

Minimum query/service:

- `get_active_context()`
- `get_system_history()`
- `get_snapshot_chain(system)`
- `get_prompt_history(prompt, system)`
- `compare_revisions(prompt, a, b)`
- `validate_all()`
- `plan_release(change_set)` — preview, tidak menulis
- `commit_release(plan)` — menghasilkan BACKUP_REQUIRED setelah validasi

## Release planning algorithm

1. load + validate current canonical state;
2. exactly one PRIMARY + zero/more SYNC;
3. verify active source revisions;
4. hitung next revision untuk file yang benar-benar berubah;
5. hitung next Snapshot ID;
6. clone parent prompt_state lalu apply change;
7. recompute diff; harus identik dengan declaration PRIMARY/SYNC;
8. verify target revision files/availability sesuai workflow sah;
9. validate proposed state penuh;
10. persist sebagai `BACKUP_REQUIRED` setelah semua invariant lulus.

## Contoh — Update Prompt 3

```text
S001:
P1A R1 | P1B R1 | P1B1 R1 | P1B2 R1 | P2 R1 | P3 R1 | P4 R1 | P5 R1

S002 — PRIMARY P3
P3   R1 → R2 [PRIMARY]
P1B2 R1 → R2 [SYNC]
P4   R1 → R2 [SYNC]
P5   R1 → R2 [SYNC]
```

## Contoh — Update Prompt 2

```text
S003 — PRIMARY P2
P2 R1 → R2 [PRIMARY]
P4 R2 → R3 [SYNC]  # hanya jika isi P4 benar-benar berubah
```

## State yang harus ditolak

- metadata P3 R3 tetapi file R3 tidak ada;
- revision berubah tetapi tidak tercatat sebagai PRIMARY/SYNC;
- snapshot/revision cycle;
- COMPLETE tanpa backup valid;
- V2 dibuat karena hanya P2 direvisi;
- validator otomatis mengedit metadata agar “cocok”.

## Schema migration

- hanya mengubah metadata structure;
- tidak mengubah prompt bytes;
- backup canonical metadata sebelum migration;
- deterministic + tested + recorded;
- data tidak cukup ⇒ explicit `null`/`UNKNOWN`/`FILE_NOT_AVAILABLE`, bukan tebak;
- full validator + semantic equivalence setelah migration.

## SHA-256 integrity

- lowercase 64 hex;
- hash byte file aktual;
- mismatch active/available file = blocking;
- jangan normalize line ending diam-diam.

## Path policy

- relative project path: YA;
- absolute developer path dalam version history: TIDAK;
- external backup path: boleh di settings/runtime, bukan history;
- GitHub URL sebagai satu-satunya source: TIDAK.

## Test wajib T01–T30

- T01 parse valid canonical JSON
- T02 reject malformed JSON
- T03 reject schema missing fields
- T04 one ACTIVE system
- T05 reject missing active_snapshot
- T06 reject missing snapshot parent
- T07 reject snapshot cycle
- T08 reject revision cycle
- T09 reject active_revision mismatch
- T10 detect undeclared revision change
- T11 incorrect PRIMARY from/to
- T12 incorrect SYNC from/to
- T13 missing available file = blocking
- T14 SHA mismatch = blocking
- T15 history-only unavailable file allowed
- T16 Draft does not alter active state
- T17 deterministic P3 release plan
- T18 independent P2 release plan
- T19 deterministic next Snapshot ID
- T20 revision next-ID scoped per prompt
- T21 atomic save success
- T22 simulated save failure preserves old canonical
- T23 expected-revision conflict rejected
- T24 reload round-trip semantic equality
- T25 schema migration fixture valid
- T26 migration does not modify prompt bytes
- T27 relative paths survive relocation
- T28 COMPLETE without valid backup rejected
- T29 App Version independent from System V/S/R
- T30 CLI validator returns non-zero on blocking issue

## Corruption fixtures minimum

- `missing-parent-snapshot.json`
- `revision-cycle.json`
- `undeclared-sync-change.json`
- `missing-active-file.json`
- `sha-mismatch.json`
- `complete-without-backup.json`
- `absolute-path-leak.json`
- `schema-version-unsupported.json`

## Developer CLI target

```text
python -m prompt_action.data validate
python -m prompt_action.data inspect-active
python -m prompt_action.data inspect-prompt P3
python -m prompt_action.data plan-release --primary P3 --sync P1B2 P4
powershell -ExecutionPolicy Bypass -File scripts/dev/validate_data.ps1
```

Read-only commands harus benar-benar read-only. Plan-release default hanya preview.

## Evidence wajib

- live repo/branch/HEAD before & after;
- prerequisite PASS evidence;
- files created/changed;
- schema version + baseline data;
- valid validation report;
- minimal 5 corrupted fixture reports;
- T01–T30 result;
- protected corpus hash/diff proof;
- atomic write failure evidence;
- migration evidence;
- relocation evidence;
- final PASS/FAIL/BLOCKED.

## Acceptance Gate

PASS hanya jika:

1. STEP 00/01 PASS;
2. canonical schema/model konsisten;
3. INV-01..INV-15 enforced;
4. file/hash validation bekerja;
5. history/revision ordering deterministic;
6. atomic write failure tidak merusak canonical;
7. migration teruji dan tidak mengubah prompt bytes;
8. T01–T30 lulus;
9. protected prompt/legacy/UI reference tidak berubah;
10. evidence lengkap.

Jika satu blocking gate gagal: **STEP 02 = FAIL/BLOCKED**. Jangan lanjut STEP 03 dengan alasan “UI dulu, data nanti”.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.

Kerjakan STEP 02 — CANONICAL DATA & VERSION ENGINE untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 02, STEP 01, STEP 00, dan master implementation plan. Kerjakan sendiri secara SERIAL.

GATE WAJIB:
1. Verifikasi STEP 00 PASS dan STEP 01 PASS dengan evidence aktual.
2. Verifikasi live repo/branch/HEAD sebelum coding; jangan mengandalkan planning SHA bila repo berubah.
3. Corpus prompt/legacy dan UI reference adalah protected source. Jangan ubah isinya.
4. Jika prerequisite atau source wajib tidak dapat diverifikasi: STOP = BLOCKED.

SCOPE STEP 02 SAJA:
- System V / Snapshot S / Prompt Revision R;
- PRIMARY CHANGE / SYNC CHANGE;
- canonical JSON/schema;
- validator structural + semantic + integrity;
- repository atomic read/write;
- version engine query + release planning;
- metadata migration;
- SHA-256 integrity;
- developer validator CLI/script;
- tests T01–T30 dan corrupted fixtures.

DILARANG:
- UI final;
- backup engine final;
- GitHub runtime sync;
- portable release;
- silent repair;
- membuat ulang prompt/legacy dari metadata;
- menyamakan App Version dengan System V/S/R.

Aturan kunci: metadata tidak pernah menggantikan file prompt fisik. Jika file/hash tidak cocok, laporkan blocking issue. Validator harus read-only. Write harus atomic. COMPLETE tanpa backup valid harus ditolak.

Setelah implementasi, jalankan T01–T30, simpan evidence lengkap, buktikan protected corpus tidak berubah, lalu keluarkan laporan final PASS/FAIL/BLOCKED dan GO/NO-GO STEP 03.
```
