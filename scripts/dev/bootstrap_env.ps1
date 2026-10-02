$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Venv = Join-Path $Root ".venv"
$ExpectedPython = "3.13.16"

$Detected = (& py -3.13 -c "import platform; print(platform.python_version())").Trim()
if ($Detected -ne $ExpectedPython) {
    throw "STEP 01 requires CPython $ExpectedPython for Windows evidence. Found $Detected."
}

if (-not (Test-Path $Venv)) {
    & py -3.13 -m venv $Venv
}
$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Root "requirements-lock.txt")
& $Python -m pip install -e $Root --no-deps --no-build-isolation
Write-Host "Environment ready: $Python"
