# Screenshot gates

Phase 1 needed no screenshots. Phase 2 captures below are actual Chromium screenshots of the built React interface connected to a temporary SQL database through FastAPI, not mockups.

| Capture | Screen and preceding action |
|---|---|
| [SS01_Overview.png](SS01_Overview.png) | Open seeded Overview; reconcile cards against live API; all sources/all-time cohort. |
| [SS02_Recovery_Queue.png](SS02_Recovery_Queue.png) | Recovery Queue → Overdue follow-up → Fictional Rep 1 → sort deal value. |
| [SS03_Lead_Timeline.png](SS03_Lead_Timeline.png) | Create fictional lead → assign Rep 2 → Qualified → schedule 25 October, 11:00 IST → record contact → Audit history. |
| [SS04_Data_Quality.png](SS04_Data_Quality.png) | Upload same generated CSV → confirm replay → inspect identity collision → compare candidate → Keep existing with explanatory note. |
| [SS02a_Mobile_Overview.png](SS02a_Mobile_Overview.png) | Render Overview at 390px after the test lead and review decision; confirm no page overflow. |

Desktop viewport: 1366 × 900; full-page captures extend beyond viewport height. Clock is visibly fixed at 24 October 2026, 17:30 IST. The initial 754/404 lead/overdue values differ from Phase 1's midnight snapshot (754/390) because evaluation time differs. Mobile capture includes the newly created test lead and one reviewed exception. To reproduce, build the UI and run `npm.cmd test` from frontend (see docs/STARTUP_PHASE_2.md). Playwright creates isolated SQL data, performs the exact steps, waits for transient success messages to disappear for detail/review captures, and overwrites these images.

## Phase 3 captures

| Capture | Exact actual screen/action |
|---|---|
| [SS02b_Recovery_Queue_Loaded.png](SS02b_Recovery_Queue_Loaded.png) | Before Phase 3: Recovery Queue → Overdue → Fictional Rep 1 → Priority score. Waited for actual rows; 12 displayed / 85 matches. Verified value sort, priority sort and opening first lead before concluding. |
| [SS05_n8n_Workflow.png](SS05_n8n_Workflow.png) | Sign in to local n8n → open published LeadRevive W2 → actual canvas with hourly/webhook triggers, reservation step, digest delivery and failure branches. |
| [SS06_Automation_Run_Log.png](SS06_Automation_Run_Log.png) | Application → Automations after real successful/failed workflow scenarios; actual PostgreSQL run records and outbox/delivery evidence. |
| [SS07_Email_Preview_Approval.png](SS07_Email_Preview_Approval.png) | Controlled fictional lead → Prepare Mailpit preview → Automations → select pending item → check sink-only approval → Approve. Capture actual review panel with approval hash/recipient policy before Send. |
| [SS08_Test_Email_Sink.png](SS08_Test_Email_Sink.png) | Execute approved UI send → verify one capture → open actual message in Mailpit. Envelope is approved-preview@leadrevive.test; no external recipient. |

Phase 3 uses the live evaluation clock and canonical PostgreSQL; those images are separate from the fixed-clock disposable Phase 2 browser scenario. SS07 intentionally crops the actual approval panel for readability. No secrets are displayed. Reproduce extra queue with `node scripts/capture_loaded_queue.mjs` and Phase 3 captures with `node scripts/test_phase3_browser.mjs` from frontend, after the real integration script completes. Instructions: docs/STARTUP_PHASE_3.md.
# Phase 4 analytics evidence

All Phase 4 captures show synthetic data at snapshot `9a80207b950500a9`. Power BI captures come from the actual reopened `LeadRevive_Phase4_SYNTHETIC.pbix`, using report-window-only capture.

| File | Actual screen/action |
|---|---|
| SS09_PowerBI_Analysis.png | Page 02: overdue/scheduled counts, rate, estimated exposure, source and owner charts |
| SS09a_Application_Analytics.png | React Analytics: snapshot provenance, stages, SLA, source filter and owner table |
| SS09b_PowerBI_Funnel.png | Page 01: cohort, coverage, qualification, current Won and stage distribution |
| SS09c_PowerBI_Source.png | Page 03: source outcome comparison and functioning source slicer |
| SS09d_PowerBI_Owners.png | Page 04: open, overdue and business-rule eligible owner workload |
| SS09e_PowerBI_SLA.png | Page 05: elapsed-hour SLA partition and contacted-only median |
| SS09f_PowerBI_Workflows.png | Page 06: actual local synthetic workflow ledger aggregates |
| SS09g_PowerBI_Simulation.png | Page 07: explicitly modeled identical-event comparison |
| SS09h_PowerBI_Reconciliation.png | Page 08: measures from actual Power BI DAX model |
| SS09i_PowerBI_Source_Filtered.png | Event selected in actual slicer: visual lead count 152; cleared back to 758 |
| SS10_Experiment_Comparison.png | React controlled simulation: modeled outcome and actual application-rule verification, including unchanged raw overdue KPI |

Reproduce app captures with `node frontend/scripts/test_phase4_browser.mjs`. Open the final PBIX and use `scripts/capture_powerbi.ps1` for its eight pages. `verify_powerbi.ps1` checks the actual model's 13 KPIs independently of image capture. Do not compare a refreshed live queue with an old analytics screenshot without matching evaluation times.



## Phase 6 clean-install captures

`SS13_Clean_Install_Queue.png` and `SS14_Clean_Install_Reports.png` are actual browser captures of independent QA on port 18000. QA starts with 754 seed leads and adds two integration fixtures; it is separate from the preserved 758-record snapshot. Reports shows a real generated pack. SS12 was refreshed from the enlarged actual PowerPoint layout. Existing Power BI captures remain tied to their frozen snapshot.

## Phase 5 review captures

All new analytics images use snapshot `9a80207b950500a9`, data revision recorded in `reports/templates/evidence_images.json`. These are actual Power BI window captures or actual rendered report files, not mockups.

| File | Evidence |
|---|---|
| SS11_Executive_Report.png | First page of the actual two-page portable PDF |
| SS11a_PowerBI_Workflows.png | Refined workflow cards/chart and latest-state job/attempt table |
| SS11b_PowerBI_Simulation.png | Refined modeled-contact comparison, with explicit timing assumptions |
| SS11c_PowerBI_Reconciliation.png | Thirteen actual DAX comparisons with consistent precision and no aggregate PASS claim |
| SS11d_PowerBI_Analysis.png | Matching frozen exposure/workload view |
| SS11e_Reports_Interface.png | Working Reports generation/download page |
| SS12_Management_Presentation.png | Actual PowerPoint-rendered slide from the editable 10-slide deck |

PowerPoint viewports crop the original window captures to the report canvas for readability; original screenshot files and hashes remain preserved. The existing browser suite refreshed standard operations captures during Phase 5 regression. Future default regression captures go to `frontend/test-results/evidence`; review baselines are replaced only when `LEADREVIVE_CAPTURE_BASELINE=1` is explicitly set. Phase 3 scenario JSON/logs and Phase 4 frozen analytics/PBIX remain historical evidence.
