-- All-time LOCAL SYNTHETIC TEST ledger, not production reliability.
-- Run status is latest state; attempts retains retries. A successful retry does
-- not erase earlier failures from audit_events. Some failures were induced.
SELECT workflow,status,count(*) AS unique_jobs,sum(attempts) AS recorded_attempts,
       sum(processed) AS latest_processed_total,sum(failed) AS latest_failed_total
FROM automation_runs GROUP BY workflow,status ORDER BY workflow,status;

SELECT count(*) AS reminder_items,count(DISTINCT lead_id) AS distinct_leads_surfaced,
       count(DISTINCT draft_id) AS grouped_reminders FROM reminder_items;

SELECT event_type,count(*) AS audit_events
FROM audit_events WHERE event_type IN ('sink_preview_approved','mailpit_smtp_accepted',
  'sink_delivery_failed','sink_delivery_uncertain','notification_cancelled','reminder_cancelled')
GROUP BY event_type ORDER BY event_type;

SELECT status,count(*) AS notification_ledgers,sum(attempts) AS logical_send_attempts,
 count(*) FILTER (WHERE status='accepted' AND attempts>1) AS accepted_after_retry,
 count(*) FILTER (WHERE sink_message_id IS NOT NULL) AS sink_capture_verified
FROM notification_deliveries GROUP BY status ORDER BY status;

-- No external delivery can be inferred from these tables. 'accepted' means
-- SMTP accepted by local Mailpit sink. Replay calls are not counted globally:
-- duplicate-send prevention is proven by scenario tests, not an invented KPI.
