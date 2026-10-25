# Interview explanation notes

**Business problem:** An overdue lead is work waiting for attention, not proof that a sale was lost. Estimated pipeline exposure prioritizes investigation; it does not measure recovered revenue.

**Data:** Fixed-seed synthetic enquiries use fictional contacts and reserved domains. PostgreSQL holds the canonical operational record; a repeatable-read snapshot drives CSV, Excel, React analytics and the Power BI import model.

**KPI trust:** Explain the creation cohort, inclusive/exclusive window, UTC evaluation timestamp and current-state limitation. Python and PostgreSQL calculate independently; Power BI DAX aggregates frozen lead facts. Compare values and snapshot IDs, not screenshots from different refreshes.

**Response SLA:** Elapsed hours from creation. The contacted-only median omits uncontacted leads; display those separately. A response at the exact deadline meets SLA. Overdue follow-up is a different next-action control.

**Why rule-based scoring:** The dataset does not justify a learned purchase model. The score explains urgency, value, stage, contactability and recency; it is not a purchase probability.

**Automation:** Intake validates and assigns; recovery groups due work by owner; outbox honors exact-content sink approval; status sync cancels stale work. Idempotency keys, unique ledger rows, cooldown and uncertain-ack lookup prevent unsafe resend.

**Failure behavior:** Deliberate SMTP failure remains audited; bounded retry is visible. Uncertain acknowledgement is reconciled against Mailpit rather than blindly resent. External live delivery stays disabled.

**Experiment:** Forty identical due events; modeled owner response after manual review or hourly scanning. Real application rules execute the contacts and reminder reservations in disposable databases. Runtime is measured locally; human effort, conversion and ROI are not. Completing a contact alone does not change an old next-action date, so raw overdue can remain unchanged.

**Stakeholder action:** Sales managers assign missing owners and rebalance workload; associates act on the queue and reschedule; analysts reconcile metrics and investigate source/cohort differences before recommending budget changes.
