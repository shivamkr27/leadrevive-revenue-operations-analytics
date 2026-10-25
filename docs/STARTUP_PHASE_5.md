# Phase 5 startup and reporting

Docker Desktop must be running. All data is synthetic; external live delivery disabled.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
```

Open http://127.0.0.1:8000 and choose Reports. Generate from the validated Analytics snapshot or a fresh PostgreSQL creation window. Fresh cohorts read current record states and do not replace the main Analytics pointer. Download the Word, PDF, PowerPoint, case study, assumptions and metadata. No SMTP or workflow execution is triggered by report generation.

Reports persist under `reports/generated/<report_id>`; generated files are ignored by Git. Do not delete Docker volumes. Analytics generations persist under `analytics/exports/generations`; earlier Phase 4 root exports/PBIX remain preserved. Rebuild a snapshot intentionally with `scripts/build_phase4.py`, not by resetting/seeding the canonical database.

This guide now follows [current setup](SETUP.md); historical Phase 5 execution records remain unchanged. For Power BI, run `.venv\Scripts\python.exe scripts/prepare_powerbi.py --output data/processed/powerbi_portable`, open the resulting PBIP in Desktop, Refresh and save a new PBIX. The helper preserves authored layouts and original artifacts while mapping all six inputs to a verified included generation. [Power BI instructions](../analytics/powerbi/README.md) include manual mappings. Do not recreate authored layouts using the older generator or overwrite prior Desktop evidence. Adjusted models require their own Desktop verification.

Screenshots are used only when their recorded data revision and hashes match. `reports/templates/evidence_images.json` records this binding. A filtered report may omit historical screenshots while retaining all computed figures. The portable PDF comes from the same structured content as the editable report; it is not claimed as a pixel-identical Word conversion. Desktop Office previews, when provided, are separately identified.

Run focused checks with `python -m unittest backend.tests.test_publications backend.tests.test_reporting backend.tests.test_analytics -v`; PostgreSQL variants require an isolated test URL. Historical browser verification is under `frontend/scripts/test_phase5_browser.mjs`; it is not a read-only command for the preserved instance. See PHASE_5_REPORT.md for dated results and FINAL_PUBLICATION_REVIEW.md for current gates. No publication is authorized.
