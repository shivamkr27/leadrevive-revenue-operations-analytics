# Power BI: inspect and refresh a portable copy

Open LeadRevive_Phase5_SYNTHETIC.pbix to inspect the saved imported model without refreshing. The Phase 4 PBIX and authored Phase 5 PBIP/model/report remain preserved. Eight pages cover stages, overdue exposure, sources, owners, elapsed-hour SLA, workflows, modeled comparison and reconciliation. All data is synthetic.

## Location-correct editable copy

From the repository root, after installing requirements:

```powershell
.venv\Scripts\python.exe scripts/prepare_powerbi.py --output data/processed/powerbi_portable
```

The helper verifies the current immutable generation, copies the authored Phase 5 project and resolves six CSV paths from the clone's actual location. It changes only the derived model's input paths, preserves visuals/DAX, excludes caches, and records original/derived hashes in PORTABILITY.json. Existing output folders are refused; use a new output name on repeat runs. No SQL writes, analytics refresh, email or workflows execute.

Open data/processed/powerbi_portable/LeadRevive.pbip in Power BI Desktop. Click Refresh, clear filters, inspect and save as a NEW PBIX. Desktop installation and interactive refresh/save remain manual. Recreate a copy after moving the clone; a PBIP does not automatically resolve CSVs relative to its own location. The helper avoids editing six paths by hand. Do not use build_powerbi.py for relocation: it recreates authored layouts.

Default included generation: f03b072d3f984a95a83a34ccb865a534. Optional --generation selects another VERIFIED locally available generation. An adjusted model has a new hash; historical Desktop DAX evidence is not a new verification of that copy.

## Existing PBIX manual alternative

Original approved artifacts retain historical paths and hashes. Save a copy before editing. In Transform Data > Advanced Editor, change ONLY each File.Contents argument to the corresponding file under the clone's included generation:

| Table | CSV |
|---|---|
| LeadFacts | LeadFacts_SYNTHETIC.csv |
| Operations | Operations_SYNTHETIC.csv |
| Experiment | Experiment_SYNTHETIC.csv |
| Reconciliation | Reconciliation_SYNTHETIC.csv |
| Workflow | Workflow_SYNTHETIC.csv |
| Snapshot | ReadMe_SYNTHETIC.csv |

Six original Phase 5 inputs point to excluded generation ec6fac1f9740442f906f00c0918cea4a. Use the INCLUDED generation above; do not reconstruct the historical directory. The helper applies this mapping automatically without changing original artifacts.

## New data and evidence

Optional refresh on your own demo: `docker compose exec -T backend python scripts/refresh_analytics.py`. It publishes new analytics outputs, not lead edits. Then prepare another Power BI copy. Do not refresh the preserved snapshot just to relocate it. Historical Desktop open/refresh/save/reopen and 13-KPI DAX evidence remains unchanged. The helper verifies paths/source hashes, not Desktop execution. The older verify_powerbi.ps1 writes historical evidence filenames; arrange separate outputs before using it for new evidence.

Facts contain no contact names/emails/phones. Stage distribution is current state, not sequential historical conversion. Exposure is estimated, not recovered revenue. The 20-versus-34 comparison assumes review/response timing. Workflow counts include induced faults. SMTP accepted by local sink only; external sending disabled.

Microsoft references: [PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [report structure](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic model](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset). Schema/path validation does not replace Desktop refresh.
