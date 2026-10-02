# STEP 16 — FINAL ACCEPTANCE & RELEASE

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 15 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 16 adalah final GO / NO-GO gate. Artifact yang dirilis harus identik dengan artifact yang diuji. Setiap perubahan payload setelah acceptance membatalkan hasil dan mengharuskan kembali ke STEP 15.

## Gate sebelum mulai

1. STEP 00–15 PASS dengan evidence terverifikasi.
2. Live repo/branch/HEAD + source commit dari BUILD_INFO diverifikasi.
3. Exact RC ZIP + SHA256 sidecar + internal manifest cocok STEP15 evidence.
4. `STEP15_RESULT.json = PASS` dan immutable sejak RC freeze.
5. Zero open S0/S1.
6. Current canonical valid; Snapshot COMPLETE; tidak ada unresolved transaction.
7. Release identity sudah diputuskan dan cocok payload.
8. Jika final App Version memerlukan perubahan payload, STOP dan kembali STEP 15.
9. Credential publish tidak boleh masuk artifact/evidence/log.

## Core rule

`TESTED BYTES = RELEASED BYTES`.

Dilarang setelah GO:
- edit EXE/QML/DLL/config/workspace seed;
- edit BUILD_INFO atau internal manifest;
- rebuild diam-diam;
- replace same-version release asset dengan byte berbeda.

Jika satu byte payload berubah, RC lama tidak lagi accepted.

## Release identity

App Version, source commit, BUILD_INFO, release tag, ZIP filename/hash, dan acceptance report harus konsisten. System V / Snapshot S / Revision R tetap layer content terpisah.

Jika payload masih `1.0.0-rc.1` tetapi final diinginkan `1.0.0`, jangan hanya mengganti judul GitHub. Kembali STEP 15, rebuild dengan identity final, lalu qualification ulang.

## Final acceptance coverage

- provenance/source identity;
- ZIP SHA256 + internal manifest;
- clean Windows 11 x64 non-admin smoke;
- 5 halaman utama;
- search/compare/download/settings/restart;
- offline mode;
- relocation + Unicode/space path;
- DPI 100/125/150/175;
- representative revision → snapshot → backup → COMPLETE flow pada isolated copy;
- restore/rollback proof;
- security/path/archive/secret checks;
- GitHub managed-scope safety;
- release notes / recovery docs / known issues;
- post-publish asset re-download + hash verification.

## Release publication

Jika GO:

1. Tag harus menunjuk exact `source_commit` dari BUILD_INFO.
2. Upload exact accepted portable ZIP + SHA256 sidecar.
3. Jangan upload token/settings/log/user workspace/private backup.
4. Publish release notes yang menjelaskan portable usage, integrity, backup, upgrade side-by-side, dan known issues.
5. Download kembali asset dari release.
6. Hitung SHA256; harus identik dengan accepted local ZIP.
7. Jika berbeda, release = WITHDRAW/NO-GO.

GitHub tetap distribution/audit channel, bukan satu-satunya recovery.

## Release Manifest

`RELEASE_MANIFEST.json` eksternal minimal menyimpan:

- release status;
- exact App Version;
- source commit/branch;
- ZIP filename + SHA256;
- internal manifest hash;
- System/Snapshot;
- STEP14/STEP15 evidence IDs;
- acceptance report hash;
- release tag;
- published asset hash;
- accepted UTC time.

## Known issue policy

- S0: NO-GO.
- S1: NO-GO.
- S2: hanya dengan explicit risk acceptance bila benar-benar non-blocking dan workaround aman.
- S3: boleh GO jika terdokumentasi.

Tidak boleh menjadikan data-loss/security/corruption blocker sebagai “known issue”.

## T01–T80

Final acceptance mencakup identity/provenance, artifact/hash, clean-PC/relocation, UI/read flow, mutation/backup/recovery, GitHub distribution, security/privacy/docs, dan GO/NO-GO evidence.

Mandatory representative checks termasuk:
- source commit == BUILD_INFO == tag target;
- App Version tidak dapat relabel tanpa rebuild;
- ZIP/internal manifest mismatch => NO-GO;
- clean PC launch tanpa Python/Node/Git;
- move portable root lalu restart;
- offline local operations;
- backup primary + second-copy required untuk COMPLETE;
- rollback membuat Snapshot baru;
- stale remote HEAD blocks publish;
- re-download remote ZIP hash == accepted ZIP hash;
- secret scan zero;
- S0/S1 = 0.

## Evidence

`evidence/step16/` minimal:

- acceptance environment;
- source/version identity;
- artifact/internal-manifest verification;
- clean-PC smoke;
- relocation/offline/DPI;
- mutation/backup/recovery evidence;
- GitHub publish test;
- security scan;
- screenshots;
- `FINAL_ACCEPTANCE_REPORT.md`;
- `RELEASE_MANIFEST.json`;
- `RELEASE_NOTES.md`;
- `KNOWN_ISSUES.md`;
- `STEP16_RESULT.json`.

## Acceptance gate

STEP 16 GO hanya jika:

1. STEP 00–15 PASS.
2. Exact ZIP SHA uniquely identified.
3. Identity/source/tag/hash consistent.
4. Payload unchanged after STEP15 freeze.
5. ZIP + internal manifest PASS.
6. Clean-PC non-admin PASS tanpa dev dependencies.
7. UI/read/settings/restart PASS.
8. Offline/relocation/DPI PASS.
9. Representative mutation + backup + recovery PASS.
10. Security/secret/path checks PASS.
11. GitHub publish model safe.
12. Docs/known issues complete.
13. S0 = 0; S1 = 0.
14. T01–T80 PASS / allowed exception explicitly accepted.
15. Post-publish downloaded asset hash matches accepted ZIP.
16. Release Manifest + Final Acceptance Report consistent.
17. `STEP16_RESULT.json = GO`.

Jika blocking gate gagal: `NO-GO` atau `BLOCKED`. Jangan sebut build sebagai final release.

## Post-release control

Jangan replace same-version asset dengan byte berbeda. Jika ada issue kritis setelah publish, tandai release withdrawn/deprecated dan hentikan distribusi bila aman. Fix menghasilkan version baru dan kembali melalui gate yang relevan. Simpan exact accepted ZIP + hash + manifest + evidence di archive/recovery di luar GitHub.

## Prompt SOL

Sol harus mengerjakan STEP 16 secara serial, tidak mengubah payload RC, memverifikasi exact hashes/identity, menjalankan final acceptance di environment bersih, membuat evidence, memutuskan GO/NO-GO/BLOCKED, dan hanya jika GO mempublish exact accepted artifact. Setelah publish, download ulang asset dan buktikan SHA256 identik.

## Master planning complete

Dengan STEP 16, planning ASTRA STEP 00–16 selesai. Berikutnya SOL menjalankan STEP 00 secara serial sampai STEP 16; dokumen planning tidak sama dengan aplikasi yang sudah jadi.
