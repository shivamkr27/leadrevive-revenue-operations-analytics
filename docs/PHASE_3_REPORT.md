# Phase 3 — verified automation implementation

Date: 24 October 2026. Scope: real local n8n + PostgreSQL + Mailpit, connected to FastAPI and the operations interface. Synthetic portfolio case; no external email or real revenue outcome is claimed.

## Delivery and business purpose

| Automation | Working behavior | Business significance and observed evidence |
|---|---|---|
| W1: Intake, validate, assign | Authenticated n8n webhook validates safe input through FastAPI, checks identity collisions, assigns unassigned enquiries round-robin across active owners, persists lead/history and an internal task. Rejections remain visible in Data Quality. | Gives a valid new enquiry an accountable owner and first-response task. Real repeated webhook returned the same lead/draft, without duplicate intake. |
| W2: Overdue recovery | Hourly Schedule Trigger plus authenticated manual webhook scans eligible open overdue leads, excludes inactive/unassigned/suppressed/closed/completed work, reserves reminders transactionally, groups one digest per owner and sends only current items to Mailpit. | Directs attention to missed follow-ups while reducing repetitive reminders. Real scenario transitioned from upcoming to overdue and produced one digest; a later scan within the rolling cooldown produced none. Unit test groups two leads for one owner into one digest. |
| W3: Approved outbox | Five-minute scheduled outbox/manual webhook processes internal tasks and explicitly approved contact previews. Approval records the exact content/context hash. Lead changes invalidate stale approvals. SMTP goes exclusively to reserved Mailpit test inboxes. | Makes review accountable and protects contacts from unapproved sending. UI approval and n8n execution produced one actual Mailpit capture. Synthetic contacts and missing consent remain explicitly blocked for any live sending. |
| Status synchronization | Authenticated n8n event applies stage/owner/schedule changes with an expected lead version, updates history and invalidates obsolete reminder work. | Prevents stale events from overwriting newer sales decisions. A real versioned Won event persisted; an older conflicting event failed and preserved the current state. The Won state was a controlled test, not a customer win. |
| Failure/retry controls | Durable run and delivery records; stable Message-ID; Mailpit lookup before transmission; bounded attempts and backoff; explicit cancellation; unknown SMTP acceptance held for reconciliation. | Failures are visible instead of silently losing work. Actual SMTP 451 rejection was logged, provider recovered, retry captured one message, and replay did not create another. |

These are demonstrated workflow correctness/coverage results. No measured customer adoption, recovered revenue, time saving or business ROI is asserted. The controlled baseline/automation experiment and full analytics model remain Phase 4.

## Persistence and preservation

- PostgreSQL **16.15** is now the application system of record. n8n **2.44.6**, Mailpit **1.32.0**, and FastAPI run through Docker Compose on loopback ports.
- Before switching, SQLite was backed up using its backup API. All **754 original leads**, four owners, 46 exceptions, 754 activities, 754 status-history records, 14 merge-audit records, 754 audit records and configuration rows reconciled by primary key and SHA-256. The fixed baseline KPI dictionaries matched exactly.
- SQLite and its backups are retained, ignored by Git, and no longer the normal application database. New startup records a verified migration marker and never recopies SQLite over subsequently edited PostgreSQL data.
- Migration **0004** adds durable automation runs, notification drafts, exact-content approvals, delivery ledger and reminder items. The previous three revisions remain intact. Alembic schema check reports no new upgrade operations.
- Scenario tests add clearly named fictional records; they do not modify original source rows. The completed real integration and UI scenarios preserve the original rows/history. Local evidence records scenario IDs and timestamps.

## Sending and approval boundaries

This phase implements local sink delivery only. Internal envelopes use `rep-N@leadrevive.test`; contact previews use `approved-preview@leadrevive.test`. The intended `.example` contact is reference metadata, never the real envelope recipient. Every message is labeled SYNTHETIC / LOCAL MAILPIT TEST ONLY.

The application rejects `mode=live`, reports external delivery disabled, and contains no general SMTP-provider transport. Mailpit relay/forwarding is not configured. Enabling an environment flag cannot enable external sending. Preview approval explicitly authorizes Mailpit capture; it does not invent consent or authorize contacting the fictional lead.

SMTP acceptance is recorded separately from verified Mailpit capture, and never described as external inbox delivery. Duplicate prevention combines job idempotency, transactional PostgreSQL locking/reservations, per-draft delivery uniqueness and stable Message-ID lookup. A lost acknowledgement is reconciled before retry; unresolved uncertainty blocks automatic resend. This is not a claim of universal exactly-once external SMTP delivery.

## Verification results

- **47 tests passed on PostgreSQL**, including concurrency, schema upgrades/rollback, all previous business/API checks, owner grouping, cooldown, stale/cancelled approvals, retry and simulated acknowledgement loss.
- SQLite regression: **47 tests run, 46 passed, one PostgreSQL-specific concurrency test skipped**.
- **19 real n8n/PostgreSQL/Mailpit integration checks passed**, including actual SMTP 451 fault injection and safe retry.
- **Seven existing browser scenarios passed** after Phase 3 UI changes.
- **Six additional real browser checks passed**: preview/approval controls, actual n8n-to-Mailpit send, accessibility/JavaScript checks, operator cancellation confirmation/evidence, real n8n workflow canvas, real Mailpit message view.
- A temporary **five-second Schedule Trigger** executed a real zero-lead-scope job with a recorded n8n execution ID, then was unpublished and verified inactive. The four normal workflow schedules/exports are retained; this does not claim waiting a full hour for the hourly trigger.
- Real service-outage checks confirm stopped Mailpit reports unreachable, and stopped n8n yields 503 plus a durable failed trigger, followed by restoration.

Evidence commands, timestamps, IDs and artifacts are in TEST_EVIDENCE.md and ignored `data/processed/phase3_*.json`. Actual screenshots are linked in screenshots/README.md.

## Issues found and resolved

Docker Desktop did not provide host connectivity on the initial internal-only network; recreating the services on a normal Compose bridge restored loopback mappings and service aliases without replacing their data volumes. PostgreSQL reconciliation was rerun successfully before switching.

Real fault testing exposed n8n treating a top-level `error` item as retryable even for an HTTP-200 business result. Integration responses now use `status` / `failure_reason`; HTTP/network failures remain retryable, while business delivery retry timing and limits remain in the outbox. The initially exhausted synthetic fixture was explicitly cancelled with audit evidence retained, then the complete scenario passed on fresh fictional fixtures.

One PostgreSQL run was interrupted by a service rebuild and is not counted as a passing run; the final complete 47-test PostgreSQL run passed. No intermediate failed test run is represented as successful evidence.

## Limits and next gate

Local single-user scope; no production authentication, public hosting or high-volume concurrency claim. n8n stores its own workflow/credential/execution metadata in its persistent local volume; PostgreSQL owns business data. Recent-run UI shows the last 100 jobs. Outbox processing handles up to 50 eligible drafts per run. Reminder cooldown defaults to 24 elapsed hours. SMTP retries are capped at three delivery attempts, with 1/2/4-minute retry eligibility; the five-minute schedule may retry later. An explicit operator retry can bypass waiting but cannot exceed the limit. Cancelled/failed records and approvals remain auditable.

Recording a contact after an overdue due date completes that recovery action and prevents repeated reminders for that same due date. The lead's overdue KPI still follows its stored schedule until the user schedules the next action; this distinction is visible in lead tracking. Internal tasks do not require contact-preview approval. Keep Mailpit captures while uncertain outcomes need reconciliation.

**Stop before Phase 4 for user review.** No Power BI integration or Phase 4 experiment has begun. External sending still requires a separate future explicit authorization and implementation review.
