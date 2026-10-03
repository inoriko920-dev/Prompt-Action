$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
$env:QT_QPA_PLATFORM = "offscreen"
$env:QT_QUICK_BACKEND = "software"
$env:QSG_RHI_BACKEND = "software"
$env:QSG_RENDER_LOOP = "basic"
$env:QT_QUICK_CONTROLS_STYLE = "Basic"
python scripts/dev/verify_step08_preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/dev/capture_step08_evidence.py --output ci-step08-evidence
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest tests/step08 -q
exit $LASTEXITCODE
