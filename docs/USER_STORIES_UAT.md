# Phase 2 user acceptance checks

All records must remain visibly SYNTHETIC. Browser tests automate the core paths in `frontend/tests/operations.spec.js`; API tests cover negative requests in `backend/tests/test_api.py`.

| User need | Action and expected result |
|---|---|
| Manager understands exposure | Overview cards reconcile to `/api/analytics/kpis`; source/cohort selections update counts and denominators. Exposure says estimated opportunity value, not lost revenue. |
| Associate finds urgent leads | Recovery Queue → follow-up Overdue, owner filter, sort Value/Priority; only matching records appear. Search, pagination, empty state and reset work. |
| Associate creates a safe enquiry | New synthetic lead → fictional identity, .example email, FICTIONAL-IN token and INR value → persisted New lead, false consent, timeline. Duplicate contact rejected. |
| Associate takes recovery action | Open lead → assign owner, schedule in IST, save → reopened record and API retain UTC-converted values. Mark contacted → first contact preserved, last contact updated, activity/audit recorded. |
| Manager sees state history | Open lead → change stage → Activities and Audit history expose recorded state changes. Stale API version returns 409 and preserves latest data. |
| Analyst checks imports | Data Quality → upload generated CSV → existing file recognized, counts unchanged. Invalid/duplicate/conflicting rows retain original values and reasons. |
| Analyst decides a conflict | Select identity collision → compare incoming/candidates → note → Keep existing → review recorded, existing lead exports unchanged. Repeated decision rejected. |
| Analyst excludes invalid input | Select validation error → explanation → Discard invalid → original evidence remains. Correct source and reimport changed file to ingest corrected data. |
| Manager configures priorities | Settings → change weights totaling 100 → Save → queue recalculates from saved rules. Invalid totals disable Save and backend independently rejects them. |
| Manager configures response expectations | SLA setting applies to newly manually created leads; imported rows and existing lead SLA values remain explicit. |
| Analyst exports evidence | Export all leads / Export exceptions → CSV downloads with SYNTHETIC origin and spreadsheet formula-prefix protection. |
| User handles failures | API unavailable/error response → visible error instead of metrics; retry via page reload/refresh after recovery. No success status fabricated. |
| Mobile user navigates | At 390px, navigation and forms remain usable; wide queue is contained in its own scroll area, page does not overflow. |

No automated external communication, approval emails, automation health simulation, Power BI visuals, or generated management reports are part of Phase 2.
