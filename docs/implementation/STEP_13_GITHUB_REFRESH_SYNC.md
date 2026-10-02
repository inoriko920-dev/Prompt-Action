# STEP 13 — GITHUB REFRESH / SYNC

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 sampai STEP 12 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 13 menyambungkan Prompt Action ke GitHub sebagai remote mirror/audit channel. GitHub **bukan** pengganti Full Backup STEP 11 dan bukan satu-satunya source recovery. `REFRESH` wajib read-only; `SYNC/PUBLISH` adalah mutasi remote eksplisit yang selalu melalui preflight, Sync Plan, dan konfirmasi.

## Gate sebelum mulai

1. STEP 00–12 wajib PASS dengan evidence yang dapat diverifikasi.
2. Verifikasi live repo / branch / HEAD pada saat eksekusi; planning SHA bukan current truth.
3. Current local Snapshot wajib `COMPLETE` untuk publish. Refresh tetap boleh saat `BACKUP_REQUIRED`, tetapi publish harus `BLOCKED`.
4. Tidak boleh ada release, backup, restore, atau recovery transaction unresolved.
5. Canonical local data, active Prompt files, dan hash wajib valid.
6. Repo identity + branch harus cocok settings dan dapat dibaca.
7. Credential write tidak boleh berasal dari plaintext token di settings JSON.
8. Jika remote HEAD berubah setelah plan dibuat, plan menjadi `STALE_PLAN` dan wajib dihitung ulang.
9. Jika managed scope tidak dapat diverifikasi: STOP = `BLOCKED`.

## Prinsip utama

- `REFRESH` = read-only.
- `PUBLISH` = explicit remote mutation.
- Tidak ada auto-pull ke live data.
- Tidak ada auto-push tanpa preview + confirmation.
- Tidak ada force-push / history rewrite.
- Local canonical truth tidak boleh diperbaiki otomatis dari remote.
- Perubahan unmanaged di repo tidak boleh hilang.
- Network failure tidak boleh merusak local state.

## Arsitektur

```text
UI / Settings / Dashboard
  ↓
GitHubSyncViewModel
  ↓
RemoteRefreshService ── SyncPlanner ── ConflictAnalyzer
  ↓
GitHubClient / AuthProvider / RateLimitGuard
  ↓
ManagedScopePolicy + OutgoingSecretScanner
  ↓
SyncJournal + LastSyncStore + EvidenceWriter
```

Service minimum:
- `GitHubClient`: repo metadata, branch HEAD, tree/blob read, commit/write adapter.
- `AuthProvider`: credential dari provider aman; secret tidak diserialisasi ke settings.
- `RemoteRefreshService`: read-only refresh + permission/status/rate limit.
- `ManagedScopePolicy`: allowlist path yang boleh disentuh runtime.
- `SyncPlanner`: deterministic local-vs-remote diff.
- `ConflictAnalyzer`: klasifikasi `CLEAN / LOCAL_AHEAD / REMOTE_AHEAD / DIVERGED`.
- `PublishService`: satu normal commit berdasarkan expected HEAD.
- `RemoteStageDownloader`: download remote managed set ke staging; tidak activate live.
- `SyncJournal`: crash/idempotency journal.
- `LastSyncStore`: remote HEAD/fingerprint/status terakhir tanpa credential.
- `OutgoingSecretScanner`: block secret sebelum publish.

Semua network I/O wajib asynchronous/background worker; UI tidak boleh freeze.

## Managed scope

Runtime sync **tidak boleh** menganggap seluruh repository sebagai miliknya.

Default allowlist yang direkomendasikan:

```text
prompts/**
version-data/**
data/version_history.json
CHANGELOG/** atau changelog file yang dikontrak
releases/manifests/**  # metadata kecil saja
```

Deny/protected area minimum:

```text
.git/**
.github/**
src/**
tests/**
docs/implementation/**
docs/UI_REFERENCE_PACKAGE_V1/**
backups/**/*.zip
runtime/**
logs/**
settings*.json
*.token / *.key / *.pem / credential files
transaction staging / temp / crash dump
```

Aturan utama: **jika path tidak ada di allowlist, runtime sync tidak boleh menulisnya.** Denylist hanya defense tambahan.

Remote delete hanya boleh untuk managed file yang memang dinyatakan delete oleh Sync Plan dan dikonfirmasi user. Unknown/unmanaged remote files tidak boleh dihapus otomatis.

## Refresh state machine

```text
IDLE
→ REFRESHING_REPO
→ REFRESHING_BRANCH
→ REFRESHING_TREE
→ ANALYZING
→ READY
```

READY status:
- `CLEAN`
- `LOCAL_AHEAD`
- `REMOTE_AHEAD`
- `DIVERGED`
- `READ_ONLY`
- `AUTH_REQUIRED`
- `OFFLINE`
- `RATE_LIMITED`
- `BLOCKED`

Definisi:
- `CLEAN`: managed local fingerprint sama dengan remote managed fingerprint.
- `LOCAL_AHEAD`: local COMPLETE state berubah tetapi belum dipublish.
- `REMOTE_AHEAD`: remote managed state berubah, local belum berubah relatif baseline.
- `DIVERGED`: local dan remote managed sama-sama berubah / ada konflik.
- `READ_ONLY`: read permission tersedia, write tidak.
- `AUTH_REQUIRED`: credential tidak tersedia/ditolak.
- `OFFLINE`: network tidak dapat mencapai GitHub; jangan salah klasifikasi sebagai auth invalid.
- `RATE_LIMITED`: respect reset/backoff; jangan spam retry.
- `BLOCKED`: integrity/policy/precondition gagal.

Refresh wajib benar-benar read-only: tidak menulis canonical, tidak mengubah active Snapshot/Revision, tidak membuat commit/branch remote, dan tidak memodifikasi Prompt bytes. Hanya cache/status/last-refresh machine-local yang boleh ditulis.

## Fingerprint & baseline sync

Jangan memakai timestamp sebagai trust signal utama. Gunakan stable content identity berbasis normalized path + content hash.

```text
ManagedFingerprint = SHA256(
  sorted(normalized_path + "\0" + content_hash)
)
```

`LastSyncRecord` minimum:

```text
repository
branch
remote_head_sha
managed_fingerprint
local_snapshot_id
local_app_data_revision
synced_at
result
commit_sha?
warnings[]
```

LastSyncRecord adalah cache/audit, bukan canonical version history. Jika hilang, refresh ulang; jangan menebak `CLEAN`.

## Sync Plan — dilarang push langsung

Semua publish wajib diawali immutable preview plan:

```text
SyncPlan {
  plan_id,
  repository,
  branch,
  expected_remote_head,
  local_snapshot_id,
  local_managed_fingerprint,
  remote_managed_fingerprint,
  status,
  additions[],
  modifications[],
  deletions[],
  conflicts[],
  unmanaged_remote_changes_summary,
  secret_scan_result,
  policy_result,
  can_publish
}
```

Preflight:
1. Local Snapshot `COMPLETE` + backup health aman.
2. Validate canonical + active Prompt hashes.
3. Refresh remote HEAD/tree.
4. Classify status.
5. Build diff hanya managed scope.
6. Scan outgoing bytes untuk secret/credential.
7. Validate path normalization, size limit, dan binary policy.
8. Tampilkan plan + commit message preview.
9. User confirm.
10. Refresh remote HEAD **sekali lagi tepat sebelum write**. Jika berubah → `STALE_PLAN`.

Commit message harus deterministic, tidak memuat secret/path lokal, dan mereferensikan Snapshot yang dipublish.

## Publish transaction

Target: satu normal commit pada branch konfigurasi dengan parent = expected remote HEAD.

```text
PLANNED
→ PREPARING_BLOBS
→ BUILDING_TREE
→ CREATING_COMMIT
→ UPDATING_REF
→ VERIFYING_REMOTE
→ PUBLISHED

failure:
→ FAILED_SAFE
→ STALE_PLAN
→ REMOTE_VERIFY_FAILED
```

Rules:
- Parent commit = expected remote HEAD terbaru.
- Tree mempertahankan seluruh unmanaged remote files.
- Hanya managed entries dari Sync Plan yang boleh berubah.
- Update ref harus fast-forward/expected-head-safe; `force=false`.
- Jika ref ditolak karena HEAD berubah: refresh + replan, jangan force.
- Setelah update sukses, fetch commit/tree lagi dan verifikasi remote managed fingerprint.
- Timeout ambigu tidak boleh membuat duplicate commit saat retry. Cek remote HEAD/fingerprint + transaction ID terlebih dulu.

## Conflict handling

| Kasus | Behavior |
| --- | --- |
| Remote berubah hanya di unmanaged files | Replan pada HEAD baru; preserve perubahan itu |
| Remote managed berubah, local unchanged | `REMOTE_AHEAD`; inspect/download-to-staging |
| Remote managed + local managed berubah | `DIVERGED`; publish BLOCKED sampai resolusi |
| Remote menambah unknown managed path | Conflict / untracked-remote; jangan delete otomatis |
| Remote menghapus managed file | Tampilkan destructive diff; jangan mirror-delete local otomatis |
| Same managed content, commit berbeda | Boleh `CLEAN` berdasarkan managed fingerprint |
| Branch rewritten eksternal | Baseline invalid; full refresh + explicit re-trust |

Resolusi yang boleh:
- Inspect Remote read-only.
- Download Remote to Staging.
- Keep Local / Publish Local hanya dengan explicit resolution dan normal commit.
- Keep Remote tidak boleh overwrite local langsung; gunakan staged import/recovery workflow.
- Manual Resolution untuk conflict kompleks.

Tidak ada tombol `force sync` yang diam-diam menghapus remote history atau mengganti local canonical state.

## Remote download-to-staging

Remote managed state boleh diunduh untuk inspeksi, tetapi **bukan live state**.

```text
runtime/github-sync/<session-id>/
  remote-tree.json
  managed-files/**
  validation-report.json
  compare-report.json
  sync-plan.json
```

Download harus dipin ke exact remote commit SHA, validate path/collision, canonical structure, dan Prompt hashes. Hasil staging tidak boleh auto-activate. Jika ingin dijadikan live state, gunakan jalur recovery/import transactional yang menjaga history.

## Authentication, credential & privacy

- Settings hanya menyimpan repo/branch/status metadata.
- Tidak boleh menyimpan PAT/token/password/cookie plaintext di settings.
- Logs harus redact `Authorization`, token, signed URL, dan secret lain.
- Diagnostics harus sanitize credential/path sensitif.
- Credential tidak boleh masuk Full Backup.
- GitHub commit tidak boleh membawa token, log, machine settings, atau crash dump.
- UI credential input harus masked; jangan menampilkan full token setelah input.
- Read-only permission → Refresh/Inspect aktif, Publish disabled.
- Write permission → Publish aktif hanya jika semua gate PASS.
- Admin permission tidak dibutuhkan untuk normal sync.

## Offline, rate limit, cache, performance

- App tetap bekerja lokal tanpa GitHub.
- Offline tidak mengubah status Snapshot lokal.
- Bedakan `OFFLINE`, `AUTH_REQUIRED`, dan `RATE_LIMITED`.
- Jangan background retry agresif.
- Cache repo/tree boleh dipakai untuk UI, tetapi publish selalu refresh HEAD sebelum write.
- Cache keyed by repo + branch + commit SHA.
- Gunakan tree/path-scoped retrieval bila tersedia; jangan download seluruh repo ZIP tiap refresh.
- Hash local managed files boleh incremental sebagai optimisasi, tetapi final trust saat publish tetap content hash.
- Batasi concurrency dan respect GitHub rate-limit/backoff.

## UI integration

Area `Pengaturan > GitHub` minimal:
- Repository owner/name.
- Branch.
- Connection status.
- Remote HEAD short SHA.
- Last refresh.
- Last successful sync.
- Permission `Read-only / Write`.
- `Refresh`.
- `Lihat Perubahan`.
- `Publish/Sync` hanya jika `can_publish=true`.
- Conflict banner saat `DIVERGED`.

Dashboard/topbar cukup memiliki indikator kecil `Sinkron / Local Ahead / Conflict / Offline`. Status Backup tetap lebih penting daripada GitHub status.

Dangerous action seperti conflict publish, delete managed remote, atau mengganti repo/branch harus menampilkan exact-effect confirmation; tidak boleh one-click destructive.

## Logging, audit & evidence

Structured events minimum:

```text
github.refresh.started / completed / failed
github.sync.plan.created / stale
github.publish.started / commit_created / ref_updated / verified / failed
github.conflict.detected
github.auth.required
github.rate_limited
github.remote_stage.downloaded / validated
```

Evidence minimum:

```text
evidence/step13/
  repo-status.json
  refresh-report.json
  sync-plan.json
  publish-report.json
  conflict-fixtures/
  remote-stage-report.json
  test-results.xml
  screenshots/
  logs-sanitized.txt
```

## Test Plan — T01 sampai T70

T01 Refresh valid repo/branch; T02 invalid repo config; T03 branch missing; T04 read-only permission; T05 write permission; T06 auth missing; T07 auth rejected; T08 offline; T09 rate limit; T10 repo rename/redirect.

T11 managed allowlist; T12 deny source code; T13 deny implementation docs; T14 deny backup ZIP; T15 deny settings/log/temp; T16 path traversal; T17 symlink/reparse escape; T18 Windows case collision; T19 unexpected managed path; T20 preserve unmanaged remote.

T21 deterministic fingerprint; T22 same content different commit → managed CLEAN; T23 local ahead; T24 remote ahead; T25 diverged; T26 missing last-sync record; T27 stale cache; T28 BACKUP_REQUIRED blocks publish; T29 canonical invalid; T30 Prompt hash mismatch.

T31 add plan; T32 modify; T33 delete; T34 no-op; T35 managed-only plan; T36 secret scanner token; T37 sanitized evidence; T38 expected HEAD stored; T39 HEAD change before confirm; T40 HEAD change immediately before write.

T41 single normal commit; T42 parent = expected HEAD; T43 no force push; T44 preserve unmanaged tree; T45 remote verify; T46 timeout after commit create; T47 timeout after ref update; T48 idempotent retry; T49 branch protection rejection; T50 insufficient write permission.

T51 remote managed edit; T52 remote managed delete; T53 unknown managed add; T54 source-code-only remote change; T55 diverged publish blocked; T56 explicit keep-local normal commit; T57 remote staging download; T58 staging canonical validation; T59 staging hash mismatch; T60 no auto activation.

T61 large managed tree; T62 Unicode filenames; T63 spaces in paths; T64 UI responsive; T65 cancel refresh; T66 cancel before publish write; T67 log redact auth; T68 diagnostics redact secret; T69 LastSyncStore restart persistence; T70 full end-to-end `COMPLETE local → refresh → plan → publish → verify CLEAN`.

## Acceptance Gate ASTRA

1. STEP 00–12 PASS.
2. Refresh benar-benar read-only.
3. Managed scope allowlist + deny policy tervalidasi.
4. Local COMPLETE state dibandingkan remote secara deterministic.
5. `CLEAN / LOCAL_AHEAD / REMOTE_AHEAD / DIVERGED` benar.
6. Publish memakai expected HEAD dan tidak force-push.
7. Unmanaged remote changes tidak hilang.
8. Secret tidak pernah masuk outgoing commit/log/diagnostics/backup/settings.
9. Retry timeout idempotent.
10. Remote staging tidak auto-activate live.
11. T01–T70 PASS dan evidence lengkap.
12. Protected corpus/source/UI refs tidak berubah di luar scope.
13. Astra review PASS sebelum STEP 14.

Jika satu gate blocking gagal, STEP 13 = `FAIL/BLOCKED`.

## Prompt eksekusi untuk SOL

```text
PERAN AKTIF: SOL.

Kerjakan STEP 13 — GITHUB REFRESH / SYNC untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX/Markdown Astra STEP 13.
Kerjakan SERIAL; jangan worker/chat paralel.

Aturan wajib:
1. Verifikasi live repo/branch/HEAD lebih dulu.
2. Jangan sentuh file di luar managed scope runtime.
3. REFRESH harus read-only.
4. PUBLISH hanya boleh jika local Snapshot COMPLETE, canonical+hash valid, secret scan PASS, dan SyncPlan can_publish=true.
5. Re-check remote HEAD tepat sebelum write; jika berubah, batalkan sebagai STALE_PLAN dan replan.
6. Jangan pernah force-push / rewrite history.
7. Preserve seluruh unmanaged remote changes.
8. Credential GitHub tidak boleh plaintext di settings/log/backup/commit.
9. Remote download hanya ke staging; jangan auto-activate live.
10. Implementasikan CLEAN / LOCAL_AHEAD / REMOTE_AHEAD / DIVERGED / READ_ONLY / AUTH_REQUIRED / OFFLINE / RATE_LIMITED / BLOCKED.
11. Retry publish harus idempotent; jangan membuat duplicate commit setelah timeout ambigu.
12. Jalankan T01–T70 dan simpan evidence STEP 13.

STOP jika ada input/gate wajib yang tidak dapat diverifikasi. Jangan menebak atau memperbaiki history diam-diam.

Output akhir wajib memuat live HEAD awal/akhir, file yang diubah, test result, evidence path, screenshot status GitHub, dan PASS/FAIL setiap Acceptance Gate.
```

## Handoff ke STEP 14

Setelah STEP 13 PASS, aplikasi memiliki fondasi, lima UI utama, version/release workflow, backup/recovery, serta remote GitHub sync yang aman. STEP 14 melakukan hardening dan full-system test: fault injection, long-run, data-corruption, accessibility, security, performance, dan regression suite.