# Phase 6 — final QA and portfolio packaging

25 October 2026. **Local release candidate v1.0.0-rc.1, pending owner approval.** No GitHub publication, public deployment, external email or final project sign-off performed.

## Outcome

Slides 4–7 use enlarged actual Power BI viewports and three readable findings. Slide 7's crop was tightened to remove a partial row. Actual PowerPoint open/export succeeded. The portable PDF is two pages; “Automation and evidence” and its figures start on page 2. Layout assertions cover normal and empty reports.

Read-only transactions verified all **758 leads**, original audit/history/notification rows and workflow definitions/publication states. No seeding, migration, regression write, workflow trigger or outage operation was run against the existing project. Already-running schedules remained active: two automation runs and two audit events naturally appended during the before/after window; every captured original record retained its hash. A running scheduler's ledger is not frozen.

## Executed verification

| Check | Result |
|---|---|
| Full PostgreSQL regression | **61 passed, 377.743 s**, temporary schemas in separate QA PostgreSQL |
| Full SQLite regression | **58 passed, 3 PostgreSQL-only skips**, 61 discovered, 100.477 s |
| Final bootstrap/layout checks | **4 passed, 1 PostgreSQL-only skip**, 5 discovered, 5.477 s; overlaps reporting regression and adds two bootstrap safeguards |
| Frontend production build/browser regression | Build passed; **7 passed, 46.7 s**, temporary test API |
| Real QA n8n/PostgreSQL/Mailpit integration | **19 checks passed**; two QA-only fixtures; original seed rows preserved |
| Clean Docker browser | **4 checks passed**: populated queue, actual PDF download, Reports automated WCAG A/AA, mobile/no JS errors |
| QA reports/persistence/provider outages | **7 checks passed**; normal/empty packs, hashes, pinned snapshot, repeat-start skip, persistence, truthful failures and restoration |
| Alembic | Fresh upgrade through **0005**; `alembic check`: **No new upgrade operations detected** |
| Existing PostgreSQL integrity | **15 tables**, 758 leads, original-row hashes preserved; no unvalidated foreign keys; workflow definitions/states unchanged |
| Reviewed report pack | 13 KPI values, five artifact hashes, 10 slides/four actual images, two PDF pages; valid eight-page Phase 5 PBIX container |
| Frozen analytics | **13 KPIs, 16 file hashes**, CSV/Excel readback and saved Desktop DAX; **10 management/evidence queries** executed read-only |
| Host dependencies | `pip check`: no broken requirements |

Suites overlap; do not add these counts as independent tests. Earlier Desktop refresh/reopen/DAX evidence was reused; Phase 6 rechecked saved values/container/provenance, not a new Desktop refresh. Automated accessibility checks are not a full manual certification.

## Clean install and fixes

QA used project `leadrevive-qa`, new PostgreSQL/n8n/Mailpit volumes, separate network/secrets, loopback ports and report/export binds. No existing volume or service port was reused. Cached image/dependency layers were available; this was not a second Windows machine or uncached download test.

`start_local.ps1` and `bootstrap_demo.py` remove dependence on private SQLite bootstrap history. An empty database migrates/seeds; a populated database is skipped without schema changes. `configure_n8n.py --if-needed` preserves existing workflow state and handles an empty store. Docker creates seed-output directories before switching to its non-root user. These paths were exercised in QA; explicit container analytics refresh is available.

Initial install attempts exposed the unwritable seed-output directory and empty-workflow handling; both were fixed and passed on retry. The new browser harness needed an explicit context for axe; the corrected harness passed. A Windows bootstrap test retained a SQLite connection during temporary-directory cleanup; closing it fixed the test. These setup/test failures are recorded, not silently omitted.

Fresh QA contains **754 seed leads**; integration adds **two** QA fixtures, yielding 756. The existing historical cohort remains **758**. Frozen Analytics/report screenshots are tied to their generation/evaluation time; live Overview and fresh reporting use their own data/clock.

## Portfolio contents

- [Setup/isolated QA](SETUP.md), [architecture](ARCHITECTURE.md), [metric definitions](METRICS_DICTIONARY.md).
- [Versioned PPTX/PDF/DOCX, case study, assumptions and provenance](../reports/portfolio/v1.0.0-rc.1/README.md).
- Editable [Phase 5 PBIX](../analytics/powerbi/LeadRevive_Phase5_SYNTHETIC.pbix), preserved Phase 4 PBIX, PBIP/model/DAX, CSV/Excel, [SQL pack](../analytics/sql/README.md), [four n8n workflows](../automation/README.md).
- Actual [screenshots](../screenshots/README.md), including clean-install queue/reports; [UAT](UAT_PHASE_5.md), [demo](DEMO_SCRIPT.md).
- [Role-specific resume candidates](RESUME_CLAIMS.md), [60–90-second interview explanation](INTERVIEW_NOTES.md), [business case](BUSINESS_CASE.md).
- Sanitized [QA evidence](evidence/), [release checklist](RELEASE_CHECKLIST.md), [exact manual Git publication commands](GIT_PUBLICATION.md).

`scripts/package_release.py` copies verified representative files and prepares the source ZIP, file-hash manifest and checksum under ignored `releases/`. It checks eligible raw files/direct ZIP members against configured local secret values and private profile paths. Only the reviewed immutable generation is eligible; runtime cohorts, credentials, databases, logs, backups and caches are excluded. No Git identity, staging, commit, tag or remote is created automatically.

`scripts/verify_release.py` checks every archived source-file hash and primary documentation links, and confirms required bootstrap inputs/runtime exclusions. Python source compilation passed. The source archive is approximately 6 MB; the release manifest contains its exact eligible file list and the companion `.sha256` identifies the archive. QA services/volumes are retained separately for review; nothing was deleted.

## Remaining limitations

- Local single-user scope; no production authentication/roles, load/security certification, public deployment or universal exactly-once guarantee.
- Synthetic records and deliberate SMTP faults are explicit. **SMTP accepted by local sink** only; **external live delivery disabled**.
- **20 versus 34** contacts depends on review schedules and assumed two-hour response. No observed uplift, revenue recovery, human savings or cash ROI is claimed. Cost values are sensitivity assumptions.
- Power BI uses local frozen CSV paths, adjusted after relocation. Desktop verification applies only to the recorded revision; new cohorts need new verification.
- No second-machine/offline installation or narrated video is claimed. A reproducible 2–4-minute demonstration script is provided. Report history has no automatic retention cleanup.
- Historical phase notes/artifacts preserve earlier gates and dates. This report gives the current status. Source-pack hashes identify the local candidate until the owner creates a real Git commit/tag.
- Project license choice, public publication and final acceptance remain owner decisions; no open-source license grant is inferred.

Recommended repository: **leadrevive-revenue-operations-analytics**. Description: **Synthetic revenue-operations portfolio: lead recovery, PostgreSQL/SQL analytics, Power BI, Excel, n8n automation and controlled local reporting.**

**Stop for review.** Review the candidate, evidence and remaining limitations before publication or final sign-off.
