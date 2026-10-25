-- PostgreSQL 16. Bind :as_of (canonical six-digit UTC ISO text).
-- These current-state views do not reconstruct past owner/stage changes.

-- 1. Funnel: stage distribution and cohort outcome counts are different concepts.
SELECT lead_source, stage, count(*) AS leads,
       sum(estimated_value_paise)/100.0 AS estimated_value_inr
FROM v_analytics_leads WHERE created_at <= :as_of
GROUP BY lead_source,stage ORDER BY lead_source,stage;

-- 2. Owner workload and unscheduled work, including unassigned leads.
SELECT coalesce(owner_name,'Unassigned') AS owner,
       count(*) FILTER (WHERE is_open=1) AS open_leads,
       count(*) FILTER (WHERE is_open=1 AND next_action_at IS NULL) AS missing_schedule,
       count(*) FILTER (WHERE is_open=1 AND next_action_at IS NOT NULL) AS scheduled,
       count(*) FILTER (WHERE is_open=1 AND next_action_at < :as_of) AS overdue,
       coalesce(sum(estimated_value_paise) FILTER (WHERE is_open=1 AND next_action_at < :as_of),0)/100.0 AS pipeline_exposure_inr
FROM v_analytics_leads WHERE created_at <= :as_of
GROUP BY coalesce(owner_name,'Unassigned') ORDER BY overdue DESC,owner;

-- 3. SLA: contacted-only timing plus uncontacted elapsed-hour breaches.
SELECT lead_source,
 count(*) AS leads,
 count(*) FILTER (WHERE first_contacted_at <= :as_of) AS contacted,
 count(*) FILTER (WHERE first_contacted_at <= :as_of AND
     first_contacted_at::timestamptz <= created_at::timestamptz + response_sla_hours*interval '1 hour') AS met,
 count(*) FILTER (WHERE
    (first_contacted_at <= :as_of AND first_contacted_at::timestamptz > created_at::timestamptz + response_sla_hours*interval '1 hour')
    OR ((first_contacted_at IS NULL OR first_contacted_at > :as_of)
     AND CAST(:as_of AS timestamptz)>created_at::timestamptz+response_sla_hours*interval '1 hour')) AS breached,
 percentile_cont(.5) WITHIN GROUP (ORDER BY
    extract(epoch FROM (first_contacted_at::timestamptz-created_at::timestamptz))/3600)
 FILTER (WHERE first_contacted_at <= :as_of) AS median_contacted_hours
FROM v_analytics_leads WHERE created_at <= :as_of
GROUP BY lead_source ORDER BY lead_source;

-- 4. Recovery candidates after pending reservations and rolling cooldown.
-- :cooldown_hours is the configured value. Display order uses overdue time/value;
-- the app's 0-100 priority formula is documented separately and exported in facts.
SELECT l.lead_id,l.owner_name,l.lead_source,l.next_action_at,l.estimated_value_paise/100.0 AS estimated_value_inr
FROM v_analytics_leads l
WHERE created_at <= :as_of AND is_open=1 AND owner_active=1
 AND NOT suppressed AND next_action_at < :as_of
 AND (last_contacted_at IS NULL OR last_contacted_at < next_action_at)
 AND NOT EXISTS (SELECT 1 FROM reminder_items r WHERE r.lead_id=l.lead_id AND
   (r.status='pending' OR (r.status='sent' AND r.sent_at::timestamptz>
      CAST(:as_of AS timestamptz)-CAST(:cooldown_hours AS integer)*interval '1 hour')))
ORDER BY l.next_action_at,l.estimated_value_paise DESC,l.lead_id;

-- 5. Reason-level quality evidence: exact repeats are preserved, conflicts reviewed.
SELECT reason,count(*) AS records FROM import_rejections GROUP BY reason ORDER BY reason;

-- 6. Lost reasons identify data gaps as well as declared reasons.
SELECT coalesce(nullif(lost_reason,''),'Not recorded') AS lost_reason,count(*) AS leads
FROM leads WHERE stage='Lost' AND created_at <= :as_of
GROUP BY coalesce(nullif(lost_reason,''),'Not recorded') ORDER BY leads DESC;
