# Operational impact — evidence and boundaries

SYNTHETIC portfolio case · Snapshot `9a80207b950500a9` · Evaluated 2026-10-24T15:44:29.684236Z (UTC).

All counts below are observed in the local synthetic test ledger at extraction. They include deliberate integration failure scenarios and are not production reliability estimates.

| Evidence | Recorded value | Business purpose / limit |
|---|---:|---|
| Distinct leads with reminder items | 386 | Surfaces due work to assigned owners; does not prove owner action |
| Reminder items | 386 | Lead-level reservations support grouped digests and cooldown |
| Notification drafts | 15 | Reviewable owner notifications and customer-preview drafts |
| Sink-only approvals | 6 | Exact-content approval trail; no authorization for external delivery |
| SMTP accepted by local sink | 13 | Local SMTP acceptance only; 13 captures verified in Mailpit |
| Accepted by local sink after retry | 1 | A failed test send was retried without creating a second capture |
| Failure/uncertain send audit events | 4 | Includes intentionally induced failure; retained even after retry |
| Operator-cancelled notifications | 2 | Prevents further sending without erasing audit history |
| Exact duplicate import rows preserved | 7 | Existing lead history retained without count inflation |
| Conflicting identity rows held for review | 7 | No contradictory automatic merge |
| Invalid import rows rejected | 32 | Visible validation exceptions |

There are 56 distinct recorded jobs and 64 attempts. Latest states show 48 succeeded and 8 failed/partial. Do not divide these into a production reliability claim: latest states combine retries, scheduled/interactive calls and intentional outages. The backend does not count every idempotent replay globally. Duplicate-send prevention and blocked live sending are demonstrated by scenario tests, not by an invented cumulative prevention counter.

## Four deployed workflows

| Workflow | Automated | Manual decision | Intentionally blocked |
|---|---|---|---|
| W1 intake (`intake.json`) | Validate, normalize, detect collisions, assign active owner, persist, draft internal notice | Review invalid/conflicting records | Silent contradictory merge; duplicate intake from the same key |
| W2 recovery (`overdue_recovery.json`) | Hourly scan, eligibility/cooldown, grouped owner reminder reservation and local dispatch | Complete/contact/reschedule lead work | Closed, suppressed, unassigned/inactive-owner work; existing reservation/cooldown duplicates |
| W3 outbox/approval (`email_approval.json`) | Five-minute outbox processing, bounded retry and uncertain-ack reconciliation | Exact-content sink-only customer-preview approval; explicit force-retry/cancel | Unapproved/stale preview, duplicate send, arbitrary SMTP, exhausted retry, external live delivery |
| Status sync (`status_sync.json`) | Versioned state update and stale-reminder cancellation | Authorized initiating lead/status change | Stale-version overwrite and reminders for completed/closed work |

`SS05_n8n_Workflow.png` shows W2 only. It is not evidence that only one workflow exists. All four JSON exports and configured workflow IDs are documented in `automation/README.md` and Phase 3 evidence. The temporary schedule probe was a disabled test helper, not a fifth deployed business workflow.

Customer-preview messages go to the reserved local test sink recipient, not to the lead's synthetic `.example` address. Internal notices use local `.test` sink addresses. **External live delivery disabled.**

The controlled Phase 4 comparison executes 20 versus 34 modeled contacts out of the same 40 events. This is an assumption-driven illustration of review cadence, not observed conversion uplift, human time saved or recovered revenue. See the event CSV and application-rule verification sheet for the calculations.
