$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Missing .venv. Run scripts/dev/bootstrap_env.ps1 first."
}
$env:PYTHONPATH = Join-Path $Root "src"
& $Python -m prompt_action @args
exit $LASTEXITCODE
