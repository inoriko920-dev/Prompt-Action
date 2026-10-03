$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $RepoRoot
try {
    python -m prompt_action.data validate
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m prompt_action.data inspect-active | Out-Null
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m prompt_action.data inspect-prompt P3 | Out-Null
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m prompt_action.data plan-release --primary P3 --sync P1B2 P4 | Out-Null
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    exit 0
}
finally { Pop-Location }
