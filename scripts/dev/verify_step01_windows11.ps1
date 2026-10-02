$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $RepoRoot

$Os = Get-CimInstance Win32_OperatingSystem
if ($Os.Caption -notmatch "Windows 11") {
    throw "STEP 01 local target requires Windows 11. Detected: $($Os.Caption) $($Os.Version)"
}

$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($Identity)
$IsAdmin = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($IsAdmin) {
    throw "T09 requires a non-admin Windows 11 run. Re-run this script from a standard-user PowerShell session."
}

$VenvPython = Join-Path $RepoRoot ".venv/Scripts/python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

& $Python -c "import platform; assert platform.python_version() == '3.13.16', platform.python_version(); import PySide6; assert PySide6.__version__ == '6.11.2', PySide6.__version__"
if ($LASTEXITCODE -ne 0) { throw "Locked Python/PySide6 runtime verification failed." }

$env:QT_QPA_PLATFORM = "windows"
& $Python -m pytest tests/step01 -q
if ($LASTEXITCODE -ne 0) { throw "STEP 01 pytest failed on local Windows 11." }

& $Python scripts/dev/capture_step01_evidence.py
if ($LASTEXITCODE -ne 0) { throw "STEP 01 evidence capture failed on local Windows 11." }

$OutDir = Join-Path $RepoRoot "evidence/step01/local-windows11"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Proof = [ordered]@{
    timestamp_utc = [DateTime]::UtcNow.ToString("o")
    os_caption = $Os.Caption
    os_version = $Os.Version
    os_build = $Os.BuildNumber
    user = $Identity.Name
    elevated = $IsAdmin
    python = (& $Python -c "import platform; print(platform.python_version())")
    pyside6 = (& $Python -c "import PySide6; print(PySide6.__version__)")
    result = "PASS"
}
$Proof | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $OutDir "result.json")
Write-Host "STEP 01 local Windows 11 non-admin verification: PASS"
Write-Host "Evidence: $OutDir"
