$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) {
        throw 'Create .venv and install requirements.txt using README instructions first.'
    }
    & $projectPython scripts/generate_synthetic_data.py --seed 42 --count 800
    if ($LASTEXITCODE -ne 0) { throw 'Generator failed' }
    & $projectPython scripts/seed_db.py
    if ($LASTEXITCODE -ne 0) { throw 'Migration/import/KPI run failed' }
    & $projectPython scripts/export_foundation.py
    if ($LASTEXITCODE -ne 0) { throw 'Export failed' }
    & $projectPython -m unittest discover -s backend/tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
    & $projectPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
} finally {
    Pop-Location
}
