$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $RepoRoot

$EvidenceRoot = Join-Path $RepoRoot "evidence/step01/local-windows11"
$EvidenceZip = Join-Path $RepoRoot "evidence/step01/STEP01_WINDOWS11_LOCAL_EVIDENCE.zip"
$EvidenceZipHash = "$EvidenceZip.sha256.txt"

function Write-Step([string]$Message) {
    Write-Host "[STEP 01] $Message" -ForegroundColor Cyan
}

function Get-LatestPromptActionLog([string]$RuntimeRoot) {
    $LogDir = Join-Path $RuntimeRoot "logs"
    $Log = Get-ChildItem -Path $LogDir -Filter "prompt-action-*.log" -File -ErrorAction Stop |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if (-not $Log) {
        throw "No Prompt Action startup log found under: $LogDir"
    }
    return $Log.FullName
}

Write-Step "Checking target operating system"
$Os = Get-CimInstance Win32_OperatingSystem
$Build = [int]$Os.BuildNumber
if (($Os.Caption -notmatch "Windows 11") -or ($Build -lt 22000)) {
    throw "STEP 01 target verification requires Windows 11. Detected: $($Os.Caption) $($Os.Version), build $($Os.BuildNumber)."
}

Write-Step "Checking that this PowerShell session is NOT elevated"
$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($Identity)
$IsAdmin = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($IsAdmin) {
    throw "T09 requires a non-admin Windows 11 run. Close this window and run STEP_01_VERIFY_WINDOWS11.bat normally (do NOT use Run as administrator)."
}

Write-Step "Preparing exact Python/PySide6 environment"
$VenvPython = Join-Path $RepoRoot ".venv/Scripts/python.exe"
$NeedsBootstrap = -not (Test-Path $VenvPython)
if (-not $NeedsBootstrap) {
    & $VenvPython -c "import platform, PySide6; assert platform.python_version() == '3.13.16'; assert PySide6.__version__ == '6.11.2'" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $NeedsBootstrap = $true
    }
}

if ($NeedsBootstrap) {
    try {
        & (Join-Path $PSScriptRoot "bootstrap_env.ps1")
    }
    catch {
        throw "Could not prepare the locked STEP 01 environment. Install CPython 3.13.16 x64 with the Python Launcher ('py'), then run this verifier again. Original error: $($_.Exception.Message)"
    }
}

$Python = $VenvPython
if (-not (Test-Path $Python)) {
    throw "Locked virtual environment was not created: $Python"
}

$PythonVersion = (& $Python -c "import platform; print(platform.python_version())").Trim()
$PySideVersion = (& $Python -c "import PySide6; print(PySide6.__version__)").Trim()
if ($PythonVersion -ne "3.13.16") {
    throw "Expected CPython 3.13.16, found $PythonVersion."
}
if ($PySideVersion -ne "6.11.2") {
    throw "Expected PySide6 6.11.2, found $PySideVersion."
}

Write-Step "Resetting local evidence workspace"
if (Test-Path $EvidenceRoot) {
    Remove-Item -Recurse -Force $EvidenceRoot
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
if (Test-Path $EvidenceZip) { Remove-Item -Force $EvidenceZip }
if (Test-Path $EvidenceZipHash) { Remove-Item -Force $EvidenceZipHash }

$GitHead = "UNAVAILABLE"
try {
    $GitHeadCandidate = (& git -C $RepoRoot rev-parse HEAD 2>$null).Trim()
    if ($LASTEXITCODE -eq 0 -and $GitHeadCandidate) {
        $GitHead = $GitHeadCandidate
    }
}
catch {
    $GitHead = "UNAVAILABLE"
}

$Preflight = [ordered]@{
    timestamp_utc = [DateTime]::UtcNow.ToString("o")
    os_caption = $Os.Caption
    os_version = $Os.Version
    os_build = $Os.BuildNumber
    process_architecture = $env:PROCESSOR_ARCHITECTURE
    elevated = $false
    python = $PythonVersion
    pyside6 = $PySideVersion
    git_head = $GitHead
}
$Preflight | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "environment.json")

Write-Step "Running STEP 01 test suite"
$env:QT_QPA_PLATFORM = "offscreen"
$TestOutput = & $Python -m pytest tests/step01 -q 2>&1
$TestExit = $LASTEXITCODE
$TestOutput | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "pytest.txt")
if ($TestExit -ne 0) {
    throw "STEP 01 pytest failed on local Windows 11. See evidence/step01/local-windows11/pytest.txt"
}

Write-Step "Running native Windows startup smoke"
$SuccessRuntime = Join-Path $EvidenceRoot "success-runtime"
$env:PROMPT_ACTION_RUNTIME_ROOT = $SuccessRuntime
$env:QT_QPA_PLATFORM = "windows"
$env:QT_QUICK_BACKEND = "software"
$env:QSG_RENDER_LOOP = "basic"
$SuccessConsole = & $Python -m prompt_action --smoke-test-ms 700 2>&1
$SuccessExit = $LASTEXITCODE
$SuccessConsole | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "startup-success-console.txt")
if ($SuccessExit -ne 0) {
    throw "Native Windows startup smoke failed with exit code $SuccessExit."
}
Copy-Item (Get-LatestPromptActionLog $SuccessRuntime) (Join-Path $EvidenceRoot "startup-success.log") -Force

Write-Step "Running intentional native Windows failure smoke"
$FailureRuntime = Join-Path $EvidenceRoot "failure-runtime"
$MissingQml = Join-Path $EvidenceRoot "intentionally-missing.qml"
$env:PROMPT_ACTION_RUNTIME_ROOT = $FailureRuntime
$FailureConsole = & $Python -m prompt_action --qml $MissingQml --smoke-test-ms 1 2>&1
$FailureExit = $LASTEXITCODE
$FailureConsole | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "startup-failure-console.txt")
if ($FailureExit -ne 21) {
    throw "Intentional missing-QML smoke returned $FailureExit; expected exit code 21."
}
Copy-Item (Get-LatestPromptActionLog $FailureRuntime) (Join-Path $EvidenceRoot "startup-failure.log") -Force

Write-Step "Capturing native Windows minimal-window screenshot"
$env:PROMPT_ACTION_RUNTIME_ROOT = (Join-Path $EvidenceRoot "screenshot-runtime")
$env:QT_QPA_PLATFORM = "windows"
$Screenshot = Join-Path $EvidenceRoot "minimal-window.png"
& $Python scripts/dev/capture_step01_evidence.py --screenshot-only $Screenshot
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Screenshot) -or (Get-Item $Screenshot).Length -le 0) {
    throw "Native Windows screenshot capture failed."
}

Write-Step "Writing final local PASS record"
$Result = [ordered]@{
    timestamp_utc = [DateTime]::UtcNow.ToString("o")
    gate = "STEP_01"
    test = "T09_WINDOWS11_NON_ADMIN_AND_TARGET_COMPATIBILITY"
    result = "PASS"
    os_caption = $Os.Caption
    os_version = $Os.Version
    os_build = $Os.BuildNumber
    elevated = $false
    python = $PythonVersion
    pyside6 = $PySideVersion
    pytest_exit_code = $TestExit
    native_startup_exit_code = $SuccessExit
    intentional_failure_exit_code = $FailureExit
    expected_failure_exit_code = 21
    screenshot_file = "minimal-window.png"
    git_head = $GitHead
    privacy_note = "No Windows account name, email, token, API key, or credential is recorded by this verifier."
}
$Result | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot "result.json")

Write-Step "Creating SHA256 manifest"
$ManifestPath = Join-Path $EvidenceRoot "sha256_manifest.txt"
$ManifestLines = @()
Get-ChildItem -Path $EvidenceRoot -File -Recurse |
    Where-Object { $_.FullName -ne $ManifestPath } |
    Sort-Object FullName |
    ForEach-Object {
        $Relative = $_.FullName.Substring($EvidenceRoot.Length).TrimStart('\','/')
        $Hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLowerInvariant()
        $ManifestLines += "$Hash  $Relative"
    }
$ManifestLines | Set-Content -Encoding UTF8 $ManifestPath

Write-Step "Creating portable evidence ZIP"
Compress-Archive -Path (Join-Path $EvidenceRoot "*") -DestinationPath $EvidenceZip -CompressionLevel Optimal
$ZipHash = (Get-FileHash -Algorithm SHA256 $EvidenceZip).Hash.ToLowerInvariant()
"$ZipHash  $(Split-Path $EvidenceZip -Leaf)" | Set-Content -Encoding UTF8 $EvidenceZipHash

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "STEP 01 LOCAL WINDOWS 11 NON-ADMIN VERIFICATION: PASS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Evidence folder : $EvidenceRoot"
Write-Host "Evidence ZIP    : $EvidenceZip"
Write-Host "ZIP SHA256      : $ZipHash"
Write-Host ""
Write-Host "Send these two files back to ChatGPT/SOL for final gate verification:" -ForegroundColor Yellow
Write-Host "1. $EvidenceZip"
Write-Host "2. $EvidenceZipHash"
