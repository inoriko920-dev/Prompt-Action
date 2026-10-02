$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
$env:PYTHONPATH = Join-Path $Root "src"
$env:QT_QPA_PLATFORM = "offscreen"
& $Python -m pytest (Join-Path $Root "tests\step01") -q
exit $LASTEXITCODE
