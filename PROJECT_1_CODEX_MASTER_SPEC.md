# PROJECT 1 — CODEX MASTER IMPLEMENTATION SPECIFICATION
## LeadRevive: Revenue Leakage & Lead Recovery Intelligence
**Version:** 1.0 | **Target:** Resume-grade working business-operations project | **Language of implementation:** English | **Owner:** Student developer | **Executor:** VS Code Codex

> **INSTRUCTIONS TO CODEX — READ FIRST**
>
> You are the implementation agent for this project. Read this entire specification before touching code. It is the authoritative product and delivery specification, not a request to immediately generate the entire application. Work **phase by phase**, make real working deliverables, execute tests, and stop at explicit approval gates. Do not claim a feature is complete because code exists: verify functionality and show evidence. If you lack a required credential, permission, provider account, source dataset, or choice that materially changes behavior, **ask the user a precise question**, explain the default, and proceed with non-dependent work. Do not invent business impact, customer data, company affiliations, survey results, screenshots, credentials, sent messages, or test results. Keep code and documentation maintainable. Assume the user is on Windows with VS Code; detect their actual environment before selecting commands.
>
> **First task after receiving this file:** Inspect workspace, make a short gap/decision checklist, generate `docs/PHASE_PLAN.md`, propose Phase 0/1, and perform only Phase 0 plus approved Phase 1 setup. **Do not build everything in one uncontrolled pass.** At the end of each phase: provide files changed, tested commands/results, screenshot instructions where relevant, known limitations, and the next gate. Ask for approval before moving from a phase that has external side effects or major scope implications.

---

## 1. Purpose, problem, audience, and honest positioning

This is a **business analytics + revenue operations + workflow automation** portfolio project, **not** a generic CRUD CRM clone and not a full-stack SaaS startup. Imagine a small **India-based B2B service provider** (e.g., IT services / professional training / logistics services) receiving inbound enquiries from web forms, events, email, referrals and manual entry. Leads are lost due to late first response, duplicate entries, unassigned owners, missing next-action dates and inconsistent follow-ups. Management cannot tell which segment leaks leads, how much opportunity value is at risk, or what action to take next.

**Product goal:** Bring disconnected lead data into a reliable database; diagnose conversion and response problems; recommend prioritized actions; trigger approved, automated internal follow-ups and optional customer emails; enable management to see what happened, what needs action and what operationally improved **in a controlled test environment**.

**Primary users:** (1) Sales/BD associate who owns leads, (2) Sales manager who prioritizes and reviews performance, (3) analyst who validates metrics and recommends process changes.

**Business research question:** Which workflow failures contribute to lead leakage, which leads should be rescued first, and can automatic assignment/reminders reduce overdue follow-ups in a controlled scenario?

**Scope credibility:** Built with synthetic or openly licensed data by default; do not describe as a real paid client deployment. If a genuine business later grants permission to pilot, separate that pilot, obtain permission and record empirical results. Business-relevant value should be based on *tested* efficiency/coverage metrics, **not** invented revenue increases.

### Success definition
- A user can upload/ingest leads, clean duplicates, see validation exceptions and owners, and run the end-to-end process.
- At least 3 meaningful scenarios are reproducible (new lead, stale lead recovery, duplicate/invalid lead), plus successful/failed email delivery handling.
- A real n8n workflow runs locally or in an approved environment, and has exportable JSON.
- A real analytic model produces reproducible KPIs and a Power BI report using project data; dashboard PNGs alone are inadequate.
- An owner can review an email, explicitly approve it, and see send outcome or simulated outcome in audit logs. No mass outbound sending.
- There is a coherent business case, assumptions, cost-benefit estimate labeled as estimates, and a concise presentation suitable for a management audience.
- Test evidence and a 2–4 minute demonstration show the system *actually working*.

---

## 2. Reference materials: what to examine, reuse boundaries

### Reference A — Analytics and lead scoring
URL: https://github.com/Akannione/crm-sales-pipeline-automation-system
Purpose: Learn how a CRM analytics pipeline cleans lead data, scores opportunities, prioritizes follow-ups, and generates sales pipeline reports. Inspect the README, actual scripts, data model, SQL and sample outputs before deciding what is useful. **Do not blindly clone as final work**. Prefer implementing our own clear pipeline, tests, metrics and data dictionary. Check its current LICENSE; if unclear, do not copy code. Link to it in `docs/REFERENCES.md` as inspiration.

### Reference B — n8n lead-qualification pattern
URL: https://github.com/Bakaare/ai-lead-qualification-n8n
Purpose: Inspect webhook validation, duplicate checks, structured scoring, Google Sheets and notification flow. Repository advertises MIT license; verify LICENSE and include copyright/attribution if code is actually reused. Use for workflow concepts or a separately attributed fork, but author a custom end-to-end lead-recovery workflow for this project.

### Reference C — official n8n documentation
- https://docs.n8n.io/
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.sendemail/
- https://n8n.io/workflows/7065-automate-personalized-email-campaigns-with-google-docs-sheets-and-smtp/
Purpose: Reliable webhook, scheduling, credential handling, SMTP sending, retries, rate limits and workflow export.

### Reference D — Power BI Desktop
- https://www.microsoft.com/en-us/download/details.aspx?id=58494
Purpose: Build an editable `.pbix`, not just an image. If Power BI cannot run on current machine, deliver SQL views + structured CSVs and a ready-to-open Power BI build guide; **do not misrepresent a screenshot as a PBIX deliverable**.

**Hard rules:** Keep an origin/attribution manifest; observe project licenses and data use restrictions. Do not import proprietary customer records or unauthorized CRM data; do not scrape private leads. Do not reuse other projects' fabricated claims as our outcomes. Use official documentation for live integration changes.

---

## 3. Scope: MUST, SHOULD, and OUT OF SCOPE

### MUST — portfolio MVP
1. Reproducible seed dataset (>= 600 realistic synthetic leads with temporal variation, several campaigns, sales stages, owners, duplicate emails/phones, invalid records, late responses, lost reasons, and opt-in flags). Synthetic data generated with fixed seed; clear label `SYNTHETIC` across app/exports/docs.
2. Ingestion: CSV import, schema validation, normalization, deduplication and rejected-record report; manual lead entry or simple public-form simulation using local test mode.
3. Persistent SQL database, migrations, migrations tests; stable IDs, audit timestamps and lead history.
4. Lead states/owners, next-action dates, configurable response SLA, deterministic transparent prioritization (no unexplained AI scores).
5. End-to-end **n8n** workflow for event intake and scheduled follow-up reminders with logging, idempotency and failure path; downloadable JSON export.
6. Local working operations interface (simple React front end or Streamlit—**choose one at Phase 0** based on build speed and functional requirements). Core screens: Overview, Lead Queue, Lead Detail/Timeline, Exceptions/Automations, Analytics, Settings/Consent.
7. Analytics with documented KPI definitions and denominators; SQL or Python transformations; Power BI editable file when environment supports it.
8. Role-specific email templates: **internal owner notifications** and optional **consented external follow-up**; preview and explicit approval before any external email.
9. CSV/Excel lead export, PDF business-summary report, PDF or PPTX executive deck as on-demand generation. Reports built from live aggregate data and branded cleanly, not LLM hallucinations.
10. Tests + reproducible start/setup scripts + screenshots/demo checklist + clear limitations.

### SHOULD — after MVP passes
- Lead assignment rules (round-robin by active reps, respect manual assignment); stage-change event history.
- SLA breach forecasting: identify approaching deadlines with adjustable thresholds.
- Priority queue with interpretable factors: urgency, stage, recency, qualification, estimated value, contactability, prior attempts.
- Before/after controlled experiment using identical synthetic scenario datasets (manual baseline vs automated scenario); transparent calculations for follow-up coverage/time and no fabricated real-world ROI.
- Google Sheets connector optional: bi-directional sync is not mandatory; avoid duplicate writes and use one system of record (database).
- Optional LLM explanation of a lead's next action; disabled by default, constrained to supplied data, fallback to deterministic rules, and do not send PII to outside AI services without permission.

### OUT OF SCOPE for v1
- Full CRM replacement; commercial-grade multitenancy; spam campaigns; LinkedIn scraping; WhatsApp messaging without approved business API; paid SaaS billing; complex ML lead-prediction trained on fabricated labels; claims of real recovered revenue; automated external prospecting to strangers.

---

## 4. Proposed architecture and choices

**Recommended practical stack**
- Backend/data logic: Python 3.11+; FastAPI (thin REST API) **or** Streamlit-native backend for ultra-lean MVP; choose and document tradeoff in Phase 0. Favor FastAPI + React only if workflow requires rich table interactions and user approves extra complexity.
- Persistence: PostgreSQL for main implementation; SQLite allowed only for Phase 1 bootstrap, then migrate to Postgres before completion. Docker Compose for Postgres + n8n if Docker available; local native fallback documented.
- Automation: n8n self-hosted, webhook and schedule triggers, credential storage inside n8n, no secrets in exported JSON.
- Data: pandas for CSV cleaning/exports; SQL for analytics views.
- Analytics: Power BI Desktop `.pbix` (Windows) + reproducible `.csv` snapshots or Postgres connection; do not expose DB to the internet.
- Report generator: python-pptx and python-docx + PDF generation via supported libraries; graceful fallback if Office/PDF renderer unavailable. On-demand and optionally scheduler-produced reports only after agreed schedule.
- Web UI: polished professional light interface, meaningful empty states, loading/error feedback, responsive and keyboard-usable; no decorative non-working buttons.
- Email: SMTP provider *only after explicit user setup*. Development = preview/sink mode using Mailpit/MailHog or logging to sandbox; never default to sending a real email.

**Data flow (canonical system of record: Postgres)**
```
CSV / test form / optional Sheets input
    -> validation and normalization -> dedupe -> PostgreSQL leads/events
    -> transparent scoring + owner assignment + SLA evaluation
    -> Lead Queue / detail timeline + SQL KPI views -> Power BI
    -> n8n events and scheduled scans -> preview / internal notification
    -> approval queue (external emails) -> provider send -> delivery logs
    -> reports / recommendations / management deck
```

**Basic API contracts (illustrative; phase may refine)**
- `POST /api/leads/import` CSV multipart; validation report and import ID.
- `POST /api/leads` validates, creates and returns stable lead ID.
- `GET /api/leads?stage=&owner=&priority=&overdue=` paginated query.
- `GET /api/leads/{id}` details + activity timeline.
- `PATCH /api/leads/{id}` stage/owner/next action, ETag/version collision protection.
- `POST /api/leads/{id}/activity` contact attempt/outcome/note.
- `GET /api/analytics/kpis?from=&to=&source=` returns documented counters and rates.
- `POST /api/email-drafts/{id}/approve` explicit action; `POST /api/email-drafts/{id}/send` checks approval + consent + delivery idempotency and policy.
- `GET /api/automations/runs` recent workflow runs and errors.
- `POST /api/reports/generate` on-demand exports; background task only if legitimately supported locally.
- `POST /api/integrations/n8n/*` secure webhook endpoints with shared secret or signed requests.
Use OpenAPI schemas, validation, safe logs and consistent errors. Avoid building endpoints not needed for functioning UI.

---

## 5. Detailed business domain and metrics

### Lead fields (minimum)
`lead_id`, `created_at`, `updated_at`, `full_name` (fictional in demo), `company` (fictional), `email`, `phone` (fictional/invalid for sends), `lead_source` (Web/Referral/Event/InboundEmail/Manual), `campaign`, `industry`, `company_size`, `estimated_deal_value_inr`, `stage` (New/Contacted/Qualified/Meeting/Proposal/Won/Lost), `owner_id`, `consent_to_email` (boolean), `email_verified` (boolean), `last_contacted_at`, `next_action_at`, `response_sla_hours`, `lost_reason`, `created_by`, `scenario_label`.

Related tables: `lead_activities`, `lead_status_history`, `import_batches`, `import_rejections`, `lead_merge_audit`, `owners`, `automation_runs`, `notification_drafts`, `notification_approvals`, `notification_deliveries`, `config`, `audit_events`. Use migrations and indices for filtering, creation time and email normalization.

### Explicit rules
- Deduplication: normalized exact email plus phone in same country context; preserve record history; never silently merge contradictory identities; mark review-required.
- Consent: `consent_to_email=false` by default; importing leads does **not** imply consent. Never email synthetic addresses. Live mode allows only user-verified, permissioned recipients; use internal owner email for safe tests.
- Assignment: configurable round-robin; no reassigning if assigned unless explicit action.
- SLA: first response due within configurable business or elapsed hours. Start with elapsed hours and label it; business-hours schedule is optional and must not be implied.
- Recovery candidate: open stages, valid owner, overdue next action, no suppression, not already sent reminder in cooldown.
- Priority score: a documented 0–100 rule-based formula with weights in config (e.g., overdue severity 35, estimated value percentile 25, buying stage 20, contactability 10, engagement recency 10). Show breakdown and any missing factor. **Don't imply prediction/probability of purchase.**
- Opportunity-at-risk: **sum of estimated open-deal values for overdue leads**, clearly labeled *pipeline exposure*, **not lost revenue**. Avoid multiplying by invented win probabilities. If scenario modelling used, label assumed rates and show sensitivity range.
- Timezone: Asia/Kolkata for UI/business timestamps, store UTC in DB and document conversions.
- User access: MVP may be single-user local with simple auth, but make it clear it is not production security. Never expose SMTP credentials or customer records in client.

### KPI definitions (put into `docs/METRICS_DICTIONARY.md`)
- New leads = distinct leads created within the selected window.
- First response coverage = leads contacted at least once / eligible new leads in cohort.
- Median first response time = median(first_contacted - lead_created) only for contacted leads; show missing/uncontacted count separately.
- Follow-up overdue rate = active leads with next_action_at past now / all active leads with a scheduled next action (report denominator).
- Lead-to-qualified rate = unique leads ever reaching Qualified or later / eligible lead cohort.
- Lead-to-win rate = Won / eligible cohort; clearly account for still-open leads.
- Source-level funnel and drop-offs by stage.
- Pipeline exposure = sum open estimated deal values for overdue leads; illustrative, not proven leakage.
- Recovery action rate = overdue leads with completed follow-up within window / overdue eligible leads; distinguish follow-up action from closed deal.
- Workflow reliability = successful scheduled workflow runs / total attempted runs.

### Dataset generator
Create `scripts/generate_synthetic_data.py --seed 42 --count 800` producing safe synthetic rows and a `DATA_PROVENANCE.md`. Include realistic stage distributions, 5+ campaigns/sources, multiple reps, weekends, overdue/stale timing, consent false by default, intentional duplicate and validation edge cases, and reproducible expected KPI snapshots. Never use real people's contact information. Emails use reserved `.example` domains; phone numbers should be obviously fictional and not dialable. A separate local safe allowlist of test email recipients supports live email integration tests.

---

## 6. Real workflow specifications

### Workflow W1 — Intake → Validate → Assign → Track
Trigger: local form/webhook/import.
1. Validate required lead fields, source, format and consent status.
2. Normalize email/phone, detect duplicates, classify merge/review and never drop existing history.
3. Save into database with unique idempotency key; assign owner.
4. Calculate response due and priority details.
5. Create an **internal** new-lead task/email draft; in dry-run record preview.
6. Record success or failure with timestamps and step outcomes.
Acceptance: repeated identical webhook does not create repeated lead or repeated notification; rejected rows are visible with reasons.

### Workflow W2 — Scheduled overdue recovery
Trigger: n8n schedule, e.g., every hour in development (configurable; no perpetual operation promised unless n8n is actually running).
1. Read active overdue leads via secure backend endpoint.
2. Filter suppressed/closed/unassigned/within cooldown.
3. Calculate deterministic priority and recommend next action.
4. Group internal reminders by owner, issue digest / queued notifications (not one per lead).
5. Update `automation_runs` and audit records; failures are retryable without duplicate sends.
Acceptance: overdue lead creates exactly one pending reminder per cooldown; Won/Lost leads and already processed duplicates produce none.

### Workflow W3 — External follow-up approval + send
Trigger: sales user creates draft, then **separate** explicit approval action.
1. Build short personalized template from verified stored lead facts only.
2. Validate permission, verified email/allowlist, suppression status, approved content and cooldown.
3. In `DRY_RUN=true`, render and log to local sink only; no network outbound email.
4. In approved `LIVE_EMAIL_ENABLED=true` mode with correct SMTP credentials, send **only individually approved messages**; record recipient, template version, provider result, send timestamp, idempotency key, error status.
5. Failed sends remain visible for bounded retry; never claim delivery from mere SMTP acceptance.
Acceptance: absolutely no external send without both consent and user approval. Test real outbound send only to user-owned test mailbox after explicit confirmation. Add unsubscribe/suppression handling if any permitted external contact is ever enabled; obey provider limits and applicable messaging rules.

### Workflow W4 — Weekly management briefing (optional after MVP)
Trigger: manual `Generate` button first; optionally scheduled local task after consent.
1. Query validated SQL KPI views and latest issues; generate a one-page PDF with date period, all definitions, observations and limitations.
2. Generate editable slide deck (`.pptx`) from actual computed KPIs and templated data-driven charts; editable Word report (`.docx`) if chosen.
3. Optional email of **internal report only**, by explicit opt-in and verified recipient.
4. Store report path and generation metadata. No fake AI-generated quotes or invented consultant recommendations.

---

## 7. User experience / polished design

Product name: **LeadRevive**. Subtitle: *Revenue Operations & Lead Recovery Intelligence*. Visual tone: credible lightweight B2B operations tool; clean light theme, neutral background, one restrained accent, consistent typography and spacing; no crowded gradients, no random stock photos, no dead-end demo buttons.

Required views and concrete behaviors:
1. **Executive Overview:** leads received, first-response median, overdue follow-ups, qualified rate, at-risk *estimated pipeline*; trends and concise actionable observation cards with definition tooltips.
2. **Recovery Queue:** filter by priority, owner, overdue bucket/source; sortable grid, reason chips and score breakdown; action buttons **assign**, **schedule**, **mark contacted**, **open detail**, **prepare email**. Changes persist and update counts.
3. **Lead Detail:** accurate timeline of source/import/status/notes/contacts, current state, next action, editable owner, draft preview and approval record.
4. **Automations:** n8n job status, last run time, number processed/suppressed/failed, retry operations, exported workflow link; no fake healthy badges if provider is offline.
5. **Analysis:** funnel by stage/cohort, segment/source comparison, lost reasons, scenario comparisons; Power BI report can be separate desktop artifact, not embedded falsely.
6. **Data Quality:** import results, duplicates, invalid rows and resolutions with audit trail.
7. **Settings:** SLA hours, scoring weights, reminder cooldown, dry-run/live status, safe recipient allowlist, SMTP status (never reveal password), data reset warning.
8. **Reports:** download aggregate CSV/XLSX, management PDF, PPTX; visibly mark synthetic-data origin.

For a project demo: provide populated fictional records, genuine filters and operations, clear error feedback, purposeful empty states, accessible form labels, keyboard navigation and mobile-friendly layouts. Target 1366px laptop screenshot. Keep charts readable and labels honest. Use screenshots taken from the actually running app; no mockups masquerading as outputs.

---

## 8. Recommended repository layout (Codex can improve with justification)
```
leadrevive/
  README.md
  .env.example                   # placeholders ONLY
  .gitignore
  docker-compose.yml
  backend/
    app/{api,models,schemas,services,analytics,notifications,db}/
    migrations/
    tests/
    pyproject.toml
  frontend/                       # only if React path chosen
    src/{components,pages,lib,styles}/
    package.json
  automation/
    n8n/workflows/{intake.json,overdue_recovery.json,email_approval.json}/
    README.md
  data/
    synthetic/                    # only fake contacts
    processed/
  scripts/
    generate_synthetic_data.py
    seed_db.py
    smoke_test.py
  analytics/
    sql/
    powerbi/                     # .pbix if built locally
    exports/
  reports/
    templates/
    generated/.gitkeep
  docs/
    PHASE_PLAN.md
    ARCHITECTURE.md
    DATA_DICTIONARY.md
    METRICS_DICTIONARY.md
    BUSINESS_CASE.md
    REQUIREMENTS_BRD.md
    USER_STORIES_UAT.md
    REFERENCES.md
    TEST_EVIDENCE.md
    DEMO_SCRIPT.md
    RESUME_CLAIMS.md
    decisions/
  screenshots/
    README.md
```
Keep generated logs, caches, private reports, real credentials, `.env`, live contacts, and secrets out of Git. `.env.example` provides documented safe placeholders. Add root scripts/Make targets appropriate to Windows PowerShell and OS detection.

---

## 9. Phase-by-phase delivery plan, approvals, and screenshot gates

### Phase 0 — Discovery & design (NO network emails)
- Inspect Windows, Docker, Python, Node, Power BI and existing folder.
- Confirm UI path (suggest **FastAPI + React** for polished product demo; Streamlit if fast-only approved), DB and n8n running mode, and whether Power BI Desktop is installed.
- Create requirements, acceptance checks, architecture diagram, licensing/reference manifest and phase plan.
- **Gate:** user approves scope/stack; no need to repeat questions already answered.

### Phase 1 — Dataset + DB + analysis foundation
- Create generator, schema/migrations, seed data, data cleaning, import exception handling, deterministic priority function, SQL KPI views.
- Write focused tests for duplicate/invalid/overdue/consent/score boundary cases; print KPI snapshot with counts and denominators.
- **Gate:** `tests pass`, SQL inspection shows consistent records. Screenshot only if a visual data-view UI exists; otherwise no unnecessary screenshots.

### Phase 2 — Working operations interface
- Build overview, recovery queue, lead detail, import/validation UI, settings; connect to persistent APIs.
- Ensure stage edits/owner changes update DB and metrics; display synthetic-data label.
- **SCREENSHOT GATE:** user captures `SS01_Overview.png`, `SS02_Recovery_Queue.png`, `SS03_Lead_Timeline.png`, `SS04_Data_Quality.png` only after actual functionality works. Codex should say **exactly which screen and action** to capture.

### Phase 3 — n8n automation, test SMTP sink
- Run real n8n workflow W1 and W2. Test webhooks, hourly schedule simulation, idempotency, retry and failure. Wire notification previews to local email sink; test with synthetic data.
- Build W3 preview+approval UI and integrate with sink; real external email remains disabled.
- **SCREENSHOT GATE:** `SS05_n8n_Workflow.png`, `SS06_Automation_Run_Log.png`, `SS07_Email_Preview_Approval.png`, `SS08_Test_Email_Sink.png`.
- **Gate:** user reviews dry-run, then separately opts into ONE verified external test send if desired. Codex must not silently enable live sending.

### Phase 4 — Analytics & measurable experiment
- Create cohort/source/stage analytics views, clean exports, and editable PBIX if Windows Desktop supports it.
- Before/after **simulated scenario**: manually managed baseline vs automation-assisted test using comparable events and fixed seed; show coverage, overdue count, processing duration and correctness. Mark as simulation and specify which timing is modeled vs measured.
- **SCREENSHOT GATE:** `SS09_PowerBI_Analysis.png`, `SS10_Experiment_Comparison.png`.
- **Gate:** KPI reconciliation tests pass (UI = SQL = Power BI within documented refresh time).

### Phase 5 — Reports + documentation + interview package
- Generate proper editable `.pptx` (approx 6–8 slides) and concise `.docx` business report plus PDF preview from measured project values. Reports should look like a junior analyst/consultant briefing, not promotional AI copy: context, assumptions, method, baseline, actions, outcomes, limitations, recommended next steps.
- Create `docs/BUSINESS_CASE.md` (~1–2 pages), user stories, UAT test sheet, `docs/DEMO_SCRIPT.md` (2–4 minutes), architecture, install/run steps, provenance and `docs/RESUME_CLAIMS.md` with ONLY verified claims.
- **SCREENSHOT GATE:** `SS11_Executive_Report.png`, `SS12_Management_Presentation.png` only where visual evidence is useful.
- **Gate:** human review of generated narrative and presentation; remove generic hype, unearned metrics and invented business claims.

### Phase 6 — Final verification / portfolio finish
- Run clean-install startup in documented Windows environment. Check lint/unit/integration/UAT, seeded demo, n8n import/run, report generation, disconnected email service behavior, and secure defaults.
- Confirm UI responsiveness, accessibility basics, file paths, links, demo screenshot quality, and README simplicity.
- Tag final state and provide only proven resume-ready bullets plus a short truthful interview explanation. Don't claim customer adoption or savings without proof.

---

## 10. Acceptance / negative tests (minimum)

Automate where practical and record observed outcomes:
- Duplicate import of same source file is idempotent or flags collisions; counts don't inflate.
- Bad email, empty company, unknown stage, malformed value produce human-readable validation errors.
- Consent false never sends external email; synthetic `.example` addresses never used for live send.
- Won/Lost leads never enter recovery queue.
- Overdue lead gets no more than one reminder per cooldown/idempotency key.
- Empty, all-overdue, and all-contacted datasets render cleanly; KPI calculations avoid divide-by-zero.
- Assign/change stage persists through refresh and audit log includes before/after state.
- n8n/SMTP offline → app shows failure and queued retry, not success; no invented delivery confirmation.
- Duplicate outbound send request (e.g., double click/retry) cannot produce duplicate email.
- Report generated from selected date window reconciles to analytics and includes data-origin note.
- Dataset contains no identifiable real persons; secrets scanner and `.gitignore` guard exports.
- Power BI `.pbix` exists and opens if deliverable claimed; otherwise document unavailable tool and provide reproducible alternative.

---

## 11. What must be asked from user (only when needed)

At the start ask **at most a compact grouped list only for blocking decisions**; don't block safe Phase 0 work:
1. Existing project workspace path and whether to initialize a fresh Git repo.
2. Installed Docker, Python, Node and Power BI (prefer auto-detect).
3. Preferred UI approach only if trade-off affects scope (default recommend FastAPI+React as user wants professional design).
4. Whether there is an authorized real business for pilot; default **none — synthetic portfolio case**.
5. Whether user has own safe test SMTP/email mailbox; default **no, use Mailpit and DRY_RUN**.
6. Whether user wants Google Sheets integration; default phase 2 optional, core works without it.

Do NOT request passwords in chat or commit secrets. User configures local `.env` or credential manager themselves. For actual external email action, demand explicit approved recipient and message content, test first against the user's own mailbox, and confirm authorization. No external sending just because a workflow was imported.

---

## 12. Report quality and resume strategy

**Business narrative rule:** Every management claim cites actual SQL query/result, dataset field or experiment log; forecasts are labeled *scenario assumptions*. Avoid phrases like "revolutionized revenue" or "improved profitability 40%" unless measured in a real consented deployment. Clearly distinguish (i) observed synthetic demo metrics, (ii) measured automation runtime, (iii) projected value/assumptions. Final reports contain tables and findings with business interpretation, not walls of generic AI prose.

**Possible honest future resume title:** `LeadRevive — Revenue Operations & Lead Recovery Automation | Excel, SQL, Power BI, n8n, Python`

**Possible post-completion bullets (must edit to match evidence):**
- `Designed a lead-recovery workflow that detects overdue follow-ups, prioritizes a sales queue, and sends controlled owner reminders using SQL-backed rules and n8n.`
- `Built Power BI funnel reporting and an Excel KPI model across [verified N] synthetic B2B lead records; documented data-quality exceptions and cohort-level conversion bottlenecks.`
- `Validated automated assignment, reminder idempotency, and email-approval safeguards through [verified N] end-to-end test cases.`

**Never place placeholders like `[verified N]` on actual final resume.** Do not claim production use of Power BI/n8n before they actually work.

**Interview readiness:** Explain why a lead can be "overdue" but not "lost"; source of each KPI; why rule-based scoring was chosen instead of unsupported ML; how duplicate and consent checks prevent operational mistakes; how the system behaves when SMTP or n8n fails; what part is real execution and what part is modeled; what business stakeholder would do with each dashboard.

---

## 13. Immediate Codex start instruction

**Your next message to the student should be:**
1. Briefly confirm you have read the spec, identify present workspace/environment facts after inspection.
2. Provide Phase 0/1 action plan and any *only essential* blockers.
3. Create `docs/PHASE_PLAN.md`, `docs/ARCHITECTURE.md` and `docs/REFERENCES.md` in repo; check repository references and licenses before reuse.
4. If no blockers, initialize clean scaffold and synthetic-data generator with repeatable tests (Phase 1 slice), then show exact commands/results and seek go-ahead for the next slice.

No fake screenshots, no unapproved email, no invented performance results, no wholesale copied project. Prioritize a functioning, attractive, business-oriented demo over gratuitous architecture complexity.

**End of master specification.**
