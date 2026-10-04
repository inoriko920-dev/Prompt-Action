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

foreach ($runtimeDir in @("runtime", "runtime\logs", "runtime\temp")) {
    New-Item -ItemType Directory -Force (Join-Path $PortableDir $runtimeDir) | Out-Null
}

$Launcher = @'
@echo off
cd /d "%~dp0"
start "" "%~dp0PromptAction.exe"
'@
Set-Content -Path (Join-Path $PortableDir "Jalankan Prompt Action.bat") -Value $Launcher -Encoding ASCII

$Readme = @"
PROMPT ACTION — PORTABLE TEST BUILD

Build label: $BuildLabel
Target: Windows 11 x64
Status: UJI COBA / BELUM FINAL

CARA MENJALANKAN
1. Ekstrak seluruh ZIP ke satu folder biasa, misalnya C:\Prompt-Action-Test.
2. Jangan jalankan langsung dari dalam ZIP.
3. Klik dua kali `Jalankan Prompt Action.bat` atau `PromptAction.exe`.
4. Tidak perlu memasang Python.

CATATAN
- Folder ini portable. Data, Prompt, backup, settings, dan log berada di folder hasil ekstrak.
- Jangan pindahkan hanya file EXE; `_internal`, `data`, `prompts`, `backups`, `src`, dan folder lain harus tetap bersama.
- Windows SmartScreen dapat menampilkan peringatan karena build uji coba ini belum ditandatangani digital.
- STEP 11 Backup Engine belum diaktifkan. Fitur yang tersedia mengikuti implementasi sampai STEP 10 + gate verifier.
- Untuk pengujian release Prompt, gunakan salinan folder ini agar data uji tidak tercampur dengan salinan lain.
"@
Set-Content -Path (Join-Path $PortableDir "BACA_DULU.txt") -Value $Readme -Encoding UTF8

$VersionInfo = @"
Prompt Action Portable Test
Build: $BuildLabel
Python runtime: 3.13.16 x64
PyInstaller: 6.22.3
"@
Set-Content -Path (Join-Path $PortableDir "BUILD_INFO.txt") -Value $VersionInfo -Encoding UTF8

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $PortableDir -DestinationPath $ZipPath -CompressionLevel Optimal

$Hash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()
Set-Content -Path $HashPath -Value "$Hash  $(Split-Path $ZipPath -Leaf)" -Encoding ASCII

Write-Host "PORTABLE_DIR=$PortableDir"
Write-Host "ZIP_PATH=$ZipPath"
Write-Host "ZIP_SHA256=$Hash"
