# Run LeadRevive locally on Windows

Run commands from `D:\project 1 -nontech`. Python 3.14.5 and Node 23.1.0 were used here. SQLite is the permitted bootstrap database; Docker is not needed for this phase. No email or n8n service is started.

## First setup or dependency update

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/generate_synthetic_data.py --seed 42 --count 800
.\.venv\Scripts\python.exe scripts/seed_db.py
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
```

Reusing an existing `.venv` is fine; recreate it only when changing Python versions. `seed_db.py` migrates to head, seeds fictional reps/default settings and imports by content hash; replay does not overwrite edited leads or duplicate rows. No `.env` auto-loader is used: set process environment variables explicitly. Default database is `data/processed/leadrevive.sqlite`.

## Start the complete application

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_phase2.ps1
```

Open **http://127.0.0.1:8000**. API/OpenAPI documentation: **http://127.0.0.1:8000/docs**. Stop with Ctrl+C. The built React UI and API share one local server; no separate Node runtime is required while using the built application.

For reproducible demo evaluation at 24 October 2026, 17:30 IST:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_phase2.ps1 -FixedDemoClock
```

The footer explicitly labels the fixed evaluation clock. Default startup uses the live UTC clock. Overdue counts change with evaluation time and saved schedules. Fixed-clock mode is for synthetic demonstrations; its activity timestamps also use that clock. Choose it at server startup, not as a hidden UI toggle. Refresh workspace data using the top-right refresh button.

## Frontend development

Terminal 1, from root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.api:create_app --factory --host 127.0.0.1 --port 8000
```

Terminal 2, from root:

```powershell
Push-Location frontend
npm.cmd run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8000. Rebuild before using the one-server production preview so it serves the latest source.

## Verification and screenshots

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd test
Pop-Location
```

Playwright owns a temporary database and loopback server on **8010**, uses a fixed demo clock, drives the actual built UI, and writes screenshots into `screenshots/`. Port 8010 must be free. It does not use or edit the main demo DB. Failure traces and HTML reports are ignored by Git and available under `frontend/test-results` and `frontend/playwright-report`. Browser binaries are a one-time installation.

Local single-user scope: keep one server worker and loopback binding. Version checks reject stale writes; an in-process lock serializes local write operations. This is not production authentication or distributed concurrency protection. PostgreSQL migration and runtime tests are still required before final delivery.
