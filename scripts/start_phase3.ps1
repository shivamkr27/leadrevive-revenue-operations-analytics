$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $projectPython=Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Create .venv and install requirements.txt first (see docs/STARTUP_PHASE_3.md).' }
    & $projectPython scripts/configure_phase3.py
    if ($LASTEXITCODE -ne 0) { throw 'Local configuration failed' }
    docker compose up -d --wait postgres mailpit n8n
    if ($LASTEXITCODE -ne 0) { throw 'Docker services did not start. Check Docker Desktop.' }
    & $projectPython scripts/initialize_phase3_db.py
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL verification failed. SQLite remains preserved.' }
    docker compose up -d --build backend
    if ($LASTEXITCODE -ne 0) { throw 'Backend build/start failed' }
    & $projectPython scripts/configure_n8n.py --if-needed
    if ($LASTEXITCODE -ne 0) { throw 'n8n setup requires review' }
    Write-Host 'LeadRevive: http://127.0.0.1:8000 | n8n: http://127.0.0.1:5678 | Mailpit: http://127.0.0.1:8025'
    Write-Host 'External sending disabled. Stop services with: docker compose stop'
} finally {
    Pop-Location
}
