# Phase 4 implementation notes

The canonical PostgreSQL database remains intact. Migration 0005 adds a portable lead/owner analytics view; existing tables, records and migrations are preserved. PostgreSQL-specific KPI SQL computes history-aware qualification and continuous median independently of application Python. Both calculations run in one repeatable-read extraction transaction.

`backend/app/analytics.py` builds contact-free lead facts and grouped results. `scripts/build_phase4.py` writes CSVs, styled/filterable Excel sheets, a snapshot and SHA-256 manifest. `analytics_api.py` serves read-only snapshot data and an explicit export allowlist; it returns an actionable error before a snapshot exists and does not expose row facts in the summary response. Compose mounts exports read-only into the backend. Nothing refreshes or sends automatically from the Analytics screen.

`frontend/src/Analytics.jsx` adds functional source filtering, stage/SLA/owner analysis, workflow evidence, controlled comparison, 13 KPI reconciliation rows and Excel/event downloads. Refresh workspace reloads the snapshot; regenerating it is an explicit local command. Operational pages remain live, which is labelled separately from frozen analysis.

`scripts/build_powerbi.py` authors a PBIP report and import model with eight pages and 18 named DAX measures. Desktop was installed locally through Microsoft's winget package, then used to open, refresh and save a genuine PBIX. `verify_powerbi.ps1` checks all 13 reconciled KPIs against the actual local Desktop model and snapshot identity. Report JSON validation checks 45 files against Microsoft schemas. Neither JSON validation nor a PNG is treated as proof of a PBIX by itself.

The report uses PostgreSQL-derived CSVs so no database secret is embedded in the PBIX/model. Absolute local M paths must be regenerated or updated after moving the workspace. Rebuilding PBIP files overwrites generated definitions; preserve manual edits in a copy first. Local Power BI caches are ignored by Git.

`run_phase4_experiment.py` uses identical seed-42 due events and two disposable SQLite databases. It executes real contact/recovery rules, reserves reminders and verifies repeated-hour idempotency. Owner timing remains an explicit assumption. It does not claim to execute n8n or SMTP in the comparison; Phase 3 evidence covers those real integrations separately.

`PHASE_4_PRESENTATION_CONTENT.md` is a seven-slide narrative draft, as requested for review. Final PPTX/DOCX/PDF formatting, demo packaging and publication remain Phase 5/6 work after approval. No external SMTP or live email capability was enabled.
