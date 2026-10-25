# Data dictionary — SYNTHETIC

Raw fixture CSV fields follow master-spec minimum lead fields plus `fixture_case`, which is testing metadata and never used to decide validation acceptance.

| Fields | Meaning / storage |
|---|---|
| lead_id | Stable SYN-prefixed input identity; primary key |
| created_at, updated_at | UTC ISO timestamp; offset required; updates cannot predate creation |
| full_name, company | Numbered fiction, required |
| email | Trimmed, case-normalized, format checked; reserved .example in fixtures |
| phone | Non-dialable FICTIONAL-IN token; nonfixture number requires explicit 91 country context |
| lead_source, campaign, industry, company_size | Source enum and segmentation dimensions |
| estimated_deal_value_inr | Raw decimal INR; persisted as estimated_value_paise integer, nonnegative |
| stage | New, Contacted, Qualified, Meeting, Proposal, Won, Lost |
| owner_id | Nullable foreign key; assigned input owner must exist and be active |
| consent_to_email, email_verified | Explicit booleans, default false; never authorize a send by themselves |
| last_contacted_at, first_contacted_at | Fixture has one contact; both match. Real activity model must maintain independently |
| next_action_at | Nullable follow-up schedule; missing is not automatically overdue |
| response_sla_hours | Positive integer; elapsed-hour SLA |
| lost_reason | Fictional reason on Lost rows |
| created_by, scenario_label | Generator attribution and mandatory SYNTHETIC origin |
| suppressed, version | Default false / 1; lifecycle editing arrives Phase 2 |

Tables: owners; leads; import_batches (unique content hash); import_rejections (raw JSON and reason); lead_activities; lead_status_history; lead_merge_audit; audit_events; config. History/event payloads are JSON text for SQLite/PostgreSQL portability. Event timestamps are recorded import time; source timestamps remain on lead records.

Phase 3 migration 0004 adds:

| Table | Meaning / constraints |
|---|---|
| automation_runs | Unique workflow/business idempotency key, semantic payload hash, n8n execution ID, attempts, timestamps, processed/skipped/failed counts, actual outcome/error |
| notification_drafts | Internal intake/digest or external-preview content, intended vs actual sink recipient, exact content/context hash, lead/owner, status/version |
| notification_approvals | One explicit sink-only approval per contact preview, approver/time and exact approved hash; retained after cancellation |
| notification_deliveries | One ledger per draft, unique stable Message-ID, bounded attempts, retry eligibility, SMTP acceptance, separate Mailpit capture ID, visible error/uncertainty |
| reminder_items | Per-lead reservation inside an owner digest, original due/contact/owner snapshot, pending/sent/cancelled state and sent timestamp for rolling cooldown |

`created_by=n8n-intake` distinguishes workflow-created enquiries from local manual entries. Actual SMTP recipients are reserved `.test` mailboxes; `.example` intended contacts are reference metadata only. SQLite originals/backups remain preserved; PostgreSQL is the canonical application store after verified migration.
# Phase 4 reporting data

`v_analytics_leads` has one current lead per row plus owner name/active status and an open-stage flag. Snapshot parameters, not database server time, determine evaluation. `analytics/exports/LeadFacts_SYNTHETIC.csv` contains lead ID, synthetic origin, creation/source/campaign/stage/owner, INR estimated value, open/contacted/qualified/won flags, scheduled/overdue flags, first-response hours, per-lead elapsed SLA, mutually exclusive SLA flags, overdue estimated pipeline exposure, explained-rule priority score, pre-cooldown recovery eligibility and seed/controlled-fixture classification. Contact names, email addresses, phone numbers and message content are omitted.

`snapshot.json` stores the frozen KPIs, independent SQL values, source/owner/stage groups, all-time local automation evidence, comparison assumptions/events/results and Desktop DAX verification. It is not an event-sourced historical reconstruction. `manifest.json` hashes exported artifacts. Excel sheets mirror the exported tables and include ReadMe definitions/provenance, Reconciliation, ExperimentEvents and ExperimentRules.

The comparison's `overdue_remaining` field means modeled incomplete due work after assumed contacts; it is not the stored next-action overdue KPI. `ExperimentRules.raw_overdue_kpi` stays 40 in both arms until due dates are rescheduled. Recorded job attempts and unique latest-state jobs are separate grains; deliberate test failures are retained. SMTP acceptance fields refer only to the local Mailpit sink.

