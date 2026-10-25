# Phase 3 test evidence — 24 October 2026

All results below are observed local execution. Synthetic scenario data only. No external email was sent.

| Verification | Observed outcome |
|---|---|
| Extra loaded Recovery Queue capture | PASS: 12 actual rows, 85 Rep-1 overdue matches; owner/overdue filters, descending value and priority sorts, and open lead detail verified |
| SQLite-to-PostgreSQL reconciliation | PASS: all 754 original leads and related source rows match by primary key and SHA-256; fixed-clock KPI dictionaries identical; backups retained |
| PostgreSQL regression | **47 tests passed in 124.473s**, isolated schemas; includes real concurrent reservation test |
| SQLite regression | **47 tests run in 50.118s**, 46 passed and one PostgreSQL-only concurrency test skipped |
| Alembic check on canonical PostgreSQL | `No new upgrade operations detected.` |
| Container dependency check | `No broken requirements found.` |
| Real n8n/PostgreSQL/Mailpit scenarios | **19 checks passed**, including actual SMTP 451 rejection, successful retry and no duplicate capture |
| Existing browser regression | **7 scenarios passed in 35.8s**; previous functional and responsive behavior preserved |
| Additional Phase 3 browser checks | **6 checks passed**, including actual UI approval/send, one Mailpit capture, cancellation/no-transmission confirmation, WCAG A/AA checks/no JS errors, n8n editor and Mailpit message view |
| Actual scheduled trigger | PASS: five-second zero-lead test job executed with recorded n8n execution ID; test workflow then unpublished and CLI-export verified inactive |
| Provider outages | PASS: Mailpit offline status truthful; n8n offline returns 503 and durable failed trigger; both restored and external sending still disabled |

## Real scenario details

`scripts/test_phase3_integration.py` drives actual authenticated n8n webhooks and real provider APIs:

1. Confirms PostgreSQL/migration 0004 and every original source row before testing.
2. Submits a fictional enquiry through W1; owner assigned and internal task created.
3. Replays the same intake; receives the same lead/draft, without another lead.
4. Confirms future follow-up produces no overdue digest.
5. Sends the internal task over SMTP to Mailpit and verifies its capture by stable Message-ID.
6. Waits for the actual short scenario deadline, then W2 creates/sends one overdue digest.
7. Repeated scan inside cooldown creates no duplicate reminder.
8. Records follow-up completion; later scan excludes the completed due action.
9. Synchronizes a test Won state through n8n, rejects a stale conflicting version, and checks state/audit.
10. Creates a second fictional lead/preview; unapproved sink-send and live-mode attempts are rejected.
11. Records sink-only exact-content approval, invokes n8n delivery and verifies one real capture.
12. Repeats send with the same and a different request key; capture count remains one.
13. Uses Mailpit Chaos to return an actual **451** sender rejection. Checks failed ledger/no captured message.
14. Restores Mailpit's normal SMTP behavior in `finally`, retries through n8n and verifies one capture with two delivery attempts; replay does not resend.
15. Rejects a bad n8n header and re-verifies external sending disabled and original rows unchanged.

The script records 19 assertions across these steps. Its JSON evidence stores actual run/draft/lead IDs, provider errors, acceptance/capture evidence and timestamps. It adds two named fictional leads per execution; the initial failed intermediate run and final successful run leave four controlled records in this workspace, so current lead count is **758**, including the 754 preserved originals. The browser continues the successful controlled lead through a further stage/approval/send; it does not add another lead.

## Reproducible commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe scripts/test_postgres.py
.\.venv\Scripts\python.exe scripts/test_phase3_integration.py
.\.venv\Scripts\python.exe scripts/verify_schedule.py
.\.venv\Scripts\python.exe scripts/verify_service_failures.py
docker compose exec -T backend python -m alembic check
docker compose exec -T backend python -m pip check
Push-Location frontend
npm.cmd run build
npm.cmd test
node scripts/capture_loaded_queue.mjs
node scripts/test_phase3_browser.mjs
Pop-Location
```

The final PostgreSQL suite ran inside the backend container with `LEADREVIVE_TEST_POSTGRES_URL` set internally from its existing `DATABASE_URL`, avoiding secret output. Each test uses a generated schema and cleans it up; the one leftover schema from an interrupted rebuild run was removed only after all tests finished. Public business tables were not dropped.

## Artifacts

Ignored local evidence under `data/processed`:

- `postgres_migration.json`: backup path, per-table original row counts/hashes and matching KPI dictionaries.
- `phase3_queue_verification.json`: populated queue checks and opened lead ID.
- `phase3_integration.json`: 19 real service assertions and scenario/delivery evidence.
- `phase3_browser.json`: UI approval/send/accessibility checks and captured message ID.
- `phase3_schedule.json`: actual scheduled run/execution ID plus verified unpublished test state.
- `phase3_service_failures.json`: provider outage outcomes and failed-trigger run ID.
- `phase3_final_state.json`: final provider reachability, external sending disabled, 758 total leads with original rows verified, four business workflows active and the schedule probe inactive, plus working workflow downloads.

Actual Chromium images: `SS02b_Recovery_Queue_Loaded.png`, `SS05_n8n_Workflow.png`, `SS06_Automation_Run_Log.png`, `SS07_Email_Preview_Approval.png`, `SS08_Test_Email_Sink.png`. SS07 is a crop of the actual message/approval panel before the send action; SS08 is the actual captured SMTP message. No mockups or invented execution screenshots.

Intermediate failures are retained/explained in PHASE_3_REPORT.md. The real SMTP test found and corrected n8n's top-level `error` retry interaction. An exhausted intermediate test message was explicitly cancelled with audit evidence preserved. Final successful assertions do not include failed/interrupted attempts as passing runs.

The five-second probe proves a real Schedule Trigger; it does not claim an hour elapsed. The probe remains unpublished, while normal hourly/five-minute business workflows remain available. Mailpit Chaos is restored to zero rejection probability. Toolchain deprecation warnings from Starlette HTTPX and host Node/npm did not fail validation.

The documented `start_phase3.ps1` completed successfully with existing records and n8n workflows preserved. Final checks verified all four workflow downloads, both provider health endpoints, canonical PostgreSQL state and original source-row hashes. Generated service-secret values were scanned against all nonignored text files and workflow exports: none found. SQLite backups, `.env`, databases, browser reports and runtime evidence remain ignored by Git.

Final UI regression also verified cancellation displays a success confirmation after the backend marks a message cancelled, with no SMTP delivery. It caught and corrected a client status check that previously treated that successful cancellation state as an error. Approval/sending and cancellation both passed afterward.
