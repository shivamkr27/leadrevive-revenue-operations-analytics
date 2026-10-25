# KPI query pack

Canonical source: local PostgreSQL 16, Alembic revision 0005. All records are synthetic. `v_analytics_leads` joins owner metadata without changing record grain (one row per lead).

Run `scripts/build_phase4.py` to execute `kpi_snapshot.sql` with bound parameters and independently compare every KPI with the application calculation in one repeatable-read transaction. Do not substitute a database password into saved SQL. Host connection: localhost:5433, database/user `leadrevive`; obtain the generated password locally from `.env`.

| File | Purpose | Parameters |
|---|---|---|
| kpi_snapshot.sql | Cohort counts, qualification history, median, rates, exposure | as_of, start, end, source (nullable) |
| management_analysis.sql | Stage/source distribution, owner work, SLA, recovery queue, quality, lost reasons | as_of; cooldown_hours for query 4 |
| automation_evidence.sql | Jobs vs attempts, reminder aggregation, audit failures, SMTP sink acceptance | None; all-time extraction scope |
| inspection.sql | Earlier foundation inspection | See file |

Use canonical UTC text (`2026-10-24T15:44:29.684236Z`, for example); creation window is inclusive start/exclusive end. `as_of` evaluates current records and filters events: it does not reconstruct past stage/ownership. Monetary fields are integer paise in storage; divide by 100 once. Overdue uses strict `<`, SLA breach uses strict `>`; exact deadline is within SLA.

The snapshot exports omit names, email addresses, phone numbers, message bodies, secrets and raw rejected payloads. Source and owner groups reconcile to the full cohort. Grouped source/owner conversion rates describe the selected cohort, not source causality or an eventual win forecast.
