# Local setup and clean-install verification

Synthetic, single-user demonstration. No external SMTP or public deployment.

## New clone on Windows

Install Docker Desktop (Linux containers), Python 3.11+ and Git. Power BI Desktop is needed only to edit/refresh PBIX files. Node is needed only for host frontend development/tests; Docker builds the UI itself.

```powershell
git clone https://github.com/shivamkr27/leadrevive-revenue-operations-analytics.git leadrevive
cd leadrevive
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
```

`start_local.ps1` generates ignored local credentials, builds the application, migrates/seeds an EMPTY database, imports/publishes four n8n workflows only when absent, and starts loopback services. Existing nonempty databases are not seeded or migrated by this path. Partial workflow sets fail for review rather than being silently overwritten. There is no dependency on a private SQLite file.

| Service | Local URL |
|---|---|
| Application and reports | http://127.0.0.1:8000 |
| OpenAPI | http://127.0.0.1:8000/docs |
| n8n | http://127.0.0.1:5678 |
| Mailpit | http://127.0.0.1:8025 |

Fresh seed: **754 accepted leads**, from 800 raw rows. The reviewed **758** snapshot includes four historical integration fixtures; do not manufacture extra seed leads just to match it. The packaged Analytics snapshot is frozen at its documented time. Live Overview uses the current clock and new-install database. Select fresh cohort reporting or refresh Analytics explicitly when evaluating new data.

n8n owner login uses `N8N_OWNER_EMAIL` and `N8N_OWNER_PASSWORD` from your ignored local `.env`. Inspect them locally; do not paste them into screenshots, issues or the repository.

```powershell
# Optional explicit analytics refresh on your own NEW demo; does not write business records.
docker compose exec -T backend python scripts/refresh_analytics.py
# Stop without removing data:
docker compose stop
# Later start without reinitialization:
docker compose start
```

Do not use `down -v`, reset commands, SQLite-to-Postgres migration or reseeding against a reviewed database. Back up and obtain approval before changing an existing live schema. Pending migration inspection: `docker compose exec -T backend python -m alembic current` and `heads`; do not automatically apply upgrades to an existing installation.

## Documents and Power BI

Use Reports to generate Word/PDF/PPTX from a validated generation, or select a fresh creation window. Empty cohorts produce N/A ratios/median. Historical screenshots appear only for their matched data revision. New cohorts have no claimed Desktop DAX verification until explicitly tested.

Open `analytics/powerbi/LeadRevive_Phase5_SYNTHETIC.pbix` to inspect the saved imported model without refreshing. Create a location-correct editable copy of the authored Phase 5 report with:

```powershell
.venv\Scripts\python.exe scripts/prepare_powerbi.py --output data/processed/powerbi_portable
```

Open `data/processed/powerbi_portable/LeadRevive.pbip` in Desktop, Refresh, clear filters and save a NEW PBIX. The helper verifies the selected generation and changes only six CSV inputs in a derived model; original PBIX/PBIP and authored visuals remain unchanged. Existing output folders are refused: choose another name on repeat runs. Recreate the copy after relocating the clone. See the [Power BI guide](../analytics/powerbi/README.md) for all mappings and the existing-PBIX manual alternative.

Desktop installation, interactive refresh/save remain manual; the helper needs no database or email service. Changed model hashes require new Desktop verification; prior DAX evidence is not silently transferred. Do not rebuild authored layouts with build_powerbi.py. No database credentials are stored in the model.

## QA without touching existing data

```powershell
.venv\Scripts\python.exe scripts/prepare_phase6_qa.py
docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json up -d --wait postgres mailpit n8n
docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json build backend
docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json run --rm --no-deps backend python scripts/bootstrap_demo.py
docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json up -d backend
.venv\Scripts\python.exe scripts/configure_n8n.py --if-needed --project leadrevive-qa --compose-file data/processed/phase6_qa/compose.json --env-file data/processed/phase6_qa/.env --base-url http://127.0.0.1:15678
docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json exec -T backend python scripts/refresh_analytics.py
.venv\Scripts\python.exe scripts/test_phase3_integration.py --isolated-qa
```

QA ports: app **18000**, n8n **15678**, Mailpit **18025**, SMTP **11025**, PostgreSQL **15433**. QA uses separately named volumes/network and output bind folders. The preparer refuses to reset an existing QA configuration. Stop with `docker compose -p leadrevive-qa -f data/processed/phase6_qa/compose.json stop`; retain volumes for inspection. The integration command deliberately adds two fixtures ONLY in QA. Do not run its default mode against a reviewed operational database.

Regression: `.venv\Scripts\python.exe -m unittest discover -s backend/tests -v` uses temporary SQLite by default. PostgreSQL regression requires `LEADREVIVE_TEST_POSTGRES_URL` set to an isolated test instance; never paste passwords into logs. Frontend: `cd frontend`, `npm ci`, `npx playwright install chromium`, `npm run build`, `npm test`. Tests use their own temporary API on port 8010, not the running demo.

Installation verification uses clean volumes/application state with cached Docker images/dependency layers where available; it is not a second operating-system installation or an offline build guarantee.
