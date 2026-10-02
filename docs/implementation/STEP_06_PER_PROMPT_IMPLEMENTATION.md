# STEP 06 — PER PROMPT IMPLEMENTATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 05 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> Halaman Per Prompt adalah read-only revision explorer. ACTIVE revision dan SELECTED revision adalah dua konsep berbeda. Production UI dilarang hardcode Prompt 3 / R3 / S004 dari mockup.

## Gate sebelum mulai

1. STEP 00–05 wajib PASS.
2. Verifikasi live repo / branch / HEAD saat eksekusi.
3. Canonical prompt registry + revision graph harus valid.
4. Master reference `03-Per-Prompt` harus dapat dibuka.
5. Jika cycle/orphan/duplicate/active-pointer invalid: STOP = `BLOCKED`.

## Tujuan

- prompt selector data-driven;
- official revision graph;
- ACTIVE vs SELECTED semantics;
- draft/experiment branch terpisah dari Revision R resmi;
- revision detail dari canonical metadata;
- PRIMARY/SYNC role + affected prompts;
- file availability + SHA-256 integrity state;
- navigation/action intents dengan capability gating;
- loading/empty/invalid/degraded/error states;
- visual regression + tests.

## Prinsip wajib

- QML tidak membaca JSON/filesystem langsung.
- Prompt 3 pada mockup hanya contoh.
- Active revision berasal dari mapping current snapshot.
- Selected revision hanya revision yang sedang dilihat user.
- Draft tidak mengonsumsi nomor R resmi.
- Change summary tidak boleh diarang UI.
- Filename tidak menentukan revision identity.
- Missing/hash-mismatch file harus men-disable download.
- Browse/select tidak boleh menulis canonical history atau prompt file.
- Presentation layer tidak boleh memperbaiki revision graph.

## File target disarankan

```text
src/prompt_action/ui/qml/pages/PerPromptPage.qml
src/prompt_action/ui/qml/per_prompt/PromptSelector.qml
src/prompt_action/ui/qml/per_prompt/RevisionTree.qml
src/prompt_action/ui/qml/per_prompt/RevisionNode.qml
src/prompt_action/ui/qml/per_prompt/DraftNode.qml
src/prompt_action/ui/qml/per_prompt/RevisionDetailCard.qml
src/prompt_action/ui/qml/per_prompt/AvailableFilesCard.qml
src/prompt_action/presentation/per_prompt_view_model.py
src/prompt_action/presentation/per_prompt_models.py
tests/step06/**
docs/evidence/step06/**
```

## Read model minimum

```text
PerPromptState
  status
  prompts
  selected_prompt_id
  active_revision_id
  selected_revision_id
  official_revisions
  drafts
  selected_revision
  available_files
  capabilities
  issues
```

## ACTIVE vs SELECTED

- `ACTIVE` = revision yang dipakai current snapshot.
- `SELECTED` = revision yang sedang dilihat user.
- Jika user memilih revision historis, marker ACTIVE tetap berada pada current revision.
- Detail panel selalu mengikuti SELECTED.
- `Download Prompt Aktif` menargetkan ACTIVE; `Download Revision Ini` menargetkan SELECTED.

## Draft

- draft bukan `R` resmi;
- draft memiliki stable draft ID;
- draft branch dapat menunjuk parent revision;
- create/edit/delete draft bukan scope STEP 06.

## File state

`VALID | MISSING | HASH_MISMATCH | HISTORY_ONLY | UNKNOWN`

Action file hanya aktif bila evidence/capability mendukung.

## Capability gating

- Download: hanya jika file valid + download/file-copy capability nyata tersedia.
- Compare: hanya jika compare capability tersedia.
- Lihat Snapshot: boleh aktif melalui STEP 05.
- Changelog: hanya jika capability/view tersedia.
- Tambah Revisi: tetap disabled sampai STEP 10.

Dilarang fake success.

## Test wajib T01–T45

Mencakup route, no-hardcode, selector canonical, active/selected semantics, draft branch, graph validation, PRIMARY/SYNC, change items, affected prompts, file integrity, capability gating, no-write behavior, states, responsive/DPI, accessibility, visual regression, dan regression STEP 01–05.

## Acceptance Gate

PASS hanya jika:

1. STEP 00–05 PASS;
2. selector + revision graph berasal dari canonical data;
3. ACTIVE/SELECTED jelas;
4. draft terpisah dari official R;
5. detail/change/sync/file state jujur;
6. capability gating tidak fake;
7. browse/select read-only;
8. visual parity diterima;
9. tests/evidence lengkap;
10. regression STEP 01–05 hijau.

Jika satu blocking condition gagal: **FAIL/BLOCKED**. Jangan lanjut STEP 07.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.
Kerjakan STEP 06 — PER PROMPT IMPLEMENTATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 06, master plan, STEP 02 canonical engine, STEP 03 design system, STEP 04 Dashboard, STEP 05 History, dan master 03-Per-Prompt. Kerjakan SERIAL.

Verifikasi STEP 00–05 PASS dan live repo/branch/HEAD sebelum coding. Implementasikan hanya read-only Per Prompt: prompt selector data-driven, official revision graph, ACTIVE vs SELECTED, draft branch, revision detail, canonical change items, PRIMARY/SYNC, affected prompts, file availability/integrity, snapshot navigation, capability-gated actions, states, responsive/DPI/accessibility, tests, dan visual evidence.

Jangan hardcode Prompt 3/R3/S004. Jangan edit prompt, create revision/draft/snapshot, rollback, atau fake Download/Compare/Release. Add Revision tetap disabled sampai STEP 10. Graph invalid = BLOCKED; jangan repair diam-diam. Browse/select tidak boleh menulis data.

Jalankan T01–T45 + regression STEP 01–05. Simpan evidence dan laporkan PASS/FAIL/BLOCKED.
```
