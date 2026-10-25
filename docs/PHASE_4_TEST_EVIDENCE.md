# Phase 4 verification evidence

All data is synthetic. Snapshot `9a80207b950500a9`, evaluation `2026-10-24T15:44:29.684236Z`. External live delivery disabled.

| Check | Observed result | Evidence / command |
|---|---|---|
| Final PostgreSQL regression suite | 51 tests passed in 151.431 s | `data/processed/phase4_postgres_tests_final.log`; disposable schemas |
| Final SQLite regression suite | 51 tests ran in 96.240 s; 49 passed, two PostgreSQL-only skips | `data/processed/phase4_sqlite_tests_final.log` |
| Updated analytics tests, including added API allowlist test | Four PostgreSQL tests passed in 19.266 s; SQLite three passed/one PostgreSQL-only skip in 2.458 s | `phase4_analytics_postgres_tests.log`, `phase4_analytics_sqlite_tests.log` |
| Existing frontend regression suite | Seven passed in 38.1 s | `cd frontend; npm run build; npm test` |
| Live Compose analytics browser checks | Six checks passed: source filter, workbook download, workflow boundaries, simulation, reconciliation/accessibility, mobile/no JS errors | `node frontend/scripts/test_phase4_browser.mjs`; `phase4_browser.json` |
| Independent KPIs and export readback | All 13 matched API snapshot, PostgreSQL SQL, CSV, Excel and actual Desktop DAX within 1e-8 | `scripts/verify_phase4_pack.py`; `phase4_pack_verification.json` |
| Management/evidence SQL pack | Ten parameterized queries executed successfully | Same pack verifier |
| Original records | All 754 original leads plus related original table rows match preserved SQLite source hashes | Same pack verifier; no source overwrite |
| Power BI model | All 13 actual Desktop DAX measures and snapshot ID matched | `scripts/verify_powerbi.ps1`; `phase4_powerbi.json` |
| Authored report JSON | 45 files validated with no errors against Microsoft schemas | `scripts/validate_powerbi.py`; `phase4_powerbi_schema.log` |
| PBIX integrity | Genuine ZIP container; DataModel and all eight page definitions present | Final `analytics/powerbi/LeadRevive_Phase4_SYNTHETIC.pbix`; opened with Desktop |
| Actual Power BI source slicer | Event selection shows 152; Clear selections restores 758 | `scripts/verify_powerbi_filter.ps1`; `phase4_powerbi_filter.json` |
| Controlled comparison | Same 40 events; 20/34 assumed contacts executed; 40 automation reminder reservations; 24 idempotent hour replays | `scripts/run_phase4_experiment.py`; `analytics/exports/experiment_engine_verification.json` |
| Export manifest | SHA-256 checks passed for the generated pack | `analytics/exports/manifest.json`; same pack verifier |
| Secret/dependency/migration checks | No configured local secrets found in 203 reviewable files or PBIX members; no broken host requirements; no Alembic drift | Final local verification |

The targeted analytics tests are a subset of the 51-test final suite, not additional unique tests. The PostgreSQL-only independent KPI test covers all five source cohorts, an absent source, empty denominator behavior, CSV formula safety, workbook readback, SLA partition and seed/fixture classification. Alembic check also reports no new upgrade operations; host dependency check found no broken requirements.

Early verification caught and corrected a workbook-column assertion, duplicated unittest discovery through an imported TestCase, a double `/api` URL, an exact-label browser selector, the Playwright axe context setup, and a Power BI case-insensitive column/measure name collision. Those failed attempts are not counted as passes. Microsoft-schema validation initially used a deprecated reference resolver; the checked-in version uses the current registry and actually validates every file.

The experiment's review/response timing is modeled. Measured values are local rule-computation durations, not human effort saved. Its raw overdue KPI remains 40 because contacts do not replace next-action dates. Phase 3's real n8n/Mailpit failure and retry evidence remains separate; no external message was sent for Phase 4.

Power BI captures use the report window only. See `screenshots/README.md` for file-to-page mapping. The temporary foreground capture that included an unrelated window was discarded and is not a deliverable.

Generated detailed logs under `data/processed` remain ignored by Git. Reusable tests, scripts, schemas, report definitions, synthetic analysis exports and this result summary are reviewable artifacts. No final-packaging or publishing phase was started.
