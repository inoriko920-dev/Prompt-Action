param(
    [string]$Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path $Root).Path
$RuntimeDir = Join-Path $Root "runtime"
$LogDir = Join-Path $RuntimeDir "logs"
$DiagDir = Join-Path $RuntimeDir "diagnostics"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $DiagDir | Out-Null

$stamp = [DateTime]::Now.ToString("yyyyMMdd-HHmmss")
$Stage = Join-Path $DiagDir "Prompt-Action-Diagnostic-$stamp"
$Zip = "$Stage.zip"
New-Item -ItemType Directory -Force $Stage | Out-Null

function Write-Utf8File([string]$Path, [string[]]$Lines) {
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

# Run the portable self-check first. A FAIL result is still useful evidence, so
# diagnostic collection continues even when the check returns a non-zero code.
$selfCheck = Join-Path $Root "scripts\portable_self_check.ps1"
if (Test-Path $selfCheck) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $selfCheck -Root $Root -SmokeTest
    $selfCheckExit = $LASTEXITCODE
} else {
    $selfCheckExit = 127
}

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("PROMPT ACTION PORTABLE DIAGNOSTIC BUNDLE")
$summary.Add("Timestamp: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz'))")
$summary.Add("Self-check exit code: $selfCheckExit")
$summary.Add("OS: $([Environment]::OSVersion.VersionString)")
$summary.Add("64-bit OS: $([Environment]::Is64BitOperatingSystem)")
$summary.Add("Machine architecture: $env:PROCESSOR_ARCHITECTURE")
$summary.Add("PowerShell: $($PSVersionTable.PSVersion)")
$summary.Add("")
$summary.Add("PRIVACY SCOPE")
$summary.Add("- Prompt file contents are NOT included.")
$summary.Add("- Backup archive contents are NOT included.")
$summary.Add("- Settings files are NOT included.")
$summary.Add("- Arbitrary application log contents are NOT included.")
$summary.Add("- Absolute portable/user paths are redacted from exported self-check output.")
$summary.Add("- Original runtime log filenames are not exported; only numbered metadata entries are included.")
$summary.Add("- Only build metadata, sanitized self-check output, EXE metadata, and a redacted log index are collected.")
Write-Utf8File (Join-Path $Stage "SUMMARY.txt") $summary

$buildInfo = Join-Path $Root "BUILD_INFO.txt"
if (Test-Path $buildInfo) {
    Copy-Item $buildInfo (Join-Path $Stage "BUILD_INFO.txt") -Force
}

$selfCheckReport = Join-Path $LogDir "portable-self-check.txt"
if (Test-Path $selfCheckReport) {
    $sanitized = Get-Content $selfCheckReport -Raw
    $sanitized = $sanitized.Replace($Root, "<PORTABLE_ROOT>")
    if ($env:USERPROFILE) {
        $sanitized = $sanitized.Replace($env:USERPROFILE, "<USERPROFILE>")
    }
    Set-Content -Path (Join-Path $Stage "portable-self-check.txt") -Value $sanitized -Encoding UTF8
}

$exe = Join-Path $Root "PromptAction.exe"
$exeLines = New-Object System.Collections.Generic.List[string]
if (Test-Path $exe) {
    $info = (Get-Item $exe).VersionInfo
    $exeLines.Add("ProductName: $($info.ProductName)")
    $exeLines.Add("FileDescription: $($info.FileDescription)")
    $exeLines.Add("ProductVersion: $($info.ProductVersion)")
    $exeLines.Add("FileVersion: $($info.FileVersion)")
    $exeLines.Add("OriginalFilename: $($info.OriginalFilename)")
    $exeLines.Add("SizeBytes: $((Get-Item $exe).Length)")
    $exeLines.Add("SHA256: $((Get-FileHash -Algorithm SHA256 $exe).Hash.ToLowerInvariant())")
} else {
    $exeLines.Add("PromptAction.exe: MISSING")
}
Write-Utf8File (Join-Path $Stage "EXE_INFO.txt") $exeLines

# Include only redacted metadata about runtime log files, never their content or
# original filenames. This prevents user-supplied names from leaking via logs.
$logIndex = New-Object System.Collections.Generic.List[string]
$logIndex.Add("RUNTIME LOG INDEX - CONTENTS AND ORIGINAL FILENAMES NOT INCLUDED")
if (Test-Path $LogDir) {
    $i = 0
    Get-ChildItem $LogDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | ForEach-Object {
        $i += 1
        $ext = $_.Extension
        if ([string]::IsNullOrWhiteSpace($ext)) { $ext = "<none>" }
        $logIndex.Add("log[$i] | ext=$ext | bytes=$($_.Length) | modified=$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss zzz'))")
    }
}
Write-Utf8File (Join-Path $Stage "LOG_INDEX.txt") $logIndex

# Record expected portable structure without reading user data files.
$structure = @(
    "PromptAction.exe",
    "_internal",
    "data\version_history.json",
    "prompts",
    "backups",
    "src\prompt_action\ui\qml\App.qml",
    "BUILD_INFO.txt",
    "BACA_DULU.txt",
    "Cek Portable.bat",
    "Buat Paket Diagnostik.bat"
)
$structureLines = New-Object System.Collections.Generic.List[string]
foreach ($relative in $structure) {
    $exists = Test-Path (Join-Path $Root $relative)
    $structureLines.Add("$relative = $exists")
}
Write-Utf8File (Join-Path $Stage "STRUCTURE.txt") $structureLines

if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Stage -DestinationPath $Zip -CompressionLevel Optimal
Remove-Item $Stage -Recurse -Force

$hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
$sidecar = "$Zip.sha256"
Set-Content -Path $sidecar -Value "$hash  $(Split-Path $Zip -Leaf)" -Encoding ASCII

Write-Host "DIAGNOSTIC_ZIP=$Zip"
Write-Host "DIAGNOSTIC_SHA256=$hash"
Write-Host "PRIVACY_SAFE=true"
exit 0
