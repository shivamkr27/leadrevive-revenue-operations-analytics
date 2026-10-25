# Business case — LeadRevive

SYNTHETIC portfolio case. Snapshot `9a80207b950500a9`; data revision `d0b3c24632131978efcdfa1d8cb57f1d46347e76d109e3a596ef0f8c8084c401`; evaluated 2026-10-24T15:44:29.684236Z.

The decision is whether disciplined ownership, response review and reminder workflows merit a permissioned pilot. The project provides evidence about data quality, visibility and local control execution. It does not prove customer adoption, increased sales or recovered revenue.

## Decision and success criteria
Sales associates need an owned next action; managers need source/workload/SLA exceptions; analysts need reconcilable denominators. Pilot success would mean measured owner action coverage, fewer unassigned enquiries, reliable rescheduling after contact and demonstrable administrative effort reduction. None should be inferred from sending a reminder alone.

## Evidence available
The verified cohort contains 758 synthetic leads. Estimated overdue pipeline exposure is INR 104,279,000, which is an opportunity-value sum, not a loss or recovery. Four local workflows cover intake, recovery, approval-controlled outbox and status sync. Real integration evidence is separate from the 40-event modeled comparison.

## Assumptions and sensitivity
The scenario assumes 200 actions/month; INR 300/hour capacity value; 24 setup hours; four maintenance hours/month; 12-month amortization. One/two/three assumed minutes saved per action produce net capacity-equivalent values of INR -800 / 200 / 1,200 per month. These values are arithmetic scenarios, not observed savings or ROI. Capacity is not necessarily cash released. Hardware, electricity and licensing costs are unmeasured and must be estimated for an actual pilot. See report `Cost_Benefit_Assumptions.json` for the calculation inputs and outputs.

## Recommended pilot measurement
Use a fixed permissioned cohort and comparable observation windows; record assignment, first response, contact completion, next-action rescheduling, actual operator effort, ordinary failures and retries. Separate deliberate faults. Review operational feasibility before any investment or external sending decision. Maintain external live delivery disabled in this portfolio system.

## Scope and gate
Local single-user prototype; no production security, public deployment or external SMTP transport. Phase 6 clean-install verification and publication remain outside this approval. Final narratives require human review; only claims supported by retained evidence belong on the resume.
