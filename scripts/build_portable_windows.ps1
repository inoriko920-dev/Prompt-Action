param(
    [string]$BuildLabel = "local"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$DistRoot = Join-Path $Root "dist"
$BuildRoot = Join-Path $Root "build"
$PortableRoot = Join-Path $Root "portable-output"
$PyInstallerOut = Join-Path $DistRoot "PromptAction"
$PortableDir = Join-Path $PortableRoot "Prompt-Action-Portable-Test"
$ZipPath = Join-Path $PortableRoot "Prompt-Action-Portable-Test-Windows-x64.zip"
$HashPath = "$ZipPath.sha256"
$VersionResource = Join-Path $Root "scripts\windows_version_info.txt"

$PyprojectText = Get-Content (Join-Path $Root "pyproject.toml") -Raw
if ($PyprojectText -notmatch '(?m)^version\s*=\s*"([^"]+)"\s*$') {
    throw "Unable to resolve application version from pyproject.toml"
}
$AppVersion = $Matches[1]
$PromptSystemLabel = (Get-Content (Join-Path $Root "START_HERE.txt") -Raw).Trim()

foreach ($path in @($BuildRoot, $DistRoot, $PortableRoot)) {
    if (Test-Path $path) { Remove-Item $path -Recurse -Force }
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name "PromptAction" `
    --contents-directory "_internal" `
    --version-file "$VersionResource" `
    --hidden-import "PySide6.QtQml" `
    --hidden-import "PySide6.QtQuick" `
    --hidden-import "PySide6.QtQuickControls2" `
    --hidden-import "PySide6.QtQuickLayouts" `
    scripts/portable_entry.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
if (-not (Test-Path (Join-Path $PyInstallerOut "PromptAction.exe"))) {
    throw "Portable executable was not produced"
}

New-Item -ItemType Directory -Force $PortableDir | Out-Null
Copy-Item (Join-Path $PyInstallerOut "*") $PortableDir -Recurse -Force

# Keep canonical data and QML resources external to the frozen runtime so the
# portable folder remains self-contained and writable without Python installed.
Copy-Item (Join-Path $Root "pyproject.toml") $PortableDir -Force
Copy-Item (Join-Path $Root "START_HERE.txt") $PortableDir -Force

foreach ($folder in @("data", "prompts", "backups", "docs")) {
    $source = Join-Path $Root $folder
    if (Test-Path $source) {
        Copy-Item $source (Join-Path $PortableDir $folder) -Recurse -Force
    }
}

$UiTarget = Join-Path $PortableDir "src\prompt_action\ui"
New-Item -ItemType Directory -Force (Split-Path $UiTarget -Parent) | Out-Null
Copy-Item (Join-Path $Root "src\prompt_action\ui") $UiTarget -Recurse -Force

# Include launcher and diagnostic tools for real Windows testing. These tools
# never mutate canonical Prompt/release state; they only write under runtime/.
$PortableScripts = Join-Path $PortableDir "scripts"
New-Item -ItemType Directory -Force $PortableScripts | Out-Null
Copy-Item (Join-Path $Root "scripts\portable_launch.ps1") (Join-Path $PortableScripts "portable_launch.ps1") -Force
Copy-Item (Join-Path $Root "scripts\portable_launch_launcher.bat") (Join-Path $PortableDir "Jalankan Prompt Action.bat") -Force
Copy-Item (Join-Path $Root "scripts\portable_self_check.ps1") (Join-Path $PortableScripts "portable_self_check.ps1") -Force
Copy-Item (Join-Path $Root "scripts\portable_self_check_launcher.bat") (Join-Path $PortableDir "Cek Portable.bat") -Force
Copy-Item (Join-Path $Root "scripts\portable_collect_diagnostics.ps1") (Join-Path $PortableScripts "portable_collect_diagnostics.ps1") -Force
Copy-Item (Join-Path $Root "scripts\portable_collect_diagnostics_launcher.bat") (Join-Path $PortableDir "Buat Paket Diagnostik.bat") -Force

foreach ($runtimeDir in @("runtime", "runtime\logs", "runtime\temp", "runtime\diagnostics")) {
    New-Item -ItemType Directory -Force (Join-Path $PortableDir $runtimeDir) | Out-Null
}

$Readme = @"
PROMPT ACTION — PORTABLE TEST BUILD

Versi aplikasi: $AppVersion
Baseline Prompt: $PromptSystemLabel
Build label: $BuildLabel
Target: Windows 11 x64
Status: UJI COBA / BELUM FINAL

CARA MENJALANKAN
1. Ekstrak seluruh ZIP ke satu folder biasa, misalnya C:\Prompt-Action-Test.
2. Jangan jalankan langsung dari dalam ZIP.
3. Klik dua kali Jalankan Prompt Action.bat.
4. Launcher mengamati startup singkat; jika EXE gagal start atau keluar dengan error, self-check dijalankan otomatis.
5. Tidak perlu memasang Python.

JIKA APLIKASI TIDAK TERBUKA
1. Buka runtime\logs\portable-launch-status.txt untuk hasil startup launcher.
2. Buka runtime\logs\portable-self-check.txt untuk hasil diagnosis otomatis.
3. Kamu juga bisa klik Cek Portable.bat untuk menjalankan pemeriksaan lagi.

JIKA PERLU MENGIRIM LAPORAN BUG
1. Klik dua kali Buat Paket Diagnostik.bat.
2. ZIP diagnostik dibuat di runtime\diagnostics.
3. Paket hanya berisi metadata build, self-check, metadata EXE, dan indeks log yang sudah disamarkan.
4. Isi Prompt, isi backup, settings, isi log aplikasi, path user lokal, dan nama log asli tidak dimasukkan.

CATATAN
- Folder ini portable. Data, Prompt, backup, settings, dan log berada di folder hasil ekstrak.
- Jangan pindahkan hanya file EXE; _internal, data, prompts, backups, src, scripts, dan folder lain harus tetap bersama.
- Windows SmartScreen dapat menampilkan peringatan karena build uji coba ini belum ditandatangani digital.
- STEP 11 Backup Engine belum diaktifkan. Fitur yang tersedia mengikuti implementasi sampai STEP 10 + gate verifier.
- Untuk pengujian release Prompt, gunakan salinan folder ini agar data uji tidak tercampur dengan salinan lain.
"@
$ReadmePath = Join-Path $PortableDir "BACA_DULU.txt"
Set-Content -Path $ReadmePath -Value $Readme -Encoding UTF8

# Fail closed if PowerShell escaping ever introduces non-printing control bytes
# into the user-facing portable instructions. Tabs/newlines/carriage returns are allowed.
$ReadmeCheck = Get-Content -Path $ReadmePath -Raw
if ($ReadmeCheck -match '[\x00-\x08\x0B\x0C\x0E-\x1F]') {
    throw "BACA_DULU.txt contains an unexpected control character"
}
foreach ($requiredText in @("Jalankan Prompt Action.bat", "portable-launch-status.txt", "Cek Portable.bat", "Buat Paket Diagnostik.bat", "runtime\diagnostics", "portable-self-check.txt", "PromptAction.exe", "_internal", "backups", $AppVersion, $PromptSystemLabel)) {
    if (-not $ReadmeCheck.Contains($requiredText)) {
        throw "BACA_DULU.txt is missing required text: $requiredText"
    }
}

$VersionInfo = @"
Prompt Action Portable Test
Application version: $AppVersion
Prompt baseline: $PromptSystemLabel
Build: $BuildLabel
Python runtime: 3.13.16 x64
PyInstaller: 6.22.3
Crash-aware launcher: Jalankan Prompt Action.bat -> runtime\logs\portable-launch-status.txt
Diagnostics self-check: Cek Portable.bat -> runtime\logs\portable-self-check.txt
Diagnostics bundle: Buat Paket Diagnostik.bat -> runtime\diagnostics
"@
Set-Content -Path (Join-Path $PortableDir "BUILD_INFO.txt") -Value $VersionInfo -Encoding UTF8

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $PortableDir -DestinationPath $ZipPath -CompressionLevel Optimal

$Hash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()
Set-Content -Path $HashPath -Value "$Hash  $(Split-Path $ZipPath -Leaf)" -Encoding ASCII

Write-Host "APP_VERSION=$AppVersion"
Write-Host "PROMPT_BASELINE=$PromptSystemLabel"
Write-Host "PORTABLE_DIR=$PortableDir"
Write-Host "ZIP_PATH=$ZipPath"
Write-Host "ZIP_SHA256=$Hash"
