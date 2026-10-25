# LeadRevive — pre-Phase 5 audit

**Date:** 24 October 2026. **Scope:** Phases 0–4; local synthetic portfolio implementation.

**Verdict:** The delivered Phase 4 snapshot and core functionality have credible implementation and execution evidence. No Critical finding was identified within the intended local-demo scope. Important reporting/verification gaps remain below; address them before claiming robust, reusable report generation. This audit does not approve or start Phase 5.

**Method:** Read-only inspection of source, migrations, tests, reports and saved execution evidence. Rechecked the 16 export-manifest hashes, CSV/Excel/saved SQL/DAX values, cohort composition and PBIX ZIP contents without refreshing data, invoking workflows, reopening Desktop or rerunning expensive tests. Only this report was created. Live service availability and today's database state were not re-certified.

## 1. Architecture and implemented functionality

FastAPI + React provide persistent lead creation/editing, filtering/sorting, owner/stage/schedule changes, contact notes, timelines/audit history, CSV import/export, duplicate/conflict review, settings, automation controls and analytics. SQLAlchemy and Alembic manage the canonical PostgreSQL database; migrations 0001–0005 exist. SQLite remains the preserved bootstrap/regression path. Docker Compose runs PostgreSQL, n8n, Mailpit and the application with loopback-bound ports. n8n metadata uses its own persisted storage, separate from business records.

Phase 0 requirements, architecture and reference/licensing notes exist. Priority is an explained rule-based score, not a purchase prediction. SLA uses elapsed hours. Reporting currently serves explicitly refreshed files; a complete on-demand PDF/PPTX reporting interface is not implemented yet.

## 2. Database integrity and count progression

The generator produced **800 raw rows → 754 accepted leads + 32 invalid rows + 7 exact duplicates + 7 identity conflicts**. Duplicates preserve existing records; conflicting identities require review rather than silent merging.

Two Phase 3 integration executions, including an intermediate failed test run, retained two clearly synthetic leads each: **754 + 4 = 758**. This is fixture growth, not customer acquisition. Snapshot facts independently show 754 seed records and four controlled fixtures. Replaying an identical intake does not create another lead.

Saved migration/pack evidence verifies original records by primary key and hashes across ten source tables, including all 754 leads and their original audit/activity/history rows. PostgreSQL migration and Alembic drift checks passed previously. This audit reused that evidence rather than rerunning migration or preservation queries.

## 3. All 13 KPIs and reconciliation

Snapshot **`9a80207b950500a9`**, evaluated **2026-10-24T15:44:29.684236Z**. Creation window is inclusive start/exclusive end, capped at evaluation time. These are current stored states, not historical stage/owner reconstruction. Open means neither Won nor Lost.

| KPI | Definition | Snapshot value |
|---|---|---:|
| `new_leads` | Distinct accepted leads in creation cohort | 758 |
| `contacted` | Cohort leads with first contact by evaluation time | 574 |
| `uncontacted` | Cohort minus contacted | 184 |
| `won` | Cohort leads currently Won | 64 |
| `qualified` | Current Qualified/Meeting/Proposal/Won, or corresponding history evidenced by evaluation time | 383 |
| `active_scheduled` | Open cohort leads with a next-action date | 586 |
| `overdue` | Scheduled open leads with next action strictly before evaluation time | 411 |
| `first_response_coverage` | Contacted / cohort | 75.7256% |
| `qualified_rate` | Ever-qualified / cohort | 50.5277% |
| `win_rate` | Current Won / cohort, including unresolved open leads in denominator | 8.4433% |
| `overdue_rate` | Overdue / scheduled open leads; missing schedules excluded | 70.1365% |
| `median_first_response_hours` | Median creation-to-first-contact elapsed hours, contacted leads only | 59 hours |
| `pipeline_exposure_inr` | Sum of overdue open estimated values, including unassigned leads; paise converted once to INR | INR 104,279,000 |

Existing Python/PostgreSQL comparison, CSV/Excel readback and actual Desktop DAX evidence agree within **1e-8**. This audit found no value or manifest-hash mismatches. Zero-denominator rates are intended to be null.

**Evidence boundary:** React Analytics consumes the frozen snapshot; CSV/Excel store its results. Power BI aggregates derived lead facts through DAX. These are not four independent implementations of domain rules. The principal independent domain calculation is PostgreSQL versus application Python. Live Overview/Queue can differ after edits or deadlines cross; equality is established for the matched snapshot, not indefinitely across live screens.

## 4. n8n, approvals and send safeguards

| Workflow | Implemented behavior |
|---|---|
| Intake | Authenticated webhook, validation, identity checks, idempotency, active-owner assignment and internal draft |
| Recovery | Hourly scan, eligibility/cooldown/reservation checks, grouped owner reminders and local sink dispatch |
| Outbox/approval | Five-minute processing, explicit exact-content/version sink-only preview approval, failure visibility and bounded retry |
| Status sync | Version-checked updates and stale-reminder cancellation |

Saved state lists four active business workflows and an inactive schedule probe. `SS05_n8n_Workflow.png` depicts recovery only. Nineteen real integration checks cover authenticated n8n, PostgreSQL, actual Mailpit SMTP 451 failure, retry and duplicate-capture prevention. A real short-interval schedule probe was executed; it does not prove an uninterrupted hour-long run.

Safeguards include PostgreSQL advisory locking, durable idempotency keys, unique delivery records, stable Message-ID, Mailpit lookup, cooldown, stale-approval rejection and a three-attempt cap. Uncertain acknowledgement without a matching sink record blocks blind resend. Internal owner notices do not require customer-preview approval. External-preview approval authorizes only the local test sink.

**External live delivery disabled.** Transport code permits only local Mailpit and reserved `.test` sink recipients. Correct outcome wording is **“SMTP accepted by local sink”**, not external email delivery. Tested duplicate protection is not a production exactly-once guarantee under every crash, retention or service-loss scenario.

## 5. Power BI and Excel

`analytics/powerbi/LeadRevive_Phase4_SYNTHETIC.pbix` is present with a valid ZIP container, imported DataModel and eight page definitions. Editable PBIP/model/report sources and DAX definitions also exist. Saved evidence records Desktop open/refresh/save/reopen, 13-KPI DAX reconciliation and a working source slicer: Event **152**, cleared **758**. This audit inspected the file without reopening Desktop.

Pages cover funnel/stage distribution, overdue exposure, source performance, owner workload, response SLA, workflow evidence, modeled comparison and reconciliation. Stage distribution is correctly distinguished from sequential conversion.

The Excel workbook has **13 sheets**, including facts, KPIs, source/owner/stage analysis, quality, operations, reconciliation, comparison events/rule results and provenance. SQL queries and CSVs are reusable. Power BI uses PostgreSQL-derived local exports, not a direct live PostgreSQL connection; paths require adjustment after moving the workspace.

## 6. Controlled comparison: 20 versus 34

Seed 42 generates the same **40 due events** for both arms. Manual reviews occur at hours **12 and 24**; automation scans hourly. Both assume a **two-hour owner response** after surfacing, with completion assessed at hour 24.

| Result | Manual | Hourly scans |
|---|---:|---:|
| Modeled contacts executed | 20/40 (50%) | 34/40 (85%) |
| Incomplete due work | 20 | 6 |
| Raw stored overdue KPI | 40 | 40 |
| Measured local rule runtime | 41.234 ms | 495.258 ms |

Real application rules execute in disposable SQLite databases; the automation arm reserves 40 reminders and checks 24 repeated-hour replays. Contacts follow predetermined scenario times, rather than being caused by actual notification receipt. No n8n/SMTP execution occurs in this comparison. The **35-percentage-point difference is assumption-driven**, not observed sales uplift. Raw overdue stays unchanged because contact completion does not reschedule next action. Runtime is computation, not human time saved.

## 7. Business-impact and resume claims

Snapshot evidence supports **386 distinct leads with reminder items, 15 drafts, six sink-only approvals, 13 local SMTP acceptances with verified captures, one acceptance after retry and four failed/uncertain-send audit events**. These include deliberate local test faults. Seven duplicate rows and seven conflicts were held without inflating accepted seed leads.

Existing resume candidates accurately describe a synthetic SQL/Excel/Power BI/n8n portfolio project. Retain the fixture explanation and snapshot date. Do not describe reminder reservations as completed recovery, INR 104.279 million exposure as recovered revenue, 48/56 latest successful jobs as production reliability, or Mailpit acceptance as external delivery. Customer adoption, real ROI, conversion uplift and human savings remain unproven.

## 8. Findings, limitations and risks

**Critical:** None identified for the intended local, synthetic, externally-disabled demo.

| Severity | Finding | Required treatment before broader claims |
|---|---|---|
| **Important** | Empty-cohort export is not robust: `write_pack` indexes `LeadFacts[0]`; tests check empty calculations but do not export the empty cohort. Verification scripts also subtract possibly null metrics, while PowerShell double casts can conflate null with zero. | Add empty/null-aware export and verifier handling before claiming arbitrary-cohort reporting. Code-inspection finding; not reproduced through a mutating export during this audit. |
| **Important** | Export refresh writes CSV, workbook, snapshot and manifest sequentially. Concurrent readers or a failed refresh can observe a mixed generation. Old experiment verification JSON can remain after a refresh without engine verification. | Publish a complete validated generation atomically and make stale evidence explicit. The delivered pack currently passes hashes. |
| **Important** | `write_phase4_docs.py` hardcodes several source, owner, SLA, composition and resume statements despite reading a snapshot. | Derive findings from the selected cohort, or freeze and label documents; otherwise refreshed narratives can become false. Current published numbers match the audited snapshot. |
| **Important** | Export reconciliation rows initialize `difference=0/status=PASS`; actual assurance comes from separate comparisons/readback, not those labels alone. Snapshot ID excludes experiment content and model/code version. | Tie report status and full-generation identity to validation results; preserve the independent evidence. No mismatch was found in this snapshot. |
| **Important** | Simulation contacts are schedule-driven assumptions, and workflow counts include test faults/latest-state retries. | Keep scenario results separate from empirical automation impact and production reliability. Existing limitations mostly do this correctly. |
| **Important** | Application is a local single-user prototype, without production user authentication/role enforcement or a proven distributed exactly-once SMTP protocol. | Keep loopback deployment and disabled external transport; do not claim production readiness or authenticated approver identity. |
| **Polish** | Power BI/CSV field `overdue_remaining` means modeled incomplete due work, whereas raw overdue remains 40; historical phase notes retain earlier migration/status wording. | Harmonize labels and keep historical notes clearly dated. |
| **Polish** | Detailed evidence is ignored local runtime data; repository files are currently untracked. | Preserve sanitized evidence and pin a reviewed revision during planned portfolio packaging. No immutable release provenance is claimed yet. |

## 9. Evidence sufficiency and missing deliverables

Reused final logs show **51 PostgreSQL tests passed** and **49 SQLite tests passed with two PostgreSQL-only skips**. Existing evidence also records seven frontend regression tests and six analytics browser checks. Ten management/evidence SQL queries executed successfully. These suites were not rerun for this audit; they are recorded execution evidence, not proof every possible edge case is covered.

No missing core Phase 0–4 artifact prevents Phase 5 planning. The Important findings should be resolved or explicitly accepted before final reusable reporting claims. Remaining planned deliverables are the final editable PPTX and business report/PDF previews, on-demand report generation/download flow, assumptions-based business case/cost estimate, consolidated UAT/demo script, final resume claims and SS11/SS12 evidence. Clean-install verification, a versioned release and GitHub publication belong to Phase 6. Phase 4 presentation content and interview/resume drafts already exist; do not present them as finished Phase 5 packaging.

**Evidence index:** `docs/PHASE_1_INTEGRITY_REVIEW.md`, `docs/PHASE_2_REPORT.md`, `docs/PHASE_3_TEST_EVIDENCE.md`, `docs/PHASE_4_TEST_EVIDENCE.md`; local `data/processed/phase4_{postgres_tests_final.log,sqlite_tests_final.log,pack_verification.json,powerbi.json,powerbi_filter.json,browser.json}`; `analytics/exports/{snapshot.json,manifest.json,Reconciliation_SYNTHETIC.csv,experiment_engine_verification.json}`; `analytics/sql/`; `screenshots/README.md`. Relevant code: `backend/app/{foundation,operations,automation,analytics}.py`, `scripts/{build_phase4,run_phase4_experiment,write_phase4_docs,verify_phase4_pack}.py`, and `scripts/verify_powerbi.ps1`.

**Audit action:** Report only. No implementation fixes, data refresh, workflow execution, test-suite rerun or Phase 5 work performed.
