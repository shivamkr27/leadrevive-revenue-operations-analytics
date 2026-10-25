$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $projectPython=Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $projectPython scripts/configure_phase3.py
    if ($LASTEXITCODE -ne 0) { throw 'Configuration failed' }
    docker compose up -d --wait postgres mailpit n8n
    if ($LASTEXITCODE -ne 0) { throw 'Docker services failed to start' }
    docker compose build backend
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    docker compose run --rm --no-deps backend python scripts/bootstrap_demo.py
    if ($LASTEXITCODE -ne 0) { throw 'Bootstrap failed; no existing database is overwritten' }
    docker compose up -d backend
    if ($LASTEXITCODE -ne 0) { throw 'Backend startup failed' }
    & $projectPython scripts/configure_n8n.py --if-needed
    if ($LASTEXITCODE -ne 0) { throw 'n8n setup needs review' }
    Write-Host 'http://127.0.0.1:8000 | n8n :5678 | Mailpit :8025. External sending disabled.'
    Write-Host 'Fresh installs contain 754 seed leads; 758 belongs to the reviewed retained-fixture snapshot.'
} finally { Pop-Location }
