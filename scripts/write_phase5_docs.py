"""Produce review documentation; business numbers come from a verified generation."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.artifacts import verified_snapshot
from backend.app.narrative import case_study,cost_scenarios


def write(name,text):
    (ROOT/'docs'/name).write_text(text.strip()+'\n',encoding='utf-8')


if __name__=='__main__':
    _,s=verified_snapshot();n=s['kpis']['new_leads'];rev=s['data_revision']
    write('PHASE_5_CASE_STUDY.md',case_study(s))
    write('BUSINESS_CASE.md',f'''# Business case — LeadRevive

SYNTHETIC portfolio case. Snapshot `{s['snapshot_id']}`; data revision `{rev}`; evaluated {s['as_of_utc']}.

The decision is whether disciplined ownership, response review and reminder workflows merit a permissioned pilot. The project provides evidence about data quality, visibility and local control execution. It does not prove customer adoption, increased sales or recovered revenue.

## Decision and success criteria
Sales associates need an owned next action; managers need source/workload/SLA exceptions; analysts need reconcilable denominators. Pilot success would mean measured owner action coverage, fewer unassigned enquiries, reliable rescheduling after contact and demonstrable administrative effort reduction. None should be inferred from sending a reminder alone.

## Evidence available
The verified cohort contains {n:,} synthetic leads. Estimated overdue pipeline exposure is INR {s['kpis']['pipeline_exposure_inr']:,.0f}, which is an opportunity-value sum, not a loss or recovery. Four local workflows cover intake, recovery, approval-controlled outbox and status sync. Real integration evidence is separate from the 40-event modeled comparison.

## Assumptions and sensitivity
The scenario assumes 200 actions/month; INR 300/hour capacity value; 24 setup hours; four maintenance hours/month; 12-month amortization. One/two/three assumed minutes saved per action produce net capacity-equivalent values of INR -800 / 200 / 1,200 per month. These values are arithmetic scenarios, not observed savings or ROI. Capacity is not necessarily cash released. Hardware, electricity and licensing costs are unmeasured and must be estimated for an actual pilot. See report `Cost_Benefit_Assumptions.json` for the calculation inputs and outputs.

## Recommended pilot measurement
Use a fixed permissioned cohort and comparable observation windows; record assignment, first response, contact completion, next-action rescheduling, actual operator effort, ordinary failures and retries. Separate deliberate faults. Review operational feasibility before any investment or external sending decision. Maintain external live delivery disabled in this portfolio system.

## Scope and gate
Local single-user prototype; no production security, public deployment or external SMTP transport. Phase 6 clean-install verification and publication remain outside this approval. Final narratives require human review; only claims supported by retained evidence belong on the resume.
''')
    write('RESUME_CLAIMS.md',f'''# ATS-ready resume candidates — select and defend

Project: **LeadRevive — Revenue Operations and Lead Recovery Intelligence** | SQL, Excel, Power BI, Python, n8n, FastAPI. Synthetic portfolio project, {n:,} records at snapshot `{s['snapshot_id']}`. These are role-specific alternatives, not four separate projects or an employment claim.

## Business Analyst
- Defined a lead-operations analysis model spanning funnel stages, response SLAs, owner workload and overdue pipeline exposure; reconciled 13 KPIs across PostgreSQL, application calculations, Excel exports and Power BI DAX.
- Documented requirements, exception handling, metric definitions and UAT scenarios for a synthetic B2B lead-management case.

## GTM / Revenue Operations
- Analyzed source-level lead outcomes and owner workload across {n:,} synthetic records to identify follow-up exposure and prioritize operational review.
- Built an SQL-backed recovery workflow with n8n owner digests, status synchronization and approval-controlled local email previews; validated retry and duplicate-send safeguards.

## Operations
- Implemented validation, conservative duplicate/conflict handling, audit history and reminder controls for a local synthetic operations workflow.
- Created reusable SQL/Excel reporting and snapshot-consistent management reports, distinguishing completed actions from unresolved next-action schedules.

## Solution Consulting
- Developed a local end-to-end demonstration connecting React/FastAPI, PostgreSQL, n8n, Mailpit and Power BI, with clear approval boundaries and evidence-backed management reporting.
- Prepared a management briefing with an assumption-based 40-event process comparison and cost sensitivity analysis, separating modeled outcomes from local test evidence.

## Attribution and permitted claims
Use a bullet only if you can explain and demonstrate its underlying artifact. This implementation was AI-assisted through Codex; do not claim it was independently handwritten or delivered for a real client. The owner set scope/constraints and approved stack, phases and reviews; the agent assisted implementation, tests and documentation. Review wording against your own actual work and understanding before using it.

Never claim production deployment, customer adoption, external email delivery, actual revenue recovery, human time saved or measured conversion uplift. Mailpit establishes local sink acceptance only. Historical test counts must carry their phase/date; do not present them as a newly executed suite.
''')
    write('INTERVIEW_NOTES.md',f'''# Interview explanation and contribution notes

## A two-minute explanation
LeadRevive is a synthetic revenue-operations portfolio case. Enquiries can become unowned or overdue without being lost sales. The system validates records, prioritizes work, orchestrates local reminders and gives managers a reconciled view of source, owner and SLA exposure. PostgreSQL is canonical; reports pin immutable exports. Estimated exposure is not recovered revenue.

## Tools and decisions
Python handles deterministic business rules; SQLAlchemy/Alembic support portability and migrations. PostgreSQL supplies independent KPI queries and transactional reminder protection. FastAPI/React provide working operations and report controls. n8n orchestrates four workflows; Mailpit tests actual local SMTP without external delivery. Excel organizes analysis; Power BI calculates DAX over frozen facts. python-docx/python-pptx produce editable outputs; ReportLab supplies a portable PDF without requiring Office on the server.

## Decisions to defend
- Exact identity matches preserve existing history; contradictory identities go to manual review.
- Rule-based priority is transparent; synthetic labels do not justify a purchase-prediction model.
- First-response SLA is elapsed hours. Median excludes uncontacted leads, shown separately.
- Current stages/cohort rates do not reconstruct historical conversion.
- Immutable generations plus atomic pointers prevent partial refreshes; report/download requests pin an ID.
- SQL and Python independently validate domain metrics. React/CSV/Excel consume results, while DAX aggregates derived facts; do not call all surfaces independent domain implementations.
- Approval is exact-content/version sink-only. Stable Message-ID and ledger/lookup/cooldown protect retries, but no universal distributed exactly-once guarantee is claimed.

## Assumptions and evidence
The 40-event comparison assumes two manual reviews/day versus hourly scans and an identical two-hour owner response. Its contacts are scheduled assumptions; real application rules execute them. No SMTP receipt causes those contacts. The result illustrates review cadence rather than observed conversion uplift. Completing a contact does not change an overdue next-action date. Cost scenarios use assumptions, not vendor quotes, actual savings or ROI.

## Personal contribution — do not invent
Confirmed owner contribution: defined the business-focused objective, chose/approved the stack and safety constraints, reviewed interfaces and phase evidence, and requested audit remediation. Engineering and documentation were AI-assisted by Codex. Prepare to demonstrate and explain the actual code, SQL, workflows and reports; identify any portions you personally changed or analyzed separately. Do not claim client work, independent coding or business results absent evidence.

## What to demonstrate
Show a recovery queue, read a score breakdown, inspect a conflict, explain approval/failure handling, open a Power BI source slicer, reconcile one KPI and generate normal/empty reports. Explain why an empty median is N/A rather than zero, and why a historical screenshot is omitted from a different cohort.

Reference snapshot: `{s['snapshot_id']}`; data revision `{rev}`. Source/owner findings and all report numbers must be read from that generation, not memorized as timeless business facts.
''')
    write('DEMO_SCRIPT.md', '''# Demonstration — 2–4 minutes

All records are synthetic. External live delivery disabled. Keep the demo local; this script does not authorize real email or publishing.

1. **0:00–0:35 — Business problem.** Open Overview/Recovery Queue. Explain ownership, overdue next actions and estimated exposure. Filter by an owner/source and open a real lead; show priority factors and timeline. Avoid editing canonical demo records merely for the presentation.
2. **0:35–1:10 — Operational controls.** Open Data Quality, then Automations. Show visible conflicts, four workflow exports, recorded jobs and exact-content sink approval. Explain actual SMTP failure/retry evidence and local Mailpit acceptance; do not trigger a new send.
3. **1:10–2:00 — Analytics.** Open the matching Power BI report. Show source slicer and workload/SLA pages. Explain contacted-only median, unresolved cohort denominators and why exposure is not recovered revenue. Show row-by-row DAX reconciliation and the data revision.
4. **2:00–2:40 — Reports.** Open Reports. Generate from the validated snapshot, download PDF/Word/PowerPoint and inspect metadata. Optionally choose a future creation window for an empty cohort: zero counts, N/A rates/median, no mismatched screenshots. This reads data but does not change lead records or the main Analytics snapshot.
5. **2:40–3:30 — Controlled comparison.** Explain identical 40 due events, assumed response timing and modeled contacts. Raw overdue stays unchanged until rescheduling. Cost sensitivity is an assumption exercise, not ROI.
6. **3:30–4:00 — Limitations and gate.** Local single-user scope, synthetic data, AI-assisted implementation, no customer adoption, external delivery or revenue recovery claim. Phase 6 and publication are not part of this demonstration approval.
''')
    write('UAT_PHASE_5.md', '''# Phase 5 UAT checklist

| Scenario | Expected behavior | Verification source |
|---|---|---|
| Normal report | DOCX/PDF/10-slide PPTX and case study contain the pinned generation's KPIs | reporting tests; live browser checks |
| Empty creation cohort | Zero counts; null rates/median displayed N/A; valid files; no stale screenshot | PostgreSQL fresh-cohort test and browser test |
| Fresh nonempty cohort | Report matches all 13 independently calculated SQL KPIs; main pointer retained | Live Reports browser verification |
| Invalid dates/generation | Visible error; no current-pointer replacement or successful report metadata | API regression |
| Failed renderer | No published partial report/history item | injected-failure regression |
| Interrupted export | Previous generation remains readable; no mixed files | publication regression |
| Pinned old generation | Downloads remain tied to their original data after a newer publish | publication/API checks |
| Corrupt artifact | Integrity validation rejects it | tampering regression |
| Null vs zero | Distinct during SQL/export/DAX verification | null regression and Desktop verifier |
| Power BI | Workflow/simulation/reconciliation pages open; actual DAX matches data/model revision | Desktop verification/captures |
| Local safety | Lead hashes unchanged; workflows preserved; external delivery disabled | final preservation check |
| Responsive Reports page | Generate/download/error/history usable on desktop and mobile | Playwright browser verification |

Execution results and exact counts are recorded in PHASE_5_REPORT.md; this checklist is not itself a blanket pass claim.
''')
    write('STARTUP_PHASE_5.md', r'''# Phase 5 startup and reporting

Docker Desktop must be running. All data is synthetic; external live delivery disabled.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/start_phase3.ps1
```

Open http://127.0.0.1:8000 and choose Reports. Generate from the validated Analytics snapshot or a fresh PostgreSQL creation window. Fresh cohorts read current record states and do not replace the main Analytics pointer. Download the Word, PDF, PowerPoint, case study, assumptions and metadata. No SMTP or workflow execution is triggered by report generation.

Reports persist under `reports/generated/<report_id>`; generated files are ignored by Git. Do not delete Docker volumes. Analytics generations persist under `analytics/exports/generations`; earlier Phase 4 root exports/PBIX remain preserved. Rebuild a snapshot intentionally with `scripts/build_phase4.py`, not by resetting/seeding the canonical database.

Power BI Phase 5 sources are under `analytics/powerbi/phase5`. They import one immutable generation path. To change the analyzed generation: publish exports, run `scripts/build_powerbi.py`, open that PBIP, Refresh, verify with `scripts/verify_powerbi.ps1`, then run `scripts/build_phase4.py --apply-powerbi-verification`. Proof publication changes the export generation but preserves the data/model revision. Save a PBIX through Desktop. The previous PBIX stays available; do not claim it refreshed automatically.

Screenshots are used only when their recorded data revision and hashes match. `reports/templates/evidence_images.json` records this binding. A filtered report may omit historical screenshots while retaining all computed figures. The portable PDF comes from the same structured content as the editable report; it is not claimed as a pixel-identical Word conversion. Desktop Office previews, when provided, are separately identified.

Run focused checks with `python -m unittest backend.tests.test_publications backend.tests.test_reporting backend.tests.test_analytics -v`; PostgreSQL variants use `LEADREVIVE_TEST_POSTGRES_URL` through the existing helper. Browser verification is under `frontend/scripts/test_phase5_browser.mjs`. See PHASE_5_REPORT.md for observed results and limitations. Stop before Phase 6/publication.
''')
    print('Generated Phase 5 case study, business case, role-specific resume, interview, demo, UAT and setup documents.')
