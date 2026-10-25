# Phase 1 integrity review — 24 October 2026

User approved Phase 2 subject to this review. Original 13 tests passed before changes. Review identified gaps and corrected them before Phase 2 implementation; expanded foundation suite then passed 18 tests. A populated legacy-migration test was subsequently added as part of Phase 2 regression coverage.

| Area | Gap found | Fix / verification |
|---|---|---|
| Duplicate/conflict handling | No direct test of one incoming row matching two different existing identities | Test competes on normalized email and another lead's phone, verifies both candidate IDs in merge audit, and compares every existing lead before/after. No automatic merge. |
| Scoring | Boundary test did not validate individual midrank/recency/overdue values | Exact 45-point case checks all five factors; invalid/NaN weights rejected; export values reconciled to the scoring function. |
| SLA | No explicit late-contact test or offset-equivalence assertion | Tests cover exact deadline, one second late, late recorded response, and equivalent UTC/IST inputs. |
| Timestamps | Variable precision ISO text could put whole-second instants after fractional instants in SQL string comparisons | Canonical six-digit fractional UTC timestamps; migration 0002 normalizes existing lead/import/history/audit timestamps. SQL callers must bind canonical UTC (`iso()`); inspection queries document this. |
| Qualification KPI | Historical lookup only recognized literal Qualified, missing later-stage history after a lead becomes Lost | Parse stored event JSON and count Qualified/Meeting/Proposal/Won evidence; regression verifies Meeting → Lost retains qualification. |
| KPI/queue exports | Export file contents not directly verified | Tests open generated exception and queue CSVs, reconcile record counts, score and breakdown; KPI totals reconcile to independent SQL exposure query and source-view sum. |
| Currency portability | PostgreSQL INTEGER would not cover the validator's allowed currency range | Application uses BIGINT on PostgreSQL and 64-bit INTEGER on SQLite; migration 0002 widens PostgreSQL currency. PostgreSQL execution remains unverified. |
| Alembic | Only empty upgrade and full rollback/rebuild checked | Added populated 0001 → head test preserving lead identity/value while normalizing timestamp precision. Existing 0001 frozen schema retained. |

Migration 0002 deliberately retains normalized timestamp precision and widened currency on downgrade to avoid data loss. Full downgrade to base still removes schema, as tested. This is documented behavior, not a claim of reversible narrowing to 32-bit currency.

Remaining limits: PostgreSQL runtime/concurrency verification awaits Docker; reminders/cooldown/send policies are Phase 3; historical state reconstruction and Power BI reconciliation belong to Phase 4. Current KPIs are a current-state creation-cohort snapshot, not a time-travel pipeline model.
