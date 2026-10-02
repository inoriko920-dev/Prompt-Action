# STEP 15 — PORTABLE WINDOWS BUILD

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 14 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 15 mengubah Release Candidate yang sudah lolos hardening menjadi paket Windows x64 **portable multi-file**. Target adalah folder + ZIP yang dapat dijalankan tanpa Python/Node/Git/IDE di PC pengguna. Bukan installer dan bukan single EXE.

## Gate sebelum mulai

1. STEP 00–14 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo/branch/HEAD; freeze exact source commit.
3. Zero open S0/S1 dari STEP 14.
4. Current canonical data valid; current Snapshot `COMPLETE`.
5. Tidak ada release/backup/restore/recovery/GitHub transaction unresolved.
6. Exact dependency lock + build-tool lock tersedia.
7. Source/build input secret scan PASS.
8. Gate gagal/tidak dapat diverifikasi => `BLOCKED`.

## Artifact contract

Wajib menghasilkan:

- portable RC folder;
- portable RC ZIP;
- ZIP SHA-256 sidecar;
- `MANIFEST.sha256` untuk payload portable;
- `BUILD_INFO.json`;
- `README_PORTABLE.txt` + `RECOVERY_GUIDE.txt`;
- `THIRD_PARTY_NOTICES/`;
- `evidence/step15/**`;
- `STEP15_RESULT.json`.

Dilarang mengganti kontrak menjadi installer/MSI atau single-file EXE.

## Version identity

App Version terpisah dari content System/Snapshot/Revision. Kandidat dapat menggunakan `1.0.0-rc.1`; STEP 16 yang mempromosikan artifact ke final setelah acceptance. Build tidak boleh membuat System/Snapshot/Revision baru.

Setelah source commit RC dibekukan, setiap perubahan code membuat RC lama gugur. Packaging bug fix => commit baru, rerun regression STEP 14 yang relevan, lalu rebuild RC dari awal.

## Portable folder contract

```text
Prompt-Action-<APP_VERSION>-Windows-x64-Portable/
├─ PromptAction.exe
├─ _internal/
├─ resources/
├─ workspace/
│  ├─ prompts/
│  ├─ version-data/
│  └─ changelog/
├─ config/
├─ logs/
├─ diagnostics/
├─ README_PORTABLE.txt
├─ RECOVERY_GUIDE.txt
├─ BUILD_INFO.json
├─ MANIFEST.sha256
└─ THIRD_PARTY_NOTICES/
```

Runtime bundle (`exe`, `_internal`, resources) tidak boleh self-modify. Workspace/config/log/diagnostics adalah portable writable state. Token/credential tidak boleh plaintext di portable root.

## Build environment

- clean Windows x64 build environment;
- exact Python build runtime dari lock;
- exact PySide6/Qt/dependencies;
- exact packager version;
- build script reproducible;
- clean dist/build cache;
- tidak mengambil file manual dari folder dev lama;
- seluruh extra file dideklarasikan oleh build spec/script.

Gunakan packaging mode folder/onedir yang sesuai kontrak multi-file. Jangan tambal hasil dist manual: perbaiki build spec lalu rebuild.

## Build pipeline

1. Preflight STEP 14 + Snapshot COMPLETE + source freeze + secret scan.
2. Clean environment + exact dependency install.
3. Pre-package smoke subset.
4. Bundle PySide6/QML portable multi-file.
5. Audit Qt platform/QML/image/TLS/resources.
6. Assemble portable root.
7. Seed/copy approved workspace dengan exact-byte/hash verification.
8. Generate BUILD_INFO + third-party notices.
9. Secret/dev-path/source/temp scan pada portable root.
10. Smoke langsung dari dist folder.
11. Generate `MANIFEST.sha256`.
12. Buat final ZIP satu-root-folder.
13. Hitung ZIP SHA-256 sidecar.
14. Extract ZIP ke lokasi baru dan rerun smoke + relocation.
15. Freeze RC + evidence.

## PySide6/QML checklist

Verifikasi `qwindows`, QML imports, Qt Quick Controls, SVG/image plugins, font fallback, icon/resources, Indonesian strings, SSL/network degradation, dan tidak ada source absolute path dependency.

## Workspace integrity

Packaging bukan migration konten. Current System/Snapshot/Revision tidak berubah. Prompt/Revision bytes dan SHA harus tetap cocok. Tidak boleh mengubah EOL/encoding diam-diam. Backup artifact tetap recovery channel terpisah kecuali artifact contract eksplisit menyatakan lain.

## Security / sanitization

FAIL jika package berisi PAT/token/password/cookie/private key, dev absolute path yang menjadi runtime dependency, staging/temp crash residue, destructive fixtures, dev log sensitif, atau payload tidak dikenal.

## BUILD_INFO minimum

`app_version`, `source_commit`, `source_branch`, `build_target`, exact Python/PySide6/packager, requirements-lock SHA256, content System/Snapshot, build UTC, dan STEP14 evidence ID.

## ZIP / hash

Nama contoh: `Prompt-Action-1.0.0-rc.1-Windows-x64-Portable.zip`.

- satu root folder dalam ZIP;
- `MANIFEST.sha256` untuk payload internal;
- `<zip>.sha256` untuk archive final;
- archive temp lalu final rename;
- Windows-safe filename;
- hash diverifikasi ulang setelah extract.

Reproducibility yang diwajibkan adalah **reproducible build procedure + payload inventory**. Byte-for-byte binary/ZIP antarmesin hanya diwajibkan jika toolchain memang terbukti deterministic.

## Clean-PC qualification

Uji Windows 11 x64 bersih/new user tanpa Python, Node, Git, IDE, repo source:

- launch EXE;
- 5 halaman utama;
- canonical load;
- search/compare/download smoke;
- settings persistence;
- offline startup;
- close/reopen;
- no-admin launch.

## Relocation matrix

Uji folder dengan spasi, Unicode path, pindah C:→D:/E:, nested path, restart setelah move, offline, dan DPI 100/125/150/175. Baseline portable root adalah local writable filesystem; network/UNC root yang belum qualified harus diberi unsupported/warning state.

## Update policy

Tidak ada auto-update baru pada STEP 15. Versi baru diekstrak side-by-side; jangan overwrite folder portable lama. Workspace dipindahkan melalui backup/restore/migration tervalidasi. Jangan delete versi lama otomatis sebelum versi baru terbukti aman.

## Failure rules

Missing Qt/QML/DLL, manifest mismatch, ZIP/hash corruption, secret/dev-path leak, partial archive, clean-PC failure, relocation failure, atau packaging residue => RC FAIL/BLOCKED. Jangan meminta user mematikan Defender/security sebagai solusi default.

## T01–T70

Qualification meliputi gate/source freeze, clean build/dependency lock, Qt/QML/resource bundling, portable path/workspace, ZIP/manifest/hash, clean-PC/relocation/offline/DPI, security/evidence/rebuild. Semua blocker harus zero.

## Evidence

`evidence/step15/` minimal memuat source identity, build environment, build log, lock hashes, packaging inventory, manifest verification, ZIP SHA256, clean-PC smoke, relocation matrix, offline/DPI smoke, security scan, screenshots, dan `STEP15_RESULT.json`.

## Acceptance gate

STEP 15 PASS hanya jika:

1. STEP 00–14 PASS dan source commit tercatat.
2. Tidak ada fitur baru setelah freeze.
3. Build berasal dari clean scripted process; bukan manual patch.
4. Tidak membutuhkan Python/Node/Git/IDE/admin pada clean-PC baseline.
5. Qt/QML/resources lengkap.
6. Relocation PASS.
7. Content System/Snapshot/Revision tidak berubah.
8. Secret/dev residue = zero.
9. Internal manifest valid.
10. ZIP extract + payload hash valid.
11. ZIP SHA256 sidecar valid.
12. Clean-PC/offline/DPI/settings/restart PASS.
13. BUILD_INFO/notices/README tersedia.
14. T01–T70 PASS.
15. `STEP15_RESULT.json = PASS` dan RC dibekukan untuk STEP 16.

Jika satu gate gagal, jangan lanjut STEP 16 dan jangan sebut artifact sebagai final release.

## Prompt SOL

Sol harus mengimplementasikan packaging secara serial, memverifikasi live HEAD, mempertahankan feature freeze, membuat Windows x64 portable multi-file RC, menjalankan clean-PC/relocation/offline/DPI qualification, membuat manifest/hash/evidence, dan berhenti `BLOCKED` bila input/gate wajib tidak dapat diverifikasi. STEP 15 tidak boleh mempublish final release; hasilnya adalah RC exact untuk STEP 16.
