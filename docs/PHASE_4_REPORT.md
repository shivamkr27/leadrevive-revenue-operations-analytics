# LeadRevive — Phase 4 analytics review

SYNTHETIC portfolio case · Snapshot `9a80207b950500a9` · Evaluated 2026-10-24T15:44:29.684236Z (UTC).

The project identifies missed lead-handling work and makes it reviewable. It is a local synthetic business-operations case, not a client deployment. The canonical database contains 758 records: 754 accepted generator records and four retained Phase 3 integration fixtures. The dashboard includes both; `LeadFacts.cohort_kind` distinguishes them. Do not treat fixture stage changes as sales results.

## Management findings

| Measure | Observed snapshot | Interpretation |
|---|---:|---|
| Lead cohort | 758 | Current stored state, all creation dates through evaluation time |
| First contacted | 574 / 758 (75.7%) | 184 uncontacted records remain outside the response-time median |
| Median first response | 59 elapsed hours | Among contacted leads only |
| Overdue follow-up | 411 / 586 (70.1%) | Open leads with a past scheduled next action |
| Estimated pipeline exposure | INR 104,279,000 | Sum of overdue open estimated values; neither lost nor recovered revenue |
| Ever qualified | 383 / 758 (50.5%) | Includes evidenced qualification before a later Lost stage |
| Current Won | 64 / 758 (8.4%) | Current cohort status, including controlled fixtures; open leads unresolved |

Referral has the largest overdue count (94) and estimated exposure (INR 23,704,000) in this snapshot. A manager should review its due dates and capacity before interpreting this as poor source quality. Different acquisition dates, current stages and unresolved leads limit conversion comparisons.

Fictional Rep 2 and Fictional Rep 4 each hold 101 overdue records. There are 24 unassigned overdue records with INR 6,390,000 estimated exposure. Resolve ownership before relying on owner reminders to surface that work. Compare the owner table's rule-eligible count with raw overdue; cooldown and existing reservations apply only when the workflow runs.

The elapsed-hour SLA partition is 119 met, 637 breached and two awaiting response within SLA. The median alone hides the 184 uncontacted records. Review uncontacted breaches alongside timing, rather than presenting the contacted-only median as the whole cohort's experience.

## What was implemented

An Alembic 0005 view preserves lead-level grain and joins owner metadata. PostgreSQL computes cohort KPIs independently of Python, including JSON qualification history and a continuous median. One repeatable-read extraction produces aggregate reporting and contact-free lead facts, CSVs, a formatted Excel workbook, the React Analytics page and an eight-page Power BI model/report. All 13 KPIs reconcile with refreshed Desktop DAX measures; the reconciliation CSV records the actual values and snapshot identifier.

Power BI pages cover stages/cohort outcomes, overdue exposure, source comparison, owner workload, response SLA, workflow evidence, modeled comparison and KPI reconciliation. Stage distribution is not labelled a sequential conversion funnel. Estimated monetary exposure never receives a recovery or savings label.

## Controlled comparison

The same seed-42 cohort of 40 due events was evaluated under manual reviews at hours 12 and 24 and hourly automation scans. Both arms assume a two-hour owner response after surfacing. This timing assumption drives the outcome; it is not a measured human response improvement.

| Scenario | Modeled contacts executed by hour 24 | Incomplete due work | Raw overdue KPI | Measured local rule runtime |
|---|---:|---:|---:|---:|
| Manual reviews | 20 | 20 | 40 | 41.234 ms |
| Hourly scans | 34 | 6 | 40 | 495.258 ms |

Real application contact/recovery rules executed in disposable SQLite databases. The automation arm reserved 40 reminders and passed 24 repeated-hour idempotency checks. No n8n or SMTP call occurs in this simulation; Phase 3 separately proves real integration execution. Processing duration measures local rule computation, not human time saved. Raw overdue remains 40 because completing a contact does not reschedule its next action. Automatic surfacing cannot substitute for owner action or correct scheduling.

## Reconciliation and refresh

The snapshot is frozen; operational Overview/Queue pages use the current clock and current data. A later due date crossing or lead edit can change their values. The Analytics page, exported files and Power BI reconcile only when they share the same snapshot. No historic stage/owner reconstruction is claimed. See `analytics/sql/README.md`, `analytics/exports/Reconciliation_SYNTHETIC.csv` and `analytics/powerbi/README.md`.

## Recommended next actions

1. Assign the 24 unassigned overdue records, then review missing next-action dates.
2. Review Referral overdue work and Rep 2/Rep 4 capacity before changing source spend.
3. Require a new next-action date after contact completion so the stored queue reflects the next task.
4. In a future permissioned pilot, measure owner response and action completion before estimating time savings or revenue impact. Keep external live delivery disabled until separately approved.

## Limits and review gate

Synthetic values and controlled fixtures cannot establish customer adoption, production reliability, real conversion uplift, recovered revenue or ROI. Failure totals include deliberate test faults. The editable PBIX is local and uses CSVs extracted from PostgreSQL; no Fabric publishing, paid account or public database is required. Refresh after moving the workspace requires updating the Power Query file paths.

Phase 4 review artifacts are complete only with the recorded test and Power BI evidence. Phase 5 final document/PDF/PPTX packaging and Phase 6 portfolio publication remain gated on user approval. The presentation supplied here is content for review, not a claimed final executive deck.
