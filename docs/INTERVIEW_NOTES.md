# Interview explanation and contribution notes

## A 60–90-second explanation

“LeadRevive is a synthetic revenue-operations portfolio project about missed follow-ups. I framed the question around which leads need attention, who owns the next action, and how a manager can measure the exposure.

The reviewed dataset contains 758 synthetic records: 754 accepted seed leads and four retained integration fixtures. The application validates intake, flags duplicates and identity conflicts, and shows a transparent priority queue. PostgreSQL is the source of truth. Four real n8n workflows cover intake, overdue reminders, approval-controlled previews and status synchronization. Mailpit tests local SMTP; external sending is disabled.

For management reporting, 13 KPIs reconcile through SQL and Python, CSV/Excel readback and saved Power BI DAX evidence. Reports use one immutable snapshot. The 20-versus-34 contact comparison is modeled under stated review-cadence and owner-response assumptions; it is not sales uplift. Estimated pipeline exposure is not recovered revenue.

My confirmed contribution was business framing, stack and constraint decisions, phase reviews and audit feedback. Implementation and documentation were AI-assisted. I can demonstrate the workflow and explain its rules, assumptions and limitations.”

Approximately 190 words; rehearse at your normal pace and shorten if it exceeds 90 seconds. Replace personal-contribution language only with work you actually performed. Use the tool details below for follow-up questions.

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

Reference snapshot: `9a80207b950500a9`; data revision `d0b3c24632131978efcdfa1d8cb57f1d46347e76d109e3a596ef0f8c8084c401`. Source/owner findings and all report numbers must be read from that generation, not memorized as timeless business facts.
