# STEP 00 — BASELINE & RECOVERY GATE

**Prompt Action — ASTRA → SOL**  
**Status:** EXECUTION SPEC / GATE CONTRACT  
**Master:** `00_MASTER_IMPLEMENTATION_PLAN_PROMPT_ACTION_ASTRA_KE_SOL.docx`  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 00 bukan tahap membuat aplikasi. Jika input wajib tidak tersedia, tidak dapat dibuka, atau tidak dapat diverifikasi, Sol harus STOP dan menetapkan gate `BLOCKED`/`FAIL`. Jangan membuat pengganti berdasarkan nama file, changelog, riwayat, atau asumsi.

## 1. Tujuan

- Verifikasi repo live, branch, HEAD, tree, remote, dan working tree.
- Inventaris seluruh source, legacy, UI reference, backup/recovery, workflow dan bootstrap lama.
- Bedakan source asli dari hasil build/decompile/reconstruction/unknown.
- Hitung inventory + SHA256 manifest yang reproducible.
- Lindungi rescue/source asli dan audit hanya pada staging copy.
- Catat konflik, missing input, dan risiko sebelum STEP 01.

## 2. DILARANG pada STEP 00

- Membuat `app/main.py`, QML, services, runtime schema, atau fitur app.
- Redesign lima master UI.
- Mengubah aturan `System V / Snapshot S / Prompt Revision R`.
- Menyatakan hasil reconstruction sebagai original source.
- Membuat ulang Prompt 1A–5 hanya karena nama/deskripsinya diketahui.
- Menghapus `zz_BOOTSTRAP`, `zz_REBUILD`, workflow lama, `.b64`, atau recovery evidence.
- Menganggap ZIP ada = recovery terbukti tanpa hash/extract verification.

## 3. Provenance label resmi

- `VERIFIED_SOURCE` — source asli dengan provenance terbukti.
- `VERIFIED_FROM_BUILD` — dibuktikan dari build/portable; bukan source lengkap.
- `DECOMPILED` — diperoleh dari decompile/inspection build.
- `RECONSTRUCTED` — dibangun ulang dari evidence lain; jangan klaim original.
- `VERSION_UNKNOWN` — file nyata ada tetapi versi/parent belum terbukti.
- `UNKNOWN` — asal/isi/status tidak dapat diverifikasi; tidak boleh jadi baseline aktif.

Urutan prioritas konflik: source asli → verified rescue ZIP → Git history di commit tertentu → materialized/reconstructed package → dokumen/changelog sebagai penjelasan saja.

## 4. Anchor live repo yang diamati Astra

Anchor saat dokumen STEP 00 dibuat:

- branch: `main`
- HEAD: `f31b194390990848548602914e4de9dfc7d90616`
- tree: `9c40a25d2767679c579ed9711bd18b659c3c1cca`
- commit: `Add authoritative materialized UI reference index`
- root terlihat: `.github`, `PLAN.md`, `START_HERE.txt`, `docs`, `zz_BOOTSTRAP`, `zz_REBUILD`

**Jangan memakai SHA di atas jika live repo telah berubah.** Sol wajib membaca ulang live branch/HEAD sebelum audit.

## 5. MUST-HAVE input

STEP 00 hanya dapat PASS bila semua ini verified:

1. repo `inoriko920-dev/Prompt-Action`, branch/HEAD aktual;
2. Master Implementation Plan;
3. lima master UI materialized;
4. versioning/UI specifications;
5. Legacy V22.5.1 source/recovery yang dapat diverifikasi;
6. Prompt 1A, 1B, 1B1, 1B2, 2, 3, 4, 5 baseline;
7. recovery package yang dapat diuji untuk scope yang diklaim.

Draft/eksperimen lama tidak blocking bila bukan baseline resmi. Workflow bootstrap lama adalah evidence-only.

## 6. Preservation

Gunakan staging. Jangan edit rescue/source asli.

```text
<WORKROOT>/
├─ 00_ORIGINAL_READONLY/
├─ 01_STAGING/
├─ 02_EVIDENCE/step00/
├─ 03_REPORT/
└─ 04_TEMP/
```

Prosedur:

1. Catat original path + byte size.
2. SHA256 original sebelum extraction/copy.
3. Copy ke area read-only/staging.
4. Extract hanya ke staging.
5. Audit/rename/normalisasi hanya di staging.
6. Hash ulang original setelah audit untuk membuktikan tidak berubah.

## 7. Git verification

Minimum commands:

```powershell
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git log -1 --decorate --oneline
git status --short --branch
git ls-tree -r --name-only HEAD > evidence\step00\git-tree.txt
```

Jika working tree dirty: jangan `reset`, `checkout --force`, `clean -fd`, atau stash otomatis. Inventaris file changed/untracked dan simpan evidence dahulu.

## 8. Inventory minimum

Setiap artefak penting harus mencatat:

`path, filename, bytes, sha256, category, provenance, version_claim, baseline_role, notes`

`baseline_role` minimum: `ACTIVE_CANDIDATE`, `LEGACY`, `REFERENCE`, `EVIDENCE_ONLY`, `EXCLUDE`.

Aturan konflik:

- hash sama + path berbeda = `DUPLICATE_IDENTICAL`;
- nama sama + hash berbeda = `CONFLICT`, jangan overwrite;
- line ending berbeda tetap dianggap hash berbeda selama baseline.

## 9. UI reference wajib

Verifikasi file asli/readable + dimensions + SHA256:

- `docs/UI_REFERENCE_PACKAGE_V1/materialized/images/01-Dashboard.jpg`
- `.../02-Sejarah-Sistem.jpg`
- `.../03-Per-Prompt.jpg`
- `.../04-Backup-Recovery.jpg`
- `.../05-Pengaturan.jpg`

`materialized/INDEX.md` adalah index authoritative. Jika JPG materialized ada, `.b64` bukan master visual.

## 10. Corpus Prompt — BLOCKING GATE

Wajib cari dan buktikan:

- Prompt 1A
- Prompt 1B
- Prompt 1B1
- Prompt 1B2
- Prompt 2
- Prompt 3
- Prompt 4
- Prompt 5

Per prompt catat exact filename/path, bytes, SHA256, version text bila ada, parent/provenance bila terbukti, legacy/current/version-unknown, serta kemampuan membuka isi penuh tanpa truncation/encoding error.

Jika source prompt tidak ada, catat `MISSING_REQUIRED_SOURCE` dan STOP. Jangan membuat TXT dari DOCX/changelog/conversation.

## 11. Legacy V22.5.1

V22.5.1 adalah `LEGACY SOURCE`, bukan nomor aktif Prompt Action. STEP 00 harus membuktikan package/source legacy yang benar-benar tersedia:

- path/ZIP/TXT + SHA256 + provenance;
- isi internal, bukan hanya nama ZIP;
- apakah memuat seluruh Prompt 1A–5;
- extract test di staging;
- konflik hash terhadap file lain.

Riwayat sebelum V22.5.1 boleh menjadi `HISTORY_METADATA` bila hanya didukung dokumentasi. Jangan membuat file palsu untuk versi tanpa source.

## 12. Backup & recovery verification

PASS package hanya jika:

- file ada dan size > 0;
- SHA256 dihitung dari file aktual;
- companion checksum cocok bila tersedia;
- extract ke folder kosong/staging tanpa error;
- required contents sesuai scope yang diklaim;
- tidak ada recursive self-backup;
- second copy dicatat bila policy mewajibkan.

UI reference recovery package bukan otomatis full Prompt Action recovery. Verifikasi scope masing-masing package.

## 13. Workflow/bootstrap lama

Inventaris, jangan edit/hapus pada STEP 00:

- `.github/workflows/extract-ui-reference.yml`
- `.github/workflows/materialize-ui-reference.yml`
- `zz_BOOTSTRAP/chunks`
- `zz_REBUILD/chunks`
- legacy `.b64`

Workflow lama boleh berstatus gagal apabila authoritative materialized/source dapat diverifikasi langsung; failure tetap dicatat sebagai risk/evidence.

## 14. SHA256 manifest

Minimal mencakup source prompt, legacy package, source-of-truth docs, lima UI, dan backup/recovery package.

Manifest harus memakai relative path yang stabil dan diurutkan. Jangan masukkan temp/lock/render evidence berubah-ubah ke canonical manifest.

## 15. Output STEP 00 yang diperbolehkan

```text
docs/implementation/
└─ STEP_00_BASELINE_REPORT.md

evidence/step00/
├─ repo_identity.json
├─ git-tree.txt
├─ inventory.csv
├─ sha256_manifest.csv
├─ original_hashes.txt
├─ preservation_log.md
├─ conflicts.md
├─ missing_required_inputs.md
├─ recovery_test.md
└─ screenshots_or_listing_evidence/

BASELINE.json
```

STEP 00 tidak boleh membuat `app/`, `data/`, `prompts/` baru untuk menyamarkan input baseline yang hilang.

## 16. Urutan eksekusi wajib — SERIAL

1. Baca master plan + STEP 00 penuh.
2. Verifikasi live repo/branch/HEAD/remote/working tree.
3. Buat evidence folder tanpa mengubah source.
4. Hash/copy rescue/original ke staging.
5. Inventaris repo + materialized/reference.
6. Verifikasi source-of-truth docs.
7. Verifikasi 5 UI.
8. Cari/verifikasi Legacy V22.5.1.
9. Cari/verifikasi 8 prompt baseline.
10. Uji recovery package di staging.
11. Catat workflow/bootstrap legacy.
12. Buat inventory + SHA256 manifest.
13. Buat conflicts/missing-input register.
14. Buat `BASELINE.json` + `STEP_00_BASELINE_REPORT.md`.
15. Re-check original hashes + live HEAD.
16. Tetapkan `PASS`, `BLOCKED`, atau `FAIL`; STOP.

## 17. Blocking tests

- T00-01 Repo identity.
- T00-02 Working tree preservation.
- T00-03 Master docs.
- T00-04 Five UI refs.
- T00-05 Legacy V22.5.1.
- T00-06 Eight-prompt corpus.
- T00-07 Recovery package extract/checksum.
- T00-08 Manifest repeatability.
- T00-09 Conflict register complete.
- T00-10 No feature code created.

Semua blocking test harus PASS untuk gate PASS.

## 18. Gate result

- `PASS` — semua MUST-HAVE verified; STEP 01 baru boleh dibuat/diaktifkan setelah review Astra/user.
- `BLOCKED` — audit valid tetapi ada input wajib hilang/tidak dapat diverifikasi.
- `FAIL` — integrity/procedure gagal: repo salah, source tertimpa, hash mismatch tak terjelaskan, dll.

Tidak ada “PASS bersyarat” untuk missing source prompt/legacy.

## 19. Laporan handoff minimum

Laporan akhir wajib berisi:

- repo / branch / live HEAD / tree;
- working tree state;
- source-of-truth docs verified;
- UI 5/5 status;
- status/path/hash/provenance P1A–P5;
- Legacy V22.5.1 status + provenance + extract test;
- recovery packages tested + checksum result;
- conflicts/missing inputs;
- files audit/evidence yang dibuat;
- final gate `PASS|BLOCKED|FAIL` + reason;
- recommendation: `READY FOR ASTRA REVIEW` atau `DO NOT START STEP 01`.

## 20. Definition of Done

STEP 00 hanya DONE jika repo identity + source-of-truth docs + 5 UI + Legacy V22.5.1 + 8 prompt baseline + preservation proof + inventory + SHA256 manifest + recovery test + conflict register + `BASELINE.json` + final gate result semuanya tersedia.

> Bahkan jika Sol menyatakan PASS, **jangan mulai STEP 01 secara otomatis**. Tunggu review Astra/user.
