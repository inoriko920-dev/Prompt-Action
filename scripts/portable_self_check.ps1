param(
    [string]$Root = (Get-Location).Path,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path $Root).Path
$RuntimeDir = Join-Path $Root "runtime"
$LogDir = Join-Path $RuntimeDir "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$Report = Join-Path $LogDir "portable-self-check.txt"

$lines = New-Object System.Collections.Generic.List[string]
function Add-Line([string]$Text) {
    $lines.Add($Text)
    Write-Host $Text
}

Add-Line "PROMPT ACTION PORTABLE SELF-CHECK"
Add-Line "Timestamp: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz'))"
Add-Line "Root: $Root"
Add-Line "OS: $([Environment]::OSVersion.VersionString)"
Add-Line "64-bit OS: $([Environment]::Is64BitOperatingSystem)"
Add-Line ""

$required = @(
    "PromptAction.exe",
    "_internal",
    "data\version_history.json",
    "prompts",
    "backups",
    "src\prompt_action\ui\qml\App.qml",
    "BUILD_INFO.txt",
    "BACA_DULU.txt"
)

$failed = $false
foreach ($relative in $required) {
    $path = Join-Path $Root $relative
    if (Test-Path $path) {
        Add-Line "[OK] $relative"
    } else {
        Add-Line "[MISSING] $relative"
        $failed = $true
    }
}

try {
    $probe = Join-Path $RuntimeDir ".write-test.tmp"
    Set-Content -Path $probe -Value "ok" -Encoding ASCII
    Remove-Item $probe -Force
    Add-Line "[OK] runtime folder writable"
} catch {
    Add-Line "[FAIL] runtime folder not writable: $($_.Exception.Message)"
    $failed = $true
}

$exe = Join-Path $Root "PromptAction.exe"
if (Test-Path $exe) {
    $v = (Get-Item $exe).VersionInfo
    Add-Line "ProductName: $($v.ProductName)"
    Add-Line "ProductVersion: $($v.ProductVersion)"
    Add-Line "FileVersion: $($v.FileVersion)"
    Add-Line "OriginalFilename: $($v.OriginalFilename)"
}

$buildInfo = Join-Path $Root "BUILD_INFO.txt"
if (Test-Path $buildInfo) {
    Add-Line ""
    Add-Line "BUILD_INFO.txt:"
    foreach ($line in (Get-Content $buildInfo)) { Add-Line "  $line" }
}

if ($SmokeTest -and (Test-Path $exe)) {
    Add-Line ""
    Add-Line "Running frozen smoke test..."
    $p = Start-Process -FilePath $exe -ArgumentList "--smoke-test-ms", "1000" -Wait -PassThru
    Add-Line "Smoke test exit code: $($p.ExitCode)"
    if ($p.ExitCode -ne 0) { $failed = $true }
}

Add-Line ""
if ($failed) {
    Add-Line "RESULT: FAIL"
} else {
    Add-Line "RESULT: PASS"
}

$lines | Set-Content -Path $Report -Encoding UTF8
Write-Host "REPORT=$Report"

if ($failed) { exit 1 }
exit 0
