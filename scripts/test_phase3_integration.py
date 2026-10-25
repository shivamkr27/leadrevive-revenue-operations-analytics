"""Real n8n/PostgreSQL/Mailpit scenarios. Adds two clearly synthetic demo leads per run.

No SMTP mocks: Mailpit Chaos returns an actual SMTP 451, then a safe retry succeeds.
Original pre-migration rows are reconciled before/after. Never enables external email.
"""
import json
import argparse
from pathlib import Path
import sys
import time
from datetime import datetime,timezone,timedelta
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import httpx
from sqlalchemy import select,inspect
from scripts.local_config import local_config,postgres_url
from scripts.migrate_to_postgres import digest
from backend.app.foundation import engine_for,iso
from backend.app import models as m
from alembic.config import Config
from alembic.script import ScriptDirectory


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-qa',action='store_true');args=parser.parse_args()
    qa=ROOT/'data/processed/phase6_qa'
    key=uuid4().hex[:10]
    checks=[];evidence={'result':'running','scenario_key':key,'checks':checks}
    config=local_config() if not args.isolated_qa else dict(line.split('=',1) for line in (qa/'.env').read_text().splitlines() if '=' in line)
    headers={'X-LeadRevive-Key':config['LEADREVIVE_WEBHOOK_SECRET']}
    db=engine_for(postgres_url() if not args.isolated_qa else 'postgresql+psycopg://leadrevive:'+config['POSTGRES_PASSWORD']+'@127.0.0.1:15433/leadrevive')
    old=engine_for('sqlite:///'+(ROOT/'data/processed/leadrevive.sqlite').as_posix()) if not args.isolated_qa else db
    api_url='http://127.0.0.1:'+('18000' if args.isolated_qa else '8000')
    sink_url='http://127.0.0.1:'+('18025' if args.isolated_qa else '8025')
    n8n_url='http://127.0.0.1:'+('15678' if args.isolated_qa else '5678')
    original={}
    with old.connect() as conn:
        for table in m.metadata.sorted_tables:
            if table.name in inspect(old).get_table_names():
                original[table.name]=[dict(r) for r in conn.execute(select(table)).mappings()]
    def check(name,condition,detail=None):
        if not condition:raise AssertionError(name)
        checks.append({'name':name,'result':'passed','detail':detail})
        print('PASS:',name,flush=True)
    def verify_originals():
        with db.connect() as conn:
            for name,rows in original.items():
                table=m.metadata.tables[name];pk=list(table.primary_key.columns)[0].name
                ids={r[pk] for r in rows}
                current=[dict(r) for r in conn.execute(select(table)).mappings() if r[pk] in ids]
                if digest(rows)!=digest(current):raise AssertionError('Original records changed: '+name)
    with httpx.Client(base_url=api_url,timeout=50) as api, httpx.Client(base_url=sink_url,timeout=10) as sink:
        def workflow(path,body,expected=200):
            response=httpx.post(n8n_url+'/webhook/leadrevive/'+path,json=body,headers=headers,timeout=50)
            if response.status_code!=expected:raise AssertionError(f'{path}: HTTP {response.status_code}, expected {expected}; {response.text[:300]}')
            return response.json()
        def get_draft(draft_id):return next(r for r in api.get('/api/notifications').json() if r['draft_id']==draft_id)
        def captured(draft_id):
            response=sink.get('/api/v1/search',params={'query':'message-id:leadrevive-'+draft_id+'@leadrevive.test'})
            response.raise_for_status();return response.json().get('messages',[])
        try:
            health=api.get('/api/health').json()
            expected_head=ScriptDirectory.from_config(Config(str(ROOT/'alembic.ini'))).get_current_head()
            check('PostgreSQL health and Alembic head match',health['database']=='postgresql' and health['migration']==expected_head)
            verify_originals();check('Original baseline records match before scenarios',True)
            due=datetime.now(timezone.utc)+timedelta(seconds=8)
            payload=dict(full_name='Fictional Automation '+key,company='Synthetic Recovery Scenario '+key,
                email=f'recovery-{key}@scenario.example',phone='FICTIONAL-IN-RECOVERY-'+key,
                estimated_deal_value_inr='125000',next_action_at=iso(due.isoformat()))
            intake_body=dict(idempotency_key='scenario-intake-'+key,lead=payload)
            intake=workflow('intake',intake_body)
            evidence['recovery_lead_id']=intake['lead_id']
            check('W1 intake validates, persists, assigns owner and creates internal draft',intake['processed']==1 and len(intake['draft_ids'])==1,intake)
            replay=workflow('intake',intake_body)
            check('Repeated intake is idempotent',replay['replay'] and replay['lead_id']==intake['lead_id'])
            before=workflow('recovery',dict(idempotency_key='before-due-'+key,lead_ids=[intake['lead_id']]))
            check('Future follow-up produces no overdue reminder',before['processed']==0)
            delivered=workflow('dispatch',dict(idempotency_key='intake-sink-'+key,draft_ids=intake['draft_ids']))
            check('Internal notification reaches real Mailpit SMTP',delivered['processed']==1 and len(captured(intake['draft_ids'][0]))==1)
            wait=max(0,(due-datetime.now(timezone.utc)).total_seconds()+.3)
            if wait:time.sleep(wait)
            recovery=workflow('recovery',dict(idempotency_key='now-overdue-'+key,lead_ids=[intake['lead_id']]))
            with db.connect() as conn:
                planned=conn.execute(select(m.automation_runs).where(m.automation_runs.c.idempotency_key=='recovery:now-overdue-'+key)).mappings().one()
                planned_result=json.loads(planned['result_json'])
            evidence['recovery_draft_id']=planned_result['draft_ids'][0]
            check('A lead becoming overdue creates one owner digest and a real sink capture',planned['processed']==1 and planned_result['digests']==1 and recovery['processed']==1 and len(captured(evidence['recovery_draft_id']))==1,planned_result)
            again=workflow('recovery',dict(idempotency_key='cooldown-'+key,lead_ids=[intake['lead_id']]))
            check('Retry/new scan within cooldown creates no duplicate reminder',again['processed']==0 and len(captured(evidence['recovery_draft_id']))==1)
            lead=api.get('/api/leads/'+intake['lead_id']).json()
            completed=api.post('/api/leads/'+lead['lead_id']+'/activity',json=dict(version=lead['version'],kind='contacted',note='SYNTHETIC integration scenario: follow-up completed; review next action.'))
            completed.raise_for_status()
            after=workflow('recovery',dict(idempotency_key='after-completed-'+key,lead_ids=[lead['lead_id']]))
            check('Completed follow-up is excluded from further reminders',after['processed']==0 and completed.json()['last_contacted_at']>=lead['next_action_at'])
            lead=api.get('/api/leads/'+intake['lead_id']).json()
            synced=workflow('status-sync',dict(idempotency_key='close-scenario-'+key,lead_id=lead['lead_id'],version=lead['version'],changes={'stage':'Won'}))
            check('n8n versioned status sync updates DB and audit',synced['stage']=='Won' and api.get('/api/leads/'+lead['lead_id']).json()['stage']=='Won')
            workflow('status-sync',dict(idempotency_key='stale-sync-'+key,lead_id=lead['lead_id'],version=lead['version'],changes={'stage':'Lost','lost_reason':'Synthetic stale event'}),expected=500)
            check('Stale status event fails visibly and preserves latest state',api.get('/api/leads/'+lead['lead_id']).json()['stage']=='Won')
            approval_lead=api.post('/api/leads',json=dict(full_name='Fictional Approval '+key,company='Synthetic Approval Scenario '+key,
                email=f'approval-{key}@scenario.example',phone='FICTIONAL-IN-APPROVAL-'+key,owner_id='REP-2',estimated_deal_value_inr='75000')).json()
            evidence['approval_lead_id']=approval_lead['lead_id']
            preview=api.post('/api/leads/'+approval_lead['lead_id']+'/email-draft').json()
            evidence['approved_draft_id']=preview['draft_id']
            denied=api.post('/api/email-drafts/'+preview['draft_id']+'/send',json=dict(idempotency_key='unapproved-'+key,mode='mailpit'))
            live=api.post('/api/email-drafts/'+preview['draft_id']+'/send',json=dict(idempotency_key='live-'+key,mode='live'))
            check('Unapproved preview and all live-mode requests are blocked',denied.status_code==409 and live.status_code==422 and not captured(preview['draft_id']))
            approved=api.post('/api/email-drafts/'+preview['draft_id']+'/approve',json=dict(version=preview['version'],sink_only=True))
            approved.raise_for_status()
            sent=api.post('/api/email-drafts/'+preview['draft_id']+'/send',json=dict(idempotency_key='approved-send-'+key,mode='mailpit'))
            sent.raise_for_status()
            item=get_draft(preview['draft_id'])
            check('Exact-content approval controls real n8n/Mailpit preview delivery',item['approval']['approved_hash']==preview['content_hash'] and item['delivery']['status']=='accepted' and len(captured(preview['draft_id']))==1)
            api.post('/api/email-drafts/'+preview['draft_id']+'/send',json=dict(idempotency_key='approved-send-'+key,mode='mailpit')).raise_for_status()
            api.post('/api/email-drafts/'+preview['draft_id']+'/send',json=dict(idempotency_key='new-send-key-'+key,mode='mailpit')).raise_for_status()
            check('Repeated send requests cannot create a second sink email',len(captured(preview['draft_id']))==1)
            changed=api.patch('/api/leads/'+approval_lead['lead_id'],json=dict(version=approval_lead['version'],stage='Qualified'))
            changed.raise_for_status()
            second=api.post('/api/leads/'+approval_lead['lead_id']+'/email-draft').json()
            evidence['retry_draft_id']=second['draft_id']
            fault=sink.put('/api/v1/chaos',json={'Sender':{'ErrorCode':451,'Probability':100}});fault.raise_for_status()
            try:
                api.post('/api/email-drafts/'+second['draft_id']+'/approve',json=dict(version=second['version'],sink_only=True)).raise_for_status()
                workflow('dispatch',dict(idempotency_key='smtp-451-'+key,draft_ids=[second['draft_id']],force_retry=True),expected=500)
                failure=get_draft(second['draft_id'])
                evidence['smtp_failure']=failure['delivery']
                check('Actual SMTP 451 is logged as failure, not delivery',failure['delivery']['status']=='failed' and '451' in failure['delivery']['error'] and len(captured(second['draft_id']))==0,failure['delivery'])
            finally:
                sink.put('/api/v1/chaos',json={}).raise_for_status()
            retry_body=dict(idempotency_key='smtp-retry-'+key,draft_ids=[second['draft_id']],force_retry=True)
            retried=workflow('dispatch',retry_body)
            retry_replay=workflow('dispatch',retry_body)
            final=get_draft(second['draft_id'])
            evidence['smtp_retry']=final['delivery']
            check('Retry after recovery succeeds once; replay does not resend',retried['processed']==1 and retry_replay['replay'] and final['delivery']['attempts']==2 and len(captured(second['draft_id']))==1,final['delivery'])
            bad=httpx.post(n8n_url+'/webhook/leadrevive/recovery',json={'idempotency_key':'unauthorized'},headers={'X-LeadRevive-Key':'invalid'},timeout=10)
            check('n8n webhook authentication rejects wrong shared header',bad.status_code in [401,403])
            check('External sending remains disabled',api.get('/api/automations/status').json()['external_email_enabled'] is False)
            verify_originals();check('Original records/history still intact after real scenarios',True)
            evidence['result']='passed'
        finally:
            sink.put('/api/v1/chaos',json={})
            destination=ROOT/'data/processed'/('phase6_integration.json' if args.isolated_qa else 'phase3_integration.json')
            destination.write_text(json.dumps(evidence,indent=2))
            db.dispose();old.dispose()
    print(f"Real integration: {len(checks)} checks passed; evidence in {destination.relative_to(ROOT)}",flush=True)


if __name__=='__main__':main()
