$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $Root
try {
    $env:PYTHONUTF8 = '1'
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:QT_QUICK_BACKEND = 'software'
    $env:QSG_RHI_BACKEND = 'software'
    $env:QSG_RENDER_LOOP = 'basic'
    $env:QT_QUICK_CONTROLS_STYLE = 'Basic'
    python scripts/dev/verify_step09_preflight.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m pytest tests/step09 -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m pytest tests/step01 tests/step02 tests/step03 tests/step04 tests/step05 tests/step06 tests/step07 tests/step08 -q
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
