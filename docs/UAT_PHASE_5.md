# Phase 5 UAT checklist

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
