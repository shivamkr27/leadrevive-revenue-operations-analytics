# Start and review Phase 4

All data is synthetic; external live delivery disabled. Existing PostgreSQL records and Docker volumes are preserved.

From `D:\project 1 -nontech`:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_phase3.ps1
```

The existing startup script applies the current Alembic head (0005), starts PostgreSQL/n8n/Mailpit/backend, and preserves the initialized database. Open http://127.0.0.1:8000 and choose **Analytics**. The delivered snapshot is already present; downloading Excel or CSV does not send messages or change leads.

Open `analytics/powerbi/LeadRevive_Phase4_SYNTHETIC.pbix` with Power BI Desktop. Its imported snapshot works without a database login. Use the source-page slicer and clear filters before comparing whole-cohort totals.

## Refresh analytics intentionally

```powershell
.venv\Scripts\python.exe scripts/build_phase4.py
.venv\Scripts\python.exe scripts/run_phase4_experiment.py
```

The first command replaces the frozen exports from PostgreSQL. The second executes a comparable simulated event cohort in disposable SQLite databases and adds its verification. Refresh Desktop, then:

To select a creation cohort, pass `--start 2026-07-01T00:00:00Z --end 2026-10-25T00:00:00Z` to `build_phase4.py`. Start is inclusive, end exclusive. The resulting window appears in snapshot metadata and Excel ReadMe; use the same refreshed pack in Power BI. This changes the review snapshot intentionally and does not reconstruct historical stage/owner states.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_powerbi.ps1
.venv\Scripts\python.exe scripts/build_phase4.py --apply-powerbi-verification
```

Save the refreshed PBIX and reload the Analytics page. This is an explicit snapshot refresh, not historical reconstruction. Operations screens use the current clock and can differ after lead changes or due-date crossings. Never mix a new export with an old PBIX screenshot.

## Verification

```powershell
.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.venv\Scripts\python.exe scripts/test_postgres.py
cd frontend
npm ci
npm run build
npm test
node scripts/test_phase4_browser.mjs
```

PostgreSQL tests use isolated schemas; they do not reset the canonical demo database. Standard Playwright tests use disposable data on port 8010. The additional Phase 4 browser script checks the running Compose application on port 8000 and captures Analytics/experiment evidence. Power BI validation is documented in `analytics/powerbi/README.md`.

Review `PHASE_4_REPORT.md`, `PHASE_4_BUSINESS_IMPACT.md`, the reconciliation CSV and screenshots before approving Phase 5. The presentation supplied at this gate is review content; final PPTX/DOCX/PDF packaging has not started.
