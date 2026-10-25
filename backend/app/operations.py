"""Transactional local lead operations. No network/email/automation integration."""
import json
from uuid import uuid4
from sqlalchemy import select
from backend.app import models as m
from backend.app.foundation import OPEN, WEIGHTS, iso, dt, priority, sla_status, normalize, record_event


class OperationError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def settings(conn):
    stored = {r['key']:json.loads(r['value_json']) for r in conn.execute(select(m.config)).mappings()}
    return dict(response_sla_hours=stored.get('response_sla_hours',24),
                scoring_weights=stored.get('scoring_weights',WEIGHTS),
                version=stored.get('settings_version',1),dry_run=True,live_email_enabled=False)


def lead_or_404(conn, lead_id):
    lead = conn.execute(select(m.leads).where(m.leads.c.lead_id==lead_id)).mappings().first()
    if not lead:
        raise OperationError(404,'Lead not found')
    return dict(lead)


def decorate(lead, as_of, values, weights):
    result = dict(lead)
    result['priority'] = priority(lead,as_of,values,weights) if lead['stage'] in OPEN else None
    result['sla'] = sla_status(lead,as_of)
    result['overdue'] = lead['stage'] in OPEN and bool(lead['next_action_at'] and lead['next_action_at'] < iso(as_of))
    result['priority_label'] = ('High' if result['priority']['score']>=60 else 'Medium' if result['priority']['score']>=35 else 'Low') if result['priority'] else 'Closed'
    result['estimated_deal_value_inr']=lead['estimated_value_paise']/100
    result['recommended_action'] = ('Assign an owner' if not lead['owner_id'] else
        'Schedule a next action' if not lead['next_action_at'] and lead['stage'] in OPEN else
        'Complete overdue follow-up' if result['overdue'] else 'Review scheduled follow-up') if lead['stage'] in OPEN else 'Closed opportunity'
    return result


def all_leads(conn, now):
    rows=conn.execute(select(m.leads)).mappings().all()
    values=[r['estimated_value_paise'] for r in rows if r['stage'] in OPEN]
    weights=settings(conn)['scoring_weights']
    return [decorate(r,now,values,weights) for r in rows]


def edit_lead(conn, lead_id, version, changes, now):
    before=lead_or_404(conn,lead_id)
    if before['version']!=version:
        raise OperationError(409,'This lead changed. Reload the lead before saving.')
    if changes.get('lost_reason'):
        changes['lost_reason']=changes['lost_reason'].strip()
    if changes.get('stage',before['stage'])=='Lost' and not changes.get('lost_reason',before['lost_reason']):
        raise OperationError(422,'A lost reason is required for Lost leads')
    if changes.get('owner_id'):
        owner=conn.execute(select(m.owners).where(m.owners.c.owner_id==changes['owner_id'],m.owners.c.active.is_(True))).first()
        if not owner:
            raise OperationError(422,'Select an active owner')
    if changes.get('next_action_at'):
        changes['next_action_at']=iso(changes['next_action_at'])
        if changes['next_action_at'] < before['created_at']:
            raise OperationError(422,'Next action cannot predate lead creation')
    if changes.get('stage',before['stage'])!='Lost':
        changes['lost_reason']=None
    changed={k:v for k,v in changes.items() if v!=before[k]}
    if not changed:
        return before
    changes=dict(changed,updated_at=now,version=version+1)
    result=conn.execute(m.leads.update().where(m.leads.c.lead_id==lead_id,m.leads.c.version==version).values(**changes))
    if result.rowcount!=1:
        raise OperationError(409,'Concurrent edit detected; reload and retry')
    detail=dict(before={k:before[k] for k in changed},after=changed,actor='local-user')
    record_event(conn,m.audit_events,lead_id,'lead_updated',detail,now)
    record_event(conn,m.lead_activities,lead_id,'lead_updated',detail,now)
    if 'stage' in changed:
        record_event(conn,m.lead_status_history,lead_id,'stage_changed',{'stage':changed['stage'],'previous':before['stage']},now)
    return lead_or_404(conn,lead_id)


def add_activity(conn, lead_id, version, kind, note, now):
    lead=lead_or_404(conn,lead_id)
    if version!=lead['version']:
        raise OperationError(409,'This lead changed. Reload before adding activity.')
    changes=dict(updated_at=now,version=version+1)
    if kind=='contacted':
        if lead['stage'] not in OPEN:
            raise OperationError(422,'Closed leads cannot be marked contacted')
        changes.update(last_contacted_at=now)
        if not lead['first_contacted_at']:
            changes['first_contacted_at']=now
        if lead['stage']=='New':
            changes['stage']='Contacted'
            record_event(conn,m.lead_status_history,lead_id,'stage_changed',{'stage':'Contacted','previous':'New'},now)
    result=conn.execute(m.leads.update().where(m.leads.c.lead_id==lead_id,m.leads.c.version==version).values(**changes))
    if result.rowcount!=1:
        raise OperationError(409,'Concurrent edit detected')
    details=dict(note=note,actor='local-user',before={k:lead[k] for k in changes},after=changes)
    record_event(conn,m.lead_activities,lead_id,kind,details,now)
    record_event(conn,m.audit_events,lead_id,kind,details,now)
    return lead_or_404(conn,lead_id)


def create_lead(conn, payload, now, actor='local-user'):
    lead_id='SYN-'+uuid4().hex[:12].upper()
    raw=dict(lead_id=lead_id,created_at=now,updated_at=now,
        campaign='SYNTHETIC Manual entry',industry='Professional Services',company_size='11-50',
        stage='New',created_by=actor,scenario_label='SYNTHETIC',
        consent_to_email='false',email_verified='false',
        response_sla_hours=settings(conn)['response_sla_hours'],**payload)
    row, errors=normalize(raw)
    if not row['email'].endswith('.example') or not row['phone'].startswith('FICTIONAL-IN-'):
        errors.append('Manual demo records require .example email and FICTIONAL-IN- phone')
    if errors:
        raise OperationError(422,'; '.join(errors))
    matches=conn.execute(select(m.leads.c.lead_id).where(
        (m.leads.c.email==row['email']) | (m.leads.c.phone==row['phone']))).scalars().all()
    if matches:
        raise OperationError(409,'Email or phone already exists. Use the existing lead or CSV conflict review.')
    if row['owner_id'] and not conn.execute(select(m.owners).where(m.owners.c.owner_id==row['owner_id'],m.owners.c.active.is_(True))).first():
        raise OperationError(422,'Select an active owner')
    conn.execute(m.leads.insert().values(**row))
    for table,kind in [(m.lead_activities,'created'),(m.audit_events,'lead_created'),(m.lead_status_history,'initial_stage')]:
        record_event(conn,table,lead_id,kind,{'stage':'New','actor':actor},now)
    return row
