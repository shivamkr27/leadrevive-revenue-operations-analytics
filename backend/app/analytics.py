"""Frozen aggregate reporting, derived from canonical database records."""
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import timedelta
from pathlib import Path
from sqlalchemy import select, text
from backend.app import models as m
from backend.app.foundation import iso, dt, kpis
from backend.app.operations import settings
from backend.app.foundation import priority

ROOT = Path(__file__).resolve().parents[2]
FACT_FIELDS=('lead_id','origin','created_at','lead_source','campaign','stage','owner','owner_id',
    'estimated_value_inr','open','contacted','qualified','won','scheduled','overdue','next_action_at',
    'first_response_hours','response_sla_hours','sla_met','sla_breached','awaiting_within_sla',
    'pipeline_exposure_inr','priority_score','recovery_rule_eligible','cohort_kind')
KPI_FIELDS = ('new_leads','contacted','uncontacted','won','qualified','active_scheduled',
              'overdue','first_response_coverage','qualified_rate','win_rate',
              'overdue_rate','median_first_response_hours','pipeline_exposure_inr')


def sql_kpis(conn, as_of, start='1900-01-01T00:00:00Z', end='2100-01-01T00:00:00Z', source=None):
    if conn.dialect.name != 'postgresql':
        raise ValueError('Independent KPI query requires PostgreSQL.')
    return {k: float(v) if v is not None and k not in KPI_FIELDS[:7] else v
            for k,v in conn.execute(text((ROOT/'analytics/sql/kpi_snapshot.sql').read_text()),
            dict(as_of=iso(as_of),start=iso(start),end=iso(end),source=source)).mappings().one().items()}


def experiment(seed=42):
    """Comparable synthetic events; owner action and task effort are assumptions."""
    import random
    import time
    randomizer=random.Random(seed)
    events=[dict(lead_id=f'SIM-{i:03}',due_hour=randomizer.randrange(0,24),
                 owner=f'REP-{1+i%4}') for i in range(40)]
    began=time.perf_counter()
    # Twice-daily manual reviews versus an hourly scan. Same due events.
    rows=[]
    for event in events:
        manual_surface=12 if event['due_hour']<12 else 24
        automated_surface=event['due_hour']+1
        # Assumed two-hour owner response after surfacing, identical in both arms.
        rows.append(dict(**event,manual_surface_hour=manual_surface,
                         automation_surface_hour=automated_surface,
                         manual_action_hour=manual_surface+2,
                         automation_action_hour=automated_surface+2))
    elapsed=(time.perf_counter()-began)*1000
    horizon=24
    summary=[]
    for arm in ['manual','automation']:
        completed=sum(r[arm+'_action_hour']<=horizon for r in rows)
        surfaced=sum(r[arm+'_surface_hour']<=horizon for r in rows)
        summary.append(dict(arm=arm,cohort=40,surfaced=surfaced,followups_completed=completed,
                            overdue_remaining=40-completed,action_rate=completed/40,
                            timing_basis='MODELED hours; two-hour owner response assumed'))
    return dict(seed=seed,origin='SYNTHETIC SIMULATION',horizon_hours=horizon,
                assumptions='Manual reviews at hours 12 and 24; hourly automation scan; identical assumed two-hour owner response. No sales or revenue outcome modeled.',
                simulation_compute_ms=round(elapsed,3),rows=rows,summary=summary)


def build_snapshot(engine, as_of, start='1900-01-01T00:00:00Z', end='2100-01-01T00:00:00Z'):
    at=iso(as_of)
    if iso(start)>=iso(end):
        raise ValueError('start must be before end')
    # Prevent a scheduled job changing facts between independent calculations.
    if engine.dialect.name != 'postgresql':
        raise ValueError('Phase 4 canonical snapshot requires PostgreSQL.')
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as conn:
        sql=sql_kpis(conn,at,start,end)
        # kpis opens a connection itself, so bind to the same transactional connection.
        class Bound:
            def connect(self):
                from contextlib import nullcontext
                return nullcontext(conn)
        app=kpis(Bound(),at,start,end)
        for name in KPI_FIELDS:
            if app[name] is None or sql[name] is None:
                assert app[name] is sql[name], name
            else:
                assert abs(float(app[name])-float(sql[name]))<1e-8, (name,app[name],sql[name])
        leads=[dict(r) for r in conn.execute(select(m.leads).where(
            m.leads.c.created_at>=iso(start),m.leads.c.created_at<iso(end),m.leads.c.created_at<=at).order_by(m.leads.c.lead_id)).mappings()]
        owners={r['owner_id']:dict(r) for r in conn.execute(select(m.owners)).mappings()}
        weights=settings(conn)['scoring_weights']
        values=[r['estimated_value_paise'] for r in leads if r['stage'] not in ['Won','Lost']]
        facts=[]
        qualified_ids={r['lead_id'] for r in leads if r['stage'] in ['Qualified','Meeting','Proposal','Won']}
        for h in conn.execute(select(m.lead_status_history).where(m.lead_status_history.c.created_at<=at)).mappings():
            if json.loads(h['details_json']).get('stage') in ['Qualified','Meeting','Proposal','Won']:
                qualified_ids.add(h['lead_id'])
        for r in leads:
            opened=r['stage'] not in ['Won','Lost']
            contacted=bool(r['first_contacted_at'] and r['first_contacted_at']<=at)
            overdue=bool(opened and r['next_action_at'] and r['next_action_at']<at)
            response=(dt(r['first_contacted_at'])-dt(r['created_at'])).total_seconds()/3600 if contacted else None
            owner=owners.get(r['owner_id'],{})
            facts.append(dict(lead_id=r['lead_id'],origin='SYNTHETIC',created_at=r['created_at'],
                lead_source=r['lead_source'],campaign=r['campaign'],stage=r['stage'],
                owner=owner.get('name','Unassigned'),owner_id=r['owner_id'] or 'Unassigned',
                estimated_value_inr=r['estimated_value_paise']/100,open=int(opened),contacted=int(contacted),
                qualified=int(r['lead_id'] in qualified_ids),won=int(r['stage']=='Won'),
                scheduled=int(opened and bool(r['next_action_at'])),overdue=int(overdue),
                next_action_at=r['next_action_at'],first_response_hours=response,
                response_sla_hours=r['response_sla_hours'],
                sla_met=int(response<=r['response_sla_hours']) if contacted else 0,
                sla_breached=int(response>r['response_sla_hours']) if contacted else int(dt(at)>dt(r['created_at'])+timedelta(hours=r['response_sla_hours'])),
                awaiting_within_sla=int(not contacted and dt(at)<=dt(r['created_at'])+timedelta(hours=r['response_sla_hours'])),
                pipeline_exposure_inr=r['estimated_value_paise']/100 if overdue else 0,
                priority_score=priority(r,at,values,weights)['score'],
                recovery_rule_eligible=int(overdue and bool(owner.get('active')) and not r['suppressed'] and
                    not (r['last_contacted_at'] and r['last_contacted_at']>=r['next_action_at'])),
                cohort_kind='Seed dataset' if r['created_by']=='synthetic-generator' else 'Controlled fixture'))
        # All-time ledger counts at extraction, deliberately separate from lead cohort.
        runs=[dict(r) for r in conn.execute(select(m.automation_runs)).mappings()]
        deliveries=[dict(r) for r in conn.execute(select(m.notification_deliveries)).mappings()]
        audit=Counter(conn.execute(select(m.audit_events.c.event_type)).scalars())
        rejections=Counter(conn.execute(select(m.import_rejections.c.reason)).scalars())
        ops=dict(unique_automation_jobs=len(runs),recorded_job_attempts=sum(r['attempts'] for r in runs),
                 latest_succeeded_jobs=sum(r['status']=='succeeded' for r in runs),
                 latest_failed_jobs=sum(r['status'] in ['failed','partial'] for r in runs),
                 distinct_reminded_leads=conn.execute(text('SELECT COUNT(DISTINCT lead_id) FROM reminder_items')).scalar(),
                 reminder_items=conn.execute(text('SELECT COUNT(*) FROM reminder_items')).scalar(),
                 notification_drafts=conn.execute(text('SELECT COUNT(*) FROM notification_drafts')).scalar(),
                 sink_only_approvals=conn.execute(text('SELECT COUNT(*) FROM notification_approvals')).scalar(),
                 smtp_accepted_by_local_sink=sum(r['status']=='accepted' for r in deliveries),
                 sink_capture_verified=sum(bool(r['sink_message_id']) for r in deliveries),
                 accepted_after_retry=sum(r['status']=='accepted' and r['attempts']>1 for r in deliveries),
                 failed_or_uncertain_send_events=audit['sink_delivery_failed']+audit['sink_delivery_uncertain'],
                 cancelled_notifications=audit['notification_cancelled'],
                 external_live_delivery_enabled=False)
        workflow=[dict(workflow=w,status=s,jobs=sum(r['workflow']==w and r['status']==s for r in runs),
                       attempts=sum(r['attempts'] for r in runs if r['workflow']==w and r['status']==s))
                  for w,s in sorted({(r['workflow'],r['status']) for r in runs})]
        quality=[dict(reason=k,records=v,origin='SYNTHETIC') for k,v in sorted(rejections.items())]
    digest=hashlib.sha256(json.dumps(dict(as_of=at,facts=facts,operations=ops),sort_keys=True).encode()).hexdigest()
    def groups(field):
        result=[]
        for name in sorted({r[field] for r in facts}):
            subset=[r for r in facts if r[field]==name]
            result.append(dict(segment=name,leads=len(subset),**{k:sum(r[k] for r in subset) for k in
                ['open','contacted','qualified','won','scheduled','overdue','pipeline_exposure_inr','sla_met','sla_breached','awaiting_within_sla','recovery_rule_eligible']}))
        return result
    return dict(snapshot_id=digest[:16],as_of_utc=at,window_start=iso(start),window_end=iso(end),
                origin='SYNTHETIC',source='PostgreSQL repeatable-read extraction',
                interpretation='Current-state snapshot, not historical reconstruction. Estimated pipeline exposure is not recovered revenue. External live delivery disabled.',
                kpis={k:app[k] for k in KPI_FIELDS},sql_kpis=sql,facts=facts,
                sources=groups('lead_source'),owners=groups('owner'),stages=groups('stage'),
                operations=ops,workflow=workflow,quality=quality,experiment=experiment())


def csv_text(rows, fields=None):
    out=io.StringIO(newline='')
    fields=fields or (list(rows[0]) if rows else ['origin'])
    writer=csv.DictWriter(out,fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for k,v in row.items()})
    return out.getvalue()
