param([switch]$FixedDemoClock)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$previousDemoClock=$env:LEADREVIVE_AS_OF
Push-Location -LiteralPath $projectRoot
try {
    $projectPython=Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Follow README setup first: create .venv and install requirements.txt.' }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'Build the frontend first: cd frontend; npm.cmd ci; npm.cmd run build' }
    & $projectPython scripts/seed_db.py
    if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed' }
    if ($FixedDemoClock) { $env:LEADREVIVE_AS_OF='2026-10-24T12:00:00Z' }
    Write-Host 'LeadRevive: http://127.0.0.1:8000 | API docs: http://127.0.0.1:8000/docs | Ctrl+C stops the server'
    & $projectPython -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error' }
} finally {
    if ($FixedDemoClock) {
        if ($null -ne $previousDemoClock) { $env:LEADREVIVE_AS_OF=$previousDemoClock }
        else { Remove-Item Env:LEADREVIVE_AS_OF -ErrorAction SilentlyContinue }
    }
    Pop-Location
}
