param(
    [string]$Root = (Get-Location).Path,
    [switch]$SmokeTest,
    [int]$EarlyExitWindowSeconds = 3
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path $Root).Path
$RuntimeDir = Join-Path $Root "runtime"
$LogDir = Join-Path $RuntimeDir "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$StatusPath = Join-Path $LogDir "portable-launch-status.txt"
$Exe = Join-Path $Root "PromptAction.exe"
$SelfCheck = Join-Path $Root "scripts\portable_self_check.ps1"

function Write-Status([string[]]$Lines) {
    $Lines | Set-Content -Path $StatusPath -Encoding UTF8
    foreach ($line in $Lines) { Write-Host $line }
}

function Run-SelfCheck {
    if (Test-Path $SelfCheck) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SelfCheck -Root $Root -SmokeTest
        return $LASTEXITCODE
    }
    return 127
}

$stamp = [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz')
if (-not (Test-Path $Exe)) {
    Write-Status @(
        "PROMPT ACTION PORTABLE LAUNCH",
        "Timestamp: $stamp",
        "RESULT: FAIL",
        "Reason: PromptAction.exe is missing.",
        "Next: run Cek Portable.bat or Buat Paket Diagnostik.bat."
    )
    [void](Run-SelfCheck)
    exit 2
}

$args = @()
if ($SmokeTest) {
    $args = @("--smoke-test-ms", "900")
}

try {
    $process = Start-Process -FilePath $Exe -ArgumentList $args -PassThru
} catch {
    Write-Status @(
        "PROMPT ACTION PORTABLE LAUNCH",
        "Timestamp: $stamp",
        "RESULT: FAIL",
        "Reason: failed to start PromptAction.exe.",
        "Error: $($_.Exception.Message)",
        "Next: run Cek Portable.bat or Buat Paket Diagnostik.bat."
    )
    [void](Run-SelfCheck)
    exit 3
}

if ($SmokeTest) {
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    if ($exitCode -eq 0) {
        Write-Status @(
            "PROMPT ACTION PORTABLE LAUNCH",
            "Timestamp: $stamp",
            "Mode: SMOKE_TEST",
            "RESULT: PASS",
            "ExitCode: 0"
        )
        exit 0
    }

    Write-Status @(
        "PROMPT ACTION PORTABLE LAUNCH",
        "Timestamp: $stamp",
        "Mode: SMOKE_TEST",
        "RESULT: FAIL",
        "ExitCode: $exitCode",
        "Next: run Cek Portable.bat or Buat Paket Diagnostik.bat."
    )
    [void](Run-SelfCheck)
    exit $exitCode
}

$waitMs = [Math]::Max(1, $EarlyExitWindowSeconds) * 1000
$exitedEarly = $process.WaitForExit($waitMs)
if (-not $exitedEarly) {
    Write-Status @(
        "PROMPT ACTION PORTABLE LAUNCH",
        "Timestamp: $stamp",
        "RESULT: STARTED",
        "ProcessId: $($process.Id)",
        "ObservationWindowSeconds: $EarlyExitWindowSeconds"
    )
    exit 0
}

$earlyCode = $process.ExitCode
if ($earlyCode -eq 0) {
    Write-Status @(
        "PROMPT ACTION PORTABLE LAUNCH",
        "Timestamp: $stamp",
        "RESULT: EARLY_EXIT_ZERO",
        "ExitCode: 0",
        "ObservationWindowSeconds: $EarlyExitWindowSeconds",
        "Note: application exited quickly but did not report a process error."
    )
    [void](Run-SelfCheck)
    exit 0
}

Write-Status @(
    "PROMPT ACTION PORTABLE LAUNCH",
    "Timestamp: $stamp",
    "RESULT: FAIL",
    "Reason: application exited during startup window.",
    "ExitCode: $earlyCode",
    "ObservationWindowSeconds: $EarlyExitWindowSeconds",
    "Next: open runtime\logs\portable-self-check.txt or run Buat Paket Diagnostik.bat."
)
[void](Run-SelfCheck)
exit $earlyCode
