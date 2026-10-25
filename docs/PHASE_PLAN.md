# LeadRevive phase plan

Authoritative input: ../PROJECT_1_CODEX_MASTER_SPEC.md, read completely on 24 October 2026.

## Decisions and environment

Workspace: D:\project 1 -nontech. Initially contained only the specification; no Git repository.
Windows PowerShell; Python 3.14.5 default and 3.13.7 available; Node 23.1.0; npm 10.9.0; Git installed.
Docker 29.5.2 client installed; Linux engine unavailable at inspection. Power BI not detected via standard Program Files path or current-user Store package; installation elsewhere remains possible.

User explicitly approved FastAPI + React, SQLAlchemy + Alembic, final PostgreSQL, and Docker Compose for PostgreSQL/n8n/Mailpit. SQLite permitted for Phase 1 bootstrap. Keep UI simple; business analysis and automation take priority. No authorized business pilot; synthetic portfolio default. No Google Sheets or LLM dependency. No real email without separate explicit approval.

## Delivery sequence and acceptance

| Phase | Scope | Gate |
|---|---|---|
| 0 | Environment, requirements, architecture, references, decisions | Stack approved by user; documented |
| 1 | Generator, portable DB/migrations, validation, conservative dedupe, priority, SQL views/KPIs, exports | Tests pass; fixed-clock SQL reconciliation; SQLite limitation explicit |
| 2 | FastAPI + React overview, queue, detail/history, imports, settings | Persistent actions tested; SS01–SS04 actual app captures |
| 3 | Docker n8n W1/W2, Mailpit, W3 approval and failures | Actual workflow execution; idempotency/cooldown; SS05–SS08; external send separate gate |
| 4 | Cohort analytics, Power BI, controlled experiment | UI/SQL/Power BI reconciliation; SS09–SS10; no fabricated PBIX |
| 5 | Live-data reports, PPTX/DOCX/PDF, business case, demo/UAT/resume evidence | Human narrative review; SS11–SS12 |
| 6 | Clean install, complete integration/UAT, GitHub portfolio | Verify final deliverables before final claims |

Phases 0–4 were approved. Phase 5 was approved subject to audit remediation and now adds validated immutable analytics publications, snapshot-bound reporting, a refined Power BI report, editable Word/PowerPoint, PDF, case study, business case and career/demo materials. See PHASE_5_REPORT.md and PHASE_5_AUDIT_RESOLUTION.md. Stop before Phase 6, GitHub publication or final project sign-off. External live delivery disabled.

## Gap checklist

- Docker Desktop is running; PostgreSQL, n8n, Mailpit and FastAPI/React were executed locally. Runtime availability is checked from the Automations screen.
- PostgreSQL 16.15 connectivity, schema migrations, data preservation and 47 regression tests are verified. SQLite remains a preserved bootstrap/regression path.
- Node 23.1.0 successfully built Vite 7/React 19 and ran Playwright. package-lock.json records resolved dependencies.
- Power BI Desktop was installed locally in Phase 4. The PBIP import model/report was opened, refreshed and saved as a genuine PBIX; actual Desktop DAX reconciles all 13 KPIs. Local CSV paths require adjustment after moving the workspace.
- Migration 0004 adds durable automation/notification/approval/delivery/reminder records. Real run logs and acceptance/capture evidence are available; external email stays disabled.
- Phase 2 and Phase 3 screenshots, extra loaded queue capture and reproduction actions are documented in screenshots/README.md.
