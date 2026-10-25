# Metrics and priority rules

All current values describe SYNTHETIC input. Phase 1 export evaluation: 2026-10-24 00:00 UTC (05:30 Asia/Kolkata). The app uses the live UTC clock by default, with an explicitly labeled optional fixed demo clock at 12:00 UTC (17:30 IST) for browser evidence. Creation cohort uses inclusive start/exclusive end, with creation no later than evaluation clock. State reflects current persisted state, not reconstructed historical state; do not use past as-of dates to claim historical pipeline movement.

| Metric | Numerator / denominator / exclusions |
|---|---|
| New leads | Distinct accepted leads created in selected cohort; rejected/duplicate input excluded |
| First-response coverage | Contacted by evaluation clock / cohort count; report uncontacted separately |
| Median first response | Median hours creation → initial contact among contacted cohort only; fixture has one initial contact |
| Overdue rate | Open scheduled leads with next action strictly before evaluation / all open scheduled cohort leads; missing schedule excluded and not inferred |
| Qualified rate | Unique cohort leads evidenced Qualified or later / cohort; initially imported Meeting/Proposal/Won count as qualified, Lost alone does not |
| Win rate | Current Won / cohort; still-open leads remain denominator |
| Pipeline exposure | Estimated INR sum over overdue open cohort; includes unassigned; opportunity exposure, not lost revenue |
| Source funnel | Current counts by source/stage in SQL view; not historical transition conversion |
| Recovery action rate | Completed contacts / identical fixed 40-event eligible cohort in Phase 4 controlled simulation; 20/40 manual versus 34/40 hourly-scan arm, conditional on the documented response assumptions; not won deals |
| Workflow reliability | Successful attempted runs / attempted runs would require complete attempt-level observation. Current outputs report unique job latest states and attempt totals separately; no production reliability rate is claimed |

Zero denominators return null (not a fabricated zero rate). Currency stored in integer paise, displayed INR. KPI calculation reads SQL-persisted cohort facts/history and aggregates in Python; independent SQL inspection reconciles exposure and source totals. Full cohort median uses Python statistics. `v_open_pipeline` excludes Won/Lost. `v_source_funnel` is all-current-stage segmentation. SQL inspection is in analytics/sql/inspection.sql. Bind canonical six-fractional-digit UTC `as_of` values when running text-based timestamp queries.

Score is deterministic task priority, never purchase probability. Overdue weight 35 scales elapsed overdue hours / 168, clamped 0–1; value weight 25 uses midrank percentile among open leads; stage weight 20 uses New=.1, Contacted=.25, Qualified=.5, Meeting=.75, Proposal=1; verified unsuppressed contactability weight 10; recency weight 10 decreases linearly from last contact over 30 days. No verified synthetic contacts; contactability component is zero. Missing schedule/contact gives zero factor and explicit missing label. Weights must be finite, nonnegative and total 100. Breakdown is exported. Closed leads excluded before queue scoring.

Phase 3 recovery eligibility requires open stage, active assigned owner, overdue due date, no suppression, no completed contact at/after that due date, no pending reservation and no sent reminder within the rolling 24-hour cooldown. Cooldown uses actual sent time; cancelled reservations do not count as sent. This candidate set can be smaller than the overdue KPI, which continues to reflect the stored next-action schedule. Recording a completed contact does not silently replace the next-action schedule. Response SLA is elapsed hours, not business-hours adjusted.

The Automations view shows actual recent backend jobs/attempts, not a claimed complete workflow reliability KPI. n8n-side failures before reaching an unavailable backend remain in n8n's execution history. Phase 4 reports all-time local ledger counts at extraction, including deliberately induced faults, and does not present them as normal production operations.

Phase 4 adds PostgreSQL `v_analytics_leads` and `analytics/sql/kpi_snapshot.sql`. The latter independently calculates all 13 application KPI values (including JSON qualification history and PostgreSQL percentile_cont median). Repeatable-read extraction freezes the cohort, evaluation timestamp and record state. The React Analytics page and CSV/Excel exports expose this frozen snapshot; Power BI imports its fact rows and computes DAX measures independently. Verify the snapshot identifier and clear filters before reconciling. Operational Overview/Queue use the current clock and can differ after edits or deadlines cross.

The response-SLA partition is contacted within SLA + late-contacted/uncontacted breached + uncontacted within SLA = cohort. Exact SLA deadline is within SLA. Rule-eligible recovery facts exclude completed/closed/suppressed/unassigned/inactive-owner work; cooldown and pending reservations are additional run-time controls. Distinct reminder leads and reminder items are recorded reservations, not proof of contact completion. SMTP accepted by local sink and verified local Mailpit capture are separate from external delivery; external live delivery disabled.

The Phase 4 event comparison assumes manual reviews at hours 12 and 24, hourly scans, and the same two-hour owner response. Contacts and reminder reservations execute through application rules in disposable databases. Local computation time is measured; review/response timing is modeled. Raw overdue remains 40 in both arms until due dates are rescheduled, even when 20/34 contacts complete. No human time savings, real conversion uplift or revenue impact is inferred.
