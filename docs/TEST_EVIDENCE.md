# Phase 0/1 verification — 24 October 2026

**Current verification:** [Phase 3 test evidence](PHASE_3_TEST_EVIDENCE.md). Earlier phase sections below are historical records, not the current database/integration status.

Actual local execution: Windows PowerShell, Python 3.14.5, SQLAlchemy 2.1.6, Alembic 1.20.1. Dependency versions in requirements.txt match installed versions. No network email was sent and no sender is implemented.

Commands from project root:

```powershell
.\.venv\Scripts\python.exe scripts/generate_synthetic_data.py --seed 42 --count 800
.\.venv\Scripts\python.exe scripts/seed_db.py
.\.venv\Scripts\python.exe scripts/export_foundation.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Observed generator SHA-256: `70170e9f10158b473aceafb5d4e90a2f152a21abc60b802c0255da03f23ed0f0`.
800 raw rows = 754 accepted + 32 invalid + 7 exact duplicates + 7 conflicting identities. All exceptions retained; initial activities, status history and audit events each 754; merge review/duplicate audit 14. Repeating same input reports replay and leaves counts unchanged. Foreign-key consistency query returns no violations.

Fixed evaluation UTC 2026-10-24T00:00:00Z:

| KPI | Observed |
|---|---|
| Accepted distinct leads | 754 |
| Contacted / eligible cohort | 572 / 754 |
| Uncontacted | 182 |
| Median initial response | 59.5 elapsed hours |
| Overdue / open scheduled | 390 / 586 |
| Estimated pipeline exposure | INR 97,967,000 |
| Qualified or later / cohort | 379 / 754 |
| Won / cohort | 62 / 754 |

These are synthetic observations, not revenue improvement or production results. Snapshot JSON is generated locally and reconciled against SQL.

Tests cover repeatability across output directories, safe contacts/false consent, campaign/source/rep/weekend coverage, temporal ordering, intentional fixture counts, count/seed boundaries, migration upgrade/downgrade/rebuild, replay, exception/audit counts, foreign keys, SQL KPI reconciliation, empty cohorts, date windows, malformed values and dates, consent default, closed-stage exclusion and score boundaries/explanations.

An initial test run exposed migration connection pooling holding SQLite files open on Windows. Fixed migration connections to use NullPool; final expanded run passed **13 tests in 7.010 seconds**, without those warnings/errors. Additional tests cover elapsed-SLA boundary, all-overdue/all-contacted datasets, suppressed and unassigned recovery exclusion.

`export_foundation.py`: 633 open priority rows, 46 exceptions, 35 source/stage groups. `seed_db.py` replay=true on repeated run with identical KPI values. `pip check`: No broken requirements found. `git check-ignore` confirms .env, SQLite database and virtual environment are ignored. Local Git initialized without commit or remote publication.

No screenshots required because no visual UI exists. PostgreSQL runtime portability, concurrent API ingestion, full recovery cooldown, email safeguards, workflow execution and Power BI are not claimed tested in Phase 1. Only the generator is stdlib-only; complete foundation requires requirements.txt. No production or external-delivery claims are supported.

## Phase 2 evidence — 24 October 2026

Original Phase 1 gate was re-reviewed before UI work. The expanded 18-test integrity suite passed before Phase 2 implementation. See PHASE_1_INTEGRITY_REVIEW.md for gaps and fixes.

Final expanded backend/API suite: **30 tests passed in 25.172 seconds**, including a populated 0001-to-head upgrade, canonical precision, qualification history after Lost, stale writes, first-contact preservation, safe manual creation, CSV replay/size/schema checks, invalid/identity review guards, settings persistence, local-origin rejection, missing records, and unavailable/unmigrated database handling.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm.cmd run build
npm.cmd test
Pop-Location
```

Observed Alembic check: `No new upgrade operations detected.` Observed pip check: `No broken requirements found.` Frontend install audit reported zero vulnerabilities. Vite production build succeeded. Browser suite: **7 connected scenarios passed**; axe checks reported no violations for the tested WCAG 2 A/AA rule tags on overview, queue, lead detail, quality review, settings and mobile overview. This is automated accessibility evidence, not a complete accessibility certification.

Browser scenarios: API-to-card reconciliation/source/cohort filters; queue filtering/sorting/pagination/export/empty/reset; safe lead creation and assign/stage/schedule/contact persistence after reload; CSV replay and audited conflict decision without changing existing lead exports; settings validation/persistence with email disabled; mobile navigation/no body overflow; explicit 503 error display and recovery.

Early browser runs found and corrected a local-origin guard rejecting same-origin test-port assets, missing exact filter labels, muted-text contrast, help-icon ARIA semantics, and an overly broad test status locator. These failed intermediate runs are not counted as successful evidence. Final screenshots are regenerated from the actual passing app. Browser data is temporary; the main demo database remains unchanged by those tests.

Versions: React 19, Vite 7, FastAPI 0.162.0, SQLAlchemy 2.1.6, Alembic 1.20.1. Actual frontend versions resolved in package-lock.json. Starlette HTTPX deprecation and Node/npm experimental module/color-environment warnings are non-failing toolchain messages. PostgreSQL, n8n, SMTP/Mailpit and Power BI are still unverified and out of Phase 2 scope.

Final browser run after readability/formatting and screenshot cleanup: **7 passed in 33.1 seconds**. Documented `start_phase2.ps1 -FixedDemoClock` launched the built app on port 8000. Smoke requests to `/`, `/docs`, `/api/health` and `/api/overview` returned 200; health reported SQLite, migration 0003, fixed clock true. Unmodified main demo data at 12:00 UTC: 754 leads, 404 overdue, INR 102,603,000 estimated pipeline exposure. The startup verification service was stopped after review.

Interactive API documentation was also checked in Chromium after configuring its docs-only asset policy: Swagger UI rendered the API title and **17 documented operations**, with zero browser JavaScript errors. Built app assets remain restricted to the local origin; only FastAPI's documentation pages permit their Swagger/ReDoc CDN assets.
# Current analytics evidence

Phase 4 results, 13-KPI reconciliation, real Power BI Desktop verification, controlled comparison, export checks and preserved-record checks are documented in [PHASE_4_TEST_EVIDENCE.md](PHASE_4_TEST_EVIDENCE.md). Earlier phase results below remain historical evidence. External live delivery disabled.

