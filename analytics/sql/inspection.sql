-- All timestamps UTC; bind :as_of explicitly, e.g. 2026-10-24T00:00:00.000000Z.
-- Use six-digit fractional precision to match migration 0002. Values are integer paise.
SELECT stage, COUNT(*) AS lead_count FROM leads GROUP BY stage;
SELECT * FROM v_source_funnel ORDER BY lead_source, stage;
SELECT COUNT(*) AS overdue, SUM(estimated_value_paise) / 100.0 AS exposure_inr
FROM v_open_pipeline WHERE next_action_at < :as_of;
SELECT COUNT(*) AS recovery_candidates FROM v_open_pipeline l
JOIN owners o ON o.owner_id=l.owner_id
WHERE o.active=true AND l.suppressed=false AND l.next_action_at < :as_of;
-- Reminder cooldown/delivery exclusion is added with Phase 3 automation storage.
SELECT reason, COUNT(*) AS row_count FROM import_rejections GROUP BY reason;
