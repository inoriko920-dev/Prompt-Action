# STEP 14 — HARDENING & FULL-SYSTEM TESTING

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 13 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 14 adalah qualification gate sebelum packaging. Berlaku **FEATURE FREEZE**: bug fix, security hardening, reliability, performance, testability, dan visual-regression fix boleh; fitur baru dan redesign besar dilarang. Setiap bug fix wajib mempunyai regression test.

## Gate sebelum mulai

1. STEP 00–13 PASS dan live repo/branch/HEAD diverifikasi.
2. Tidak ada release/backup/restore/GitHub transaction unresolved.
3. Current Snapshot COMPLETE; canonical validator PASS.
4. Primary + second-copy backup current valid.
5. 5 master UI reference tersedia.
6. Destructive test hanya pada fixture/workspace terisolasi.
7. Baseline corpus Prompt/legacy/UI reference di-hash sebelum hardening.

## Tujuan

- full regression seluruh STEP 00–13;
- T01–T100 qualification index;
- E2E release → backup → COMPLETE → GitHub publish → rollback/restore → re-backup;
- crash/fault/concurrency injection;
- security + path safety + secret leak tests;
- visual regression 5 UI pada DPI 100/125/150/175%;
- performance/resource soak tanpa UI freeze;
- zero S0/S1 defect;
- evidence package + traceability matrix.

## Freeze policy

Allowed: correctness bug fix, crash/race/atomicity fix, security hardening, performance optimization dengan behavior equivalence, visual micro-fix, diagnostics/testability.  
Forbidden: fitur baru, tombol/action baru, redesign besar, perubahan aturan versioning, schema change non-blocking.

Bug-fix loop:

`REPRODUCE → FAILING TEST → MINIMAL FIX → TARGET SUITE → RELATED SUITE → FULL REGRESSION → EVIDENCE`

## Deterministic fixtures

Minimum fixtures: CLEAN_BASELINE, MULTI_HISTORY, LONG_HISTORY (≥250 snapshot), MISSING_FILE, HASH_MISMATCH, GRAPH_CORRUPT, BACKUP_CORRUPT, RECOVERY_INTERRUPTED, GITHUB_DIVERGED, PATH_ATTACKS, UNICODE_LONG_PATH, LARGE_DATASET.

## E2E minimum

- E2E-01 normal release → backup → COMPLETE.
- E2E-02 COMPLETE → GitHub refresh/plan/publish → CLEAN.
- E2E-03 rollback old revision → new Snapshot → backup again.
- E2E-04 verified backup dry-run + restore activation.
- E2E-05 crash during release + deterministic recovery.
- E2E-06 crash during backup + no false COMPLETE.
- E2E-07 GitHub divergence + no overwrite.
- E2E-08 relocate workspace/app and run normally.
- E2E-09 offline local workflow remains usable.
- E2E-10 primary backup missing → restore from verified second copy.

## Hardening areas

### Canonical/version
Re-run INV-01..INV-15; verify monotonic S/R, exactly-one PRIMARY, SYNC=actual changed bytes, active pointer consistency, immutable history, AppVersion separation, fail-closed schema behavior.

### Backup/recovery
Corrupt/truncated ZIP, missing/modified manifest, second-copy mismatch, low disk, file lock, crash phases, Zip Slip, reparse escape, activation crash, Safety Copy failure, rollback=new snapshot.

### GitHub/network
Offline, timeout, auth expired, read-only, rate limit, stale remote HEAD, branch protection, remote unmanaged change preservation, managed divergence, idempotent retry after ambiguous commit result, outgoing secret scan.

### Security/path
Reject traversal, absolute/UNC paths, symlink/junction/reparse escape, case collision, Windows reserved names, ADS-like paths, zip bomb, malformed/oversized JSON, log injection, secret leakage.

### Concurrency
Two-instance release race; release vs backup; restore with another instance; stale `app_data_revision`; stale GitHub plan after other publish.

### UI/visual/accessibility
5 master screens, 100/125/150/175%, supported resolutions/min-window, keyboard/focus, status not color-only, loading/error/empty/degraded/blocked states, no clipping/overlap.

### Performance/resource
No event-loop blocking for hashing/ZIP/restore/network; long history stays responsive; repeated navigation/dialogs do not leak; cancellation cleans temp state; mixed-workflow soak.

## T01–T100 qualification index

- T01–T10 Startup/Foundation
- T11–T20 Canonical/Version
- T21–T30 UI/Navigation
- T31–T40 Search/Compare/Download
- T41–T50 Release Transaction
- T51–T60 Backup Engine
- T61–T70 Restore/Rollback
- T71–T80 GitHub Sync
- T81–T90 Security/Privacy
- T91–T100 Performance/Soak

Semua test STEP lama tetap regression suite; T01–T100 adalah index qualification lintas sistem, bukan penggantinya.

## Defect severity

- **S0 Critical:** data loss, unrecoverable corruption, security compromise, secret exposure → ZERO allowed.
- **S1 High:** common crash, wrong version state, false COMPLETE, unsafe overwrite, incorrect restore → ZERO allowed.
- **S2 Medium:** important edge-case issue dengan workaround aman → target ZERO; exception perlu Astra approval.
- **S3 Low:** cosmetic/non-critical → dapat dicatat untuk post-release.

Tidak boleh menutup S0/S1 sebagai “known issue”.

## Evidence minimum

`evidence/step14/` harus berisi environment, baseline hashes, canonical validation, automated results/JUnit, E2E evidence, fault-injection, security, performance, visual DPI evidence, defect records, final regression summary, traceability matrix, dan `STEP14_RESULT.json`.

## Acceptance Gate

PASS hanya jika:
1. STEP 00–13 PASS + live HEAD tercatat.
2. Feature freeze dipatuhi.
3. Full regression PASS.
4. T01–T100 PASS.
5. E2E-01..10 PASS.
6. Fault/crash/concurrency suite PASS.
7. Security/path/secret suite PASS.
8. 5 UI visual qualification PASS pada seluruh DPI target.
9. Tidak ada UI freeze/resource leak blocker.
10. Zero S0/S1 terbuka.
11. Protected corpus hash-identical kecuali perubahan disetujui.
12. Evidence reproducible lengkap.
13. Astra menyatakan PASS sebelum STEP 15.

Jika satu gate gagal: `FAIL/BLOCKED`; jangan lanjut packaging.

## Prompt untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 14 — HARDENING & FULL-SYSTEM TESTING untuk Prompt Action berdasarkan spec ASTRA ini. Kerjakan SERIAL; jangan worker/chat paralel.

Repo: inoriko920-dev/Prompt-Action.

1. STEP 00–13 harus PASS; verify live repo/branch/HEAD.
2. FEATURE FREEZE. Tidak boleh tambah fitur/redesign besar.
3. Setiap bugfix wajib regression test.
4. Gunakan fixture/workspace terisolasi untuk destructive test.
5. Jalankan full regression + T01–T100 + E2E-01..10.
6. Fault/crash injection release, backup, restore, GitHub publish.
7. Security/path test lengkap termasuk traversal/reparse/unsafe ZIP/secret leak.
8. Uji concurrency dua instance dan stale transaction/plan.
9. Uji 5 UI di 100/125/150/175%, keyboard/focus/min-window/all states.
10. Heavy operations tidak boleh freeze UI; lakukan performance/resource soak.
11. Zero S0/S1 untuk PASS.
12. Hash protected corpus before/after.
13. Buat evidence/step14 + traceability matrix + STEP14_RESULT.json.
14. Jangan lanjut STEP 15 sebelum Astra review PASS.
```
