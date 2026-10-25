# LeadRevive — Business operations case study

SYNTHETIC portfolio case | Snapshot 9a80207b950500a9 | Data revision d0b3c24632131978efcdfa1d8cb57f1d46347e76d109e3a596ef0f8c8084c401 | Generation f03b072d3f984a95a83a34ccb865a534
Evaluation: 2026-10-24T15:44:29.684236Z; creation window [1900-01-01T00:00:00.000000Z, 2100-01-01T00:00:00.000000Z). Current-state reporting; no historical reconstruction.

## Problem and decision
A B2B services team needs to see unowned enquiries, late first responses and missed next actions. The system helps a manager assign work and prioritize follow-up; it does not establish that overdue leads are lost sales.

## Method and cohort
PostgreSQL is canonical. Independent SQL and Python calculations reconcile before publication; CSV/Excel are read back. Power BI aggregates the derived facts. Cohort: 758 leads (754 seed records; 4 controlled fixtures).

| Measure | Snapshot value |
|---|---:|
| Leads in cohort | 758 |
| First contacted | 574 |
| Uncontacted | 184 |
| Current Won | 64 |
| Ever qualified | 383 |
| Open with scheduled action | 586 |
| Overdue follow-up | 411 |
| First-response coverage | 75.7% |
| Lead-to-qualified rate | 50.5% |
| Lead-to-win rate | 8.4% |
| Overdue / scheduled open | 70.1% |
| Median first response (hours) | 59 |
| Estimated pipeline exposure (INR) | 104,279,000 |

## Findings and recommended actions
- Referral has the largest overdue count in this cohort: 94, with INR 23,704,000 estimated exposure. Review cohort age and capacity before changing source spend.
- 24 overdue leads are unassigned, representing INR 6,390,000 estimated exposure. Owner reminders cannot resolve missing ownership.
- Elapsed-hour SLA: 119 met, 637 breached and 2 awaiting within SLA. The response median excludes 184 uncontacted leads.

## Automation and evidence
Four workflows cover intake, recovery, approval-controlled outbox and status sync. Internal owner reminders are automated; customer-preview approval is manual and bound to exact content/version. External live delivery disabled.
All-time local test ledger (not the selected lead cohort; includes deliberate fault tests):
- distinct reminded leads: 386
- sink only approvals: 6
- smtp accepted by local sink: 13
- accepted after retry: 1
- failed or uncertain send events: 4

## Controlled comparison
Manual reviews at hours 12 and 24; hourly automation scan; identical assumed two-hour owner response. No sales or revenue outcome modeled.
Owner actions are predetermined scenario assumptions. Application contact/recovery rules execute locally; n8n/SMTP receipt does not cause the simulated contacts.
- manual: 20/40 modeled contacts (50%); 20 incomplete due tasks.
- automation: 34/40 modeled contacts (85%); 6 incomplete due tasks.
Raw overdue remains unchanged without next-action rescheduling. Local rule runtime is measured computation, not human time saved.

## Limits and next measurement
Estimated pipeline exposure is neither recovered nor lost revenue. Current Won includes synthetic fixtures. Source comparisons are descriptive, not causal. Job counts include induced faults and retries; no production reliability or distributed exactly-once claim is made.
A permissioned pilot should measure owner action and rescheduling rates, actual administrative effort, and recurring operating costs before making efficiency or financial claims. Local single-user scope only.

## Cost / benefit scenario
Illustrative assumptions, not observed savings, cash flow, vendor prices or ROI. Hardware, electricity and licensing costs are not measured; capacity value is not revenue.
Assume 200 actions/month, INR 300/hour capacity value, 24 setup hours, 4 maintenance hours/month, amortized over 12 months. These are editable scenario inputs, not measurements.
| Assumed minutes saved/action | Capacity hours/month | Net capacity-equivalent INR/month |
|---:|---:|---:|
| 1 | 3.33 | -800 |
| 2 | 6.67 | 200 |
| 3 | 10.0 | 1,200 |

## Evidence boundaries
Historical Phase 3 evidence: 19 real integration checks. Phase 4 final regression: 51 PostgreSQL tests and 49 SQLite passes/two skips. These historical counts are not newly executed Phase 5 tests. Current report metadata records exact export and screenshot hashes.
