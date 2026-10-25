-- PostgreSQL. Bind :as_of, :start, :end, :source (NULL means all sources).
-- Current record state evaluated at a fixed timestamp, not historical time travel.
WITH cohort AS (
 SELECT l.*,
   first_contacted_at IS NOT NULL AND first_contacted_at <= :as_of AS contacted,
   stage NOT IN ('Won','Lost') AND next_action_at IS NOT NULL AS scheduled,
   stage NOT IN ('Won','Lost') AND next_action_at < :as_of AS overdue,
   stage IN ('Qualified','Meeting','Proposal','Won') OR EXISTS (
      SELECT 1 FROM lead_status_history h WHERE h.lead_id=l.lead_id
      AND h.created_at <= :as_of
      AND h.details_json::jsonb ->> 'stage' IN ('Qualified','Meeting','Proposal','Won')
   ) AS qualified
 FROM v_analytics_leads l
 WHERE created_at >= :start AND created_at < :end AND created_at <= :as_of
   AND (CAST(:source AS text) IS NULL OR lead_source = :source)
)
SELECT count(*) AS new_leads,
 count(*) FILTER (WHERE contacted) AS contacted,
 count(*) FILTER (WHERE NOT contacted) AS uncontacted,
 count(*) FILTER (WHERE stage='Won') AS won,
 count(*) FILTER (WHERE qualified) AS qualified,
 count(*) FILTER (WHERE scheduled) AS active_scheduled,
 count(*) FILTER (WHERE overdue) AS overdue,
 count(*) FILTER (WHERE contacted)::double precision / NULLIF(count(*),0) AS first_response_coverage,
 count(*) FILTER (WHERE qualified)::double precision / NULLIF(count(*),0) AS qualified_rate,
 count(*) FILTER (WHERE stage='Won')::double precision / NULLIF(count(*),0) AS win_rate,
 count(*) FILTER (WHERE overdue)::double precision / NULLIF(count(*) FILTER (WHERE scheduled),0) AS overdue_rate,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY
   extract(epoch FROM (first_contacted_at::timestamptz-created_at::timestamptz))/3600)
   FILTER (WHERE contacted) AS median_first_response_hours,
 coalesce(sum(estimated_value_paise) FILTER (WHERE overdue),0)/100.0 AS pipeline_exposure_inr
FROM cohort;
