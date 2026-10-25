# Requirements and acceptance checks

Problem: an India-based fictional B2B provider lacks consistent response and follow-up discipline. Users are sales associate, sales manager and analyst. Objective: identify workflow failures and prioritize recovery, with honest synthetic evidence. This is not a real client deployment.

| Requirement | Acceptance / phase |
|---|---|
| Safe representative input | 800 reproducible rows, 5 sources, 6 campaigns, 4 fictional reps, deliberate invalid and conflicting fixtures; Phase 1 |
| Reliable persistence | Alembic upgrade/downgrade, SQL constraints, foreign keys, stable source IDs, history and audit; Phase 1 |
| Quality exceptions | Every invalid/duplicate/conflict recorded with original row and human-readable reason; repeat file has no extra writes; Phase 1 |
| Deterministic recovery | Closed leads excluded, explainable bounded score and missing factors; Phase 1; cooldown and assignment workflows Phase 3 |
| Operational interface | Persistent owner/stage/schedule/contact changes and optimistic version checks; Phase 2 |
| Safe automation | Running n8n intake/reminder workflows, grouped digests, retries, idempotency and Mailpit; Phase 3 |
| External approval | Separate approval, consent, verification, synthetic block, allowlist and suppression; real send separately authorized; Phase 3 |
| Accurate analytics | Explicit cohorts/denominators, fixed evaluation clock, SQL reconciliation; Phase 1 foundation / Phase 4 full model |
| Management outputs | Actual computed aggregates in reports/deck, labeled assumptions, evidence-based resume; Phases 5–6 |

Local single-user MVP. No paid services, private customer imports, external AI processing or unattended schedules required. Generated reports/live records/secrets excluded from Git. PostgreSQL and actual n8n/Power BI deliverables are mandatory final checks or explicitly documented tool limitations.
