"""Authenticated n8n integration and local operator notification controls."""
import hmac
import json
import os
from pathlib import Path
from typing import Literal
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from backend.app import models as m
from backend.app.automation import Automations
from backend.app.operations import OperationError


class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Job(Strict):
    idempotency_key:str=Field(min_length=1,max_length=150)
    execution_id:str|None=Field(default=None,max_length=100)
class Intake(Job):lead:dict
class Recovery(Job):lead_ids:list[str]|None=Field(default=None,max_length=1000)
class Dispatch(Job):
    draft_ids:list[str]|None=Field(default=None,max_length=50)
    force_retry:bool=False
class Synchronize(Job):
    lead_id:str
    version:int=Field(ge=1)
    changes:dict
class Approval(Strict):
    version:int=Field(ge=1)
    sink_only:Literal[True]
class Send(Job):mode:Literal['mailpit']='mailpit'
class Cancel(Strict):note:str=Field(min_length=3,max_length=500)


def build_router(engine,now,lock):
    router=APIRouter()
    service=Automations(engine)

    def wire(result):
        # n8n's retry-on-fail recognizes a top-level `error` item as a node error.
        # Business failures use status/failure_reason; HTTP/network errors still retry.
        result=dict(result)
        if 'error' in result:result['failure_reason']=result.pop('error')
        return result

    def authenticate(x_leadrevive_key:str=Header(default='')):
        secret=os.environ.get('LEADREVIVE_WEBHOOK_SECRET','')
        if not secret:raise HTTPException(503,'n8n shared credential is not configured')
        if not hmac.compare_digest(x_leadrevive_key,secret):raise HTTPException(401,'Invalid automation credential')

    @router.post('/api/integrations/n8n/intake',dependencies=[Depends(authenticate)])
    def intake(body:Intake):
        with lock:return wire(service.intake(body.idempotency_key,body.lead,now(),body.execution_id))

    @router.post('/api/integrations/n8n/recovery',dependencies=[Depends(authenticate)])
    def recovery(body:Recovery):
        with lock:return wire(service.recovery(body.idempotency_key,now(),body.execution_id,body.lead_ids))

    @router.post('/api/integrations/n8n/dispatch',dependencies=[Depends(authenticate)])
    def dispatch(body:Dispatch):
        with lock:return wire(service.dispatch(body.idempotency_key,now(),body.execution_id,body.draft_ids,body.force_retry))

    @router.post('/api/integrations/n8n/status-sync',dependencies=[Depends(authenticate)])
    def synchronize(body:Synchronize):
        from backend.app.api import LeadEdit
        payload=LeadEdit.model_validate(dict(body.changes,version=body.version))
        changes=payload.model_dump(exclude_unset=True,exclude={'version'})
        if any(key in changes and changes[key] is None for key in ['stage','suppressed']):
            raise HTTPException(422,'Stage and suppression cannot be null')
        with lock:return wire(service.sync(body.idempotency_key,body.lead_id,body.version,changes,now(),body.execution_id))

    def trigger(path,body):
        secret=os.environ.get('LEADREVIVE_WEBHOOK_SECRET','')
        base=os.environ.get('N8N_BASE_URL','http://127.0.0.1:5678')
        if base not in ('http://n8n:5678','http://127.0.0.1:5678','http://localhost:5678'):
            raise HTTPException(503,'Only local n8n is supported')
        if not secret:raise HTTPException(503,'n8n shared credential is not configured')
        try:
            response=httpx.post(base+'/webhook/leadrevive/'+path,json=body,
                headers={'X-LeadRevive-Key':secret},timeout=45)
            response.raise_for_status()
            result=response.json()
            if not isinstance(result,dict):raise ValueError('Unexpected n8n response')
            return result
        except (httpx.HTTPError,ValueError) as exc:
            def failed(conn,run_id,at):
                return dict(processed=0,skipped=0,failed=1,error='n8n request failed or timed out. Review workflow and delivery logs before retrying.')
            with lock:service.run('n8n_trigger',path+':'+body['idempotency_key'],{'path':path},now(),failed)
            raise HTTPException(503,'n8n workflow failed or is unavailable. No success is assumed; inspect runs and retry safely.') from exc

    @router.post('/api/automations/recovery')
    def trigger_recovery(body:Recovery):return trigger('recovery',body.model_dump(exclude_none=True))

    @router.post('/api/notifications/dispatch')
    def trigger_dispatch(body:Dispatch):return trigger('dispatch',body.model_dump(exclude_none=True))

    @router.get('/api/automations/status')
    def status():
        result={'external_email_enabled':False,'transport':'Mailpit only','dry_run':True,
                'database':engine.dialect.name,'services':{},'schedule':'Hourly recovery / five-minute outbox while n8n is running and workflows are published'}
        for name,url in [('n8n',os.environ.get('N8N_BASE_URL','http://127.0.0.1:5678')+'/healthz'),
                         ('mailpit',os.environ.get('MAILPIT_API_URL','http://127.0.0.1:8025')+'/api/v1/info')]:
            try:
                response=httpx.get(url,timeout=2)
                result['services'][name]={'reachable':response.status_code==200}
            except httpx.HTTPError:result['services'][name]={'reachable':False}
        return result

    @router.get('/api/automations/runs')
    def runs():
        with engine.connect() as conn:
            return [dict(r,result=json.loads(r['result_json'])) for r in conn.execute(
                select(m.automation_runs).order_by(m.automation_runs.c.started_at.desc()).limit(100)).mappings()]

    @router.get('/api/notifications')
    def notifications():
        with engine.connect() as conn:
            approvals={r['draft_id']:dict(r) for r in conn.execute(select(m.notification_approvals)).mappings()}
            deliveries={r['draft_id']:dict(r) for r in conn.execute(select(m.notification_deliveries)).mappings()}
            rows=[]
            for draft in conn.execute(select(m.notification_drafts).order_by(m.notification_drafts.c.created_at.desc()).limit(200)).mappings():
                live_reasons=['External sending is disabled in Phase 3']
                if draft['lead_id']:
                    lead=conn.execute(select(m.leads).where(m.leads.c.lead_id==draft['lead_id'])).mappings().one()
                    if not lead['consent_to_email']:live_reasons.append('Contact has not consented to external email')
                    if not lead['email_verified']:live_reasons.append('Contact email is not verified')
                    if lead['email'].endswith('.example') or lead['scenario_label']=='SYNTHETIC':live_reasons.append('Synthetic contacts are blocked from live email')
                rows.append(dict(draft,approval=approvals.get(draft['draft_id']),delivery=deliveries.get(draft['draft_id']),
                    context=json.loads(draft['context_json']),live_block_reasons=live_reasons))
            return rows

    @router.post('/api/leads/{lead_id}/email-draft')
    def preview(lead_id:str):
        with lock:return service.preview(lead_id,now())

    @router.post('/api/email-drafts/{draft_id}/approve')
    def approve(draft_id:str,body:Approval):
        with lock:return service.approve(draft_id,body.version,now())

    @router.post('/api/email-drafts/{draft_id}/send')
    def send(draft_id:str,body:Send):
        with engine.connect() as conn:
            draft=service._draft(conn,draft_id)
            if draft['status'] not in ['approved','failed','uncertain','sent_to_sink']:
                raise HTTPException(409,'Review and explicitly approve this Mailpit preview before requesting delivery')
        return trigger('dispatch',dict(idempotency_key=body.idempotency_key,draft_ids=[draft_id]))

    @router.post('/api/notifications/{draft_id}/cancel')
    def cancel(draft_id:str,body:Cancel):
        if len(body.note.strip())<3:raise HTTPException(422,'Explain the cancellation')
        with lock:return service.cancel(draft_id,body.note.strip(),now())

    @router.get('/api/automations/workflows/{name}')
    def download(name:Literal['intake','overdue_recovery','email_approval','status_sync']):
        from fastapi.responses import FileResponse
        root=Path(__file__).resolve().parents[2]
        return FileResponse(root/'automation/n8n/workflows'/f'{name}.json',media_type='application/json',filename=f'{name}.json')

    return router
