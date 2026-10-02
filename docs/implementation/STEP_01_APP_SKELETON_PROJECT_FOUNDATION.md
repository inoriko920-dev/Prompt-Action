# STEP 01 — APP SKELETON & PROJECT FOUNDATION

**Prompt Action — ASTRA → SOL**  
**Status:** HOLD — hanya boleh dieksekusi setelah STEP 00 PASS  
**Repo:** `inoriko920-dev/Prompt-Action`

> STEP 01 hanya membuat fondasi aplikasi. Jangan implementasikan fitur produk, version engine, Dashboard, Sejarah Sistem, Per Prompt, Backup UI, GitHub runtime sync, atau portable release pada step ini.

## Gate sebelum mulai

Sol wajib:

1. membuktikan STEP 00 berstatus PASS;
2. membaca live repo / branch / HEAD pada saat eksekusi;
3. tidak memakai SHA planning sebagai kebenaran mutlak jika repo berubah;
4. memastikan source prompt/legacy dan UI reference tetap read-only;
5. STOP bila input wajib tidak dapat diverifikasi.

## Tujuan

- membuat package Python/PySide6 modular;
- membuat entry point deterministik;
- membuat portable root/path resolver tanpa absolute path;
- membuat QML bootstrap + minimal shell window;
- membuat logging startup/error;
- membuat dependency lock reproducible;
- membuat PowerShell developer scripts;
- membuat unit/smoke tests dan basic CI;
- membuktikan project dapat dipindahkan lokasi folder tanpa merusak resource resolution.

## Scope boleh

- `pyproject.toml`
- `requirements-lock.txt`
- `src/prompt_action/**`
- `scripts/dev/**`
- `tests/step01/**`
- `runtime/.gitkeep`
- optional `.github/workflows/ci-step01.yml`
- docs STEP 01

## Scope terlarang

- final Dashboard/sidebar/master UI;
- System/Snapshot/Revision engine;
- memindahkan atau membuat ulang prompt/legacy;
- backup/release engine;
- GitHub runtime sync;
- single-EXE/portable release final;
- menyimpan credential/token di repo atau log.

## Struktur target

```text
Prompt-Action/
├─ pyproject.toml
├─ requirements-lock.txt
├─ .gitignore
├─ src/
│  └─ prompt_action/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ main.py
│     ├─ app_version.py
│     ├─ bootstrap/
│     │  ├─ __init__.py
│     │  ├─ app_paths.py
│     │  ├─ logging_setup.py
│     │  ├─ qml_boot.py
│     │  └─ exit_codes.py
│     └─ ui/qml/App.qml
├─ scripts/dev/
│  ├─ bootstrap_env.ps1
│  ├─ run_dev.ps1
│  └─ test_step01.ps1
├─ tests/step01/
│  ├─ test_imports.py
│  ├─ test_app_paths.py
│  └─ test_qml_boot.py
└─ runtime/
   ├─ .gitkeep
   ├─ logs/  # generated/ignored
   └─ temp/  # generated/ignored
```

## Dependency policy

- jangan pilih versi hanya karena paling baru;
- pilih Python minor stable + PySide6 exact yang lulus compatibility smoke test di Windows 11;
- pin exact versions di lock file;
- `.venv` hanya untuk dev dan tidak di-commit;
- packaging final belum diputuskan sampai STEP 15.

## Version separation

- App version awal: `0.1.0-dev`;
- System `V1`, Snapshot `Sxxx`, Prompt Revision `Rxx` adalah domain data STEP 02+;
- perubahan Prompt 3 tidak otomatis menaikkan executable version.

## Bootstrap contract

Urutan minimum:

1. `python -m prompt_action`;
2. validate runtime;
3. resolve AppPaths tanpa bergantung pada current working directory;
4. siapkan `runtime/logs` dan `runtime/temp`;
5. initialize logging;
6. create Qt application;
7. create `QQmlApplicationEngine`;
8. load `App.qml` dari resource path;
9. rootObjects kosong → FATAL + non-zero exit;
10. success → event loop;
11. shutdown normal → exit 0 + flush log.

## AppPaths contract

Minimal field:

- `project_root`
- `resource_root`
- `runtime_root`
- `log_dir`
- `temp_dir`
- `docs_root`

Aturan:

- bebas hardcoded `C:\Users\...` / `D:\...`;
- tidak mengandalkan `os.chdir()`;
- harus lulus saat command dijalankan dari cwd lain;
- test path dengan spasi dan non-ASCII;
- packaged/frozen contract baru divalidasi final pada STEP 15.

## Minimal QML shell

Hanya smoke target:

- title `Prompt Action`;
- window sekitar 1280×720;
- placeholder netral seperti `Prompt Action — Foundation Build`;
- belum ada sidebar final, Dashboard, version tree, atau fitur produk.

## Logging

Minimum:

- UTF-8;
- lokasi relatif `runtime/logs/`;
- app version, Python version, PySide6/Qt version, resolved paths, startup status;
- exception startup harus menyimpan traceback;
- token/API key/credential dilarang ditulis ke log.

## Exit code contract

Baseline yang disarankan:

- `0` normal success;
- `10` bootstrap/path failure;
- `11` runtime directory not writable;
- `20` Qt/QML initialization failure;
- `21` QML root object failed to load;
- `30` dependency/runtime mismatch;
- `99` unexpected fatal startup error.

Exact number boleh dikunci ulang sekali saat implementasi, lalu harus konsisten.

## Test wajib T01–T15

- T01 import package;
- T02 module entry point;
- T03 window title;
- T04 QML root load;
- T05 invalid QML simulation → non-zero + log;
- T06 run from different cwd;
- T07 path with spaces;
- T08 Unicode path;
- T09 no admin;
- T10 runtime write;
- T11 read-only runtime simulation;
- T12 clean install from dependency lock;
- T13 repeated start/close;
- T14 relocation;
- T15 CI smoke.

## Relocation test

1. jalankan dari lokasi A;
2. copy/move working tree ke lokasi B yang mengandung spasi;
3. jalankan PowerShell dari cwd lain;
4. pastikan QML/resource ditemukan tanpa edit manual;
5. log AppPaths harus menunjuk lokasi B aktual;
6. tidak boleh ada drive letter tertentu sebagai requirement.

## Evidence wajib

- repo / branch / HEAD before & after;
- exact Python + PySide6 + dependency lock;
- screenshot minimal window;
- startup success log;
- failure log;
- T01–T15 result;
- relocation evidence;
- file inventory;
- git diff summary yang membuktikan prompt/legacy/UI reference tidak berubah.

## Acceptance Gate

PASS hanya jika:

1. STEP 00 PASS;
2. package skeleton modular;
3. dependency exact tercatat;
4. minimal QML window start;
5. relocation/path tests pass;
6. logging + exit code bekerja;
7. blocking tests lulus;
8. evidence lengkap;
9. protected source tidak berubah;
10. live HEAD final tercatat.

Jika satu blocking item gagal: **FAIL/BLOCKED**. Jangan lanjut STEP 02 dengan catatan “nanti diperbaiki”.

## Prompt eksekusi untuk Sol

```text
PERAN AKTIF: SOL.
Kerjakan STEP 01 — APP SKELETON & PROJECT FOUNDATION untuk repo inoriko920-dev/Prompt-Action berdasarkan DOCX STEP 01 dan master plan. Kerjakan sendiri secara SERIAL. Sebelum coding, verifikasi STEP 00 benar-benar PASS dan verifikasi live repo/branch/HEAD. Jangan mengandalkan SHA planning jika repo sudah berubah. Scope hanya package Python/PySide6, entry point, portable AppPaths, QML shell minimal, logging, exit codes, dependency lock, PowerShell dev scripts, tests, dan basic CI. Jangan implementasikan Dashboard, Sejarah Sistem, Per Prompt, Backup UI, version engine, backup engine, GitHub runtime sync, atau portable release. Jangan ubah corpus prompt/legacy maupun UI reference. Jalankan T01–T15, simpan evidence, lalu keluarkan laporan final PASS/FAIL/BLOCKED. Jika STEP 00 tidak PASS atau input wajib tidak dapat diverifikasi: STOP.
```
