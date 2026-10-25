# LeadRevive local automation

Original n8n exports:

| File | Trigger | Effect |
|---|---|---|
| n8n/workflows/intake.json | Authenticated POST `/webhook/leadrevive/intake` | Validate/dedupe/assign → persist → internal task/draft → audit |
| n8n/workflows/overdue_recovery.json | Hourly schedule or authenticated recovery webhook | Reserve current overdue work → group by owner → Mailpit-only digest → audit |
| n8n/workflows/email_approval.json | Five-minute schedule or authenticated dispatch webhook | Check outbox/approval/context → reconcile stable Message-ID → safe SMTP → ledger/failure |
| n8n/workflows/status_sync.json | Authenticated status-sync webhook | Version-checked lead change → history → stale-reminder cancellation |

FastAPI owns the database, deterministic eligibility and SMTP transport so scheduled/manual operations share approval, suppression, retry and idempotency rules. n8n supplies real webhook/schedule execution, authenticated HTTP steps, failure branches and execution history. Credential `LeadRevive local shared header` supplies `X-LeadRevive-Key` to both authenticated webhooks and backend calls. No token values appear in exports.

Use scripts/start_local.ps1 for new-clone startup; the historical start_phase3.ps1 assumes the preserved SQLite migration history. Run configure_n8n.py without `--if-needed` only when intentionally restoring the four project exports; it reimports/re-publishes known workflows. Normal startup uses `--if-needed` and preserves existing states. Exports default inactive for safe import elsewhere; publish only after binding your local credential. Never configure an external SMTP relay.

The tests/schedule_probe.json definition is a zero-lead-scope fixture; verification temporarily publishes it for a real scheduled callback, then unpublishes it. It is not a fifth permanent business automation. See docs/STARTUP_PHASE_3.md and docs/PHASE_3_REPORT.md for runtime details, tests, business purpose and limitations.
