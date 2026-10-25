"""Local-only Phase 2 API and optional built React UI. Never sends email."""
import csv
import io
import json
import os
import tempfile
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, IntegrityError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from backend.app import models as m
from backend.app.foundation import engine_for, iso, kpis, import_csv, record_event, STAGES, OPEN, priority
from backend.app.operations import (OperationError, settings, lead_or_404, all_leads,
                                    decorate, edit_lead, add_activity, create_lead)

ROOT=Path(__file__).resolve().parents[2]
Stage=Literal['New','Contacted','Qualified','Meeting','Proposal','Won','Lost']


class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid')


class LeadEdit(StrictModel):
    version:int=Field(ge=1)
    stage:Stage|None=None
    owner_id:str|None=None
    next_action_at:str|None=None
    lost_reason:str|None=Field(default=None,max_length=500)
    suppressed:bool|None=None


class Activity(StrictModel):
    version:int=Field(ge=1)
    kind:Literal['contacted','note']
    note:str=Field(min_length=1,max_length=2000)


class NewLead(StrictModel):
    full_name:str=Field(min_length=1,max_length=120)
    company:str=Field(min_length=1,max_length=120)
    email:str=Field(max_length=254)
    phone:str=Field(max_length=80)
    lead_source:Literal['Web','Referral','Event','InboundEmail','Manual']='Manual'
    estimated_deal_value_inr:str
    owner_id:str|None=None
    next_action_at:str|None=None


class Review(StrictModel):
    decision:Literal['keep_existing','discard_invalid']
    note:str=Field(min_length=3,max_length=2000)


class SettingsEdit(StrictModel):
    version:int=Field(ge=1)
    response_sla_hours:int=Field(ge=1,le=720)
    scoring_weights:dict[str,float]


def csv_response(rows, fields, name):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        clean={key: ("'"+value if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r')) else value) for key,value in row.items()}
        writer.writerow(clean)
    return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{name}_SYNTHETIC.csv"'})


def create_app(database_url=None, fixed_now=None):
    engine=engine_for(database_url or os.environ.get('DATABASE_URL','sqlite:///data/processed/leadrevive.sqlite'))
    lock=threading.RLock()
    fixed_now=fixed_now or os.environ.get('LEADREVIVE_AS_OF')

    def now():
        return iso(fixed_now or datetime.now(timezone.utc).isoformat())

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app=FastAPI(title='LeadRevive Local Operations',version='0.5.0',lifespan=lifespan)
    from backend.app.analytics_api import router as analytics_router
    app.include_router(analytics_router)
    from backend.app.reports_api import create_router as reports_router
    app.include_router(reports_router(engine,now))
    app.state.engine=engine
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver','backend'])

    @app.middleware('http')
    async def local_origin(request, call_next):
        origin=request.headers.get('origin')
        if origin and origin not in [str(request.base_url).rstrip('/'),'http://127.0.0.1:5173','http://localhost:5173']:
            return JSONResponse({'detail':'Only the local application origin is allowed'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws://127.0.0.1:5173; frame-ancestors 'none'"
        if request.url.path in ['/docs','/redoc']:
            # FastAPI's built-in documentation loads its versioned Swagger/ReDoc assets
            # from jsDelivr and initializes them with an inline script.
            response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(OperationError)
    async def operation_error(request,exc):
        return JSONResponse({'detail':exc.message},status_code=exc.status)

    @app.exception_handler(ValueError)
    async def validation_error(request,exc):
        return JSONResponse({'detail':str(exc)},status_code=422)

    @app.exception_handler(OperationalError)
    async def database_unavailable(request,exc):
        return JSONResponse({'detail':'Database unavailable or migrations pending. Run scripts/seed_db.py and retry.'},status_code=503)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request,exc):
        return JSONResponse({'detail':'Data conflict; reload and review the current record.'},status_code=409)

    @app.get('/api/health')
    def health():
        with engine.connect() as conn:
            revision=conn.execute(text('SELECT version_num FROM alembic_version')).scalar()
        return dict(status='ok',database=engine.dialect.name,migration=revision,origin='SYNTHETIC',as_of_utc=now(),fixed_clock=bool(fixed_now))

    @app.get('/api/owners')
    def owners():
        with engine.connect() as conn:
            return [dict(r) for r in conn.execute(select(m.owners).where(m.owners.c.active.is_(True))).mappings()]

    @app.get('/api/analytics/kpis')
    def metrics(start:str='1900-01-01T00:00:00Z',end:str='2100-01-01T00:00:00Z',source:str|None=None):
        return kpis(engine,now(),start,end,source)

    @app.get('/api/overview')
    def overview(start:str='1900-01-01T00:00:00Z',end:str='2100-01-01T00:00:00Z',source:str|None=None):
        at=now()
        stats=kpis(engine,at,start,end,source)
        with engine.connect() as conn:
            rows=[r for r in all_leads(conn,at) if iso(start)<=r['created_at']<iso(end) and r['created_at']<=at and (not source or r['lead_source']==source)]
            quality=conn.execute(select(m.import_rejections.c.rejection_id)).scalars().all()
            reviewed=conn.execute(select(m.exception_reviews.c.rejection_id)).scalars().all()
        sources=[]
        for name in ['Web','Referral','Event','InboundEmail','Manual']:
            group=[r for r in rows if r['lead_source']==name]
            sources.append(dict(source=name,total=len(group),overdue=sum(r['overdue'] for r in group),
                won=sum(r['stage']=='Won' for r in group)))
        stages=[dict(stage=s,count=sum(r['stage']==s for r in rows)) for s in STAGES]
        unassigned=sum(not r['owner_id'] for r in rows if r['stage'] in OPEN)
        missing=sum(not r['next_action_at'] for r in rows if r['stage'] in OPEN)
        trend=[]
        anchor=datetime.fromisoformat(at.replace('Z','+00:00')).replace(hour=0,minute=0,second=0,microsecond=0)
        for index in reversed(range(8)):
            finish=anchor-timedelta(days=index*7)+timedelta(days=1)
            begin=finish-timedelta(days=7)
            trend.append(dict(week=begin.strftime('%d %b'),leads=sum(begin<=datetime.fromisoformat(r['created_at'].replace('Z','+00:00'))<finish for r in rows)))
        return dict(kpis=stats,sources=sources,stages=stages,trend=trend,unassigned=unassigned,
            missing_schedule=missing,unresolved_exceptions=len(set(quality)-set(reviewed)),
            urgent=sorted([r for r in rows if r['overdue']],key=lambda r:-r['priority']['score'])[:4])

    @app.get('/api/leads')
    def list_leads(q:str='',stage:str='',owner:str='',source:str='',priority_label:str='',
                   followup:Literal['','overdue','missing','scheduled']='',open_only:bool=True,
                   sort:Literal['priority','value','created','next_action']='priority',
                   page:int=Query(1,ge=1),page_size:int=Query(15,ge=1,le=100)):
        with engine.connect() as conn:
            rows=all_leads(conn,now())
        rows=[r for r in rows if (not open_only or r['stage'] in OPEN)
            and (not q or q.casefold() in ' '.join([r['full_name'],r['company'],r['email'],r['lead_id']]).casefold())
            and (not stage or r['stage']==stage)
            and (not owner or (not r['owner_id'] if owner=='unassigned' else r['owner_id']==owner))
            and (not source or r['lead_source']==source)
            and (not priority_label or r['priority_label']==priority_label)
            and (not followup or (r['overdue'] if followup=='overdue' else not r['next_action_at'] and r['stage'] in OPEN if followup=='missing' else bool(r['next_action_at']) and r['stage'] in OPEN and not r['overdue']))]
        rows.sort(key=lambda r:(-(r['priority']['score'] if r['priority'] else -1),r['lead_id']) if sort=='priority' else
                  (-r['estimated_value_paise'],r['lead_id']) if sort=='value' else
                  (r['created_at'],r['lead_id']) if sort=='created' else (r['next_action_at'] or '9999',r['lead_id']))
        return dict(items=rows[(page-1)*page_size:page*page_size],total=len(rows),page=page,page_size=page_size,as_of_utc=now())

    @app.get('/api/leads/export')
    def export_leads():
        with engine.connect() as conn:
            rows=all_leads(conn,now())
        for row in rows:
            row['origin']='SYNTHETIC'
        return csv_response(rows,['lead_id','company','full_name','email','stage','owner_id','next_action_at','estimated_deal_value_inr','origin'],'leads')

    @app.post('/api/leads/import')
    async def upload(file:UploadFile):
        content=await file.read(2_000_001)
        if len(content)>2_000_000:
            raise HTTPException(413,'CSV must be smaller than 2 MB')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.csv'
            path.write_bytes(content)
            with lock:
                return import_csv(engine,path,now())

    @app.post('/api/leads',status_code=201)
    def create(payload:NewLead):
        with lock, engine.begin() as conn:
            return create_lead(conn,payload.model_dump(),now())

    @app.get('/api/leads/{lead_id}')
    def detail(lead_id:str):
        with engine.connect() as conn:
            lead=lead_or_404(conn,lead_id)
            decorated=next(r for r in all_leads(conn,now()) if r['lead_id']==lead_id)
            timeline=[]
            for table in [m.lead_activities,m.audit_events,m.lead_status_history,m.lead_merge_audit]:
                for row in conn.execute(select(table).where(table.c.lead_id==lead_id)).mappings():
                    timeline.append(dict(row,category=table.name,details=json.loads(row['details_json'])))
            decorated['timeline']=sorted(timeline,key=lambda r:(r['created_at'],r['event_id']),reverse=True)
            return decorated

    @app.patch('/api/leads/{lead_id}')
    def edit(lead_id:str,payload:LeadEdit):
        changes=payload.model_dump(exclude_unset=True,exclude={'version'})
        for field in ['stage','suppressed']:
            if field in changes and changes[field] is None:
                raise HTTPException(422,field+' cannot be null')
        with lock, engine.begin() as conn:
            return edit_lead(conn,lead_id,payload.version,changes,now())

    @app.post('/api/leads/{lead_id}/activity')
    def activity(lead_id:str,payload:Activity):
        if not payload.note.strip():
            raise HTTPException(422,'Activity note cannot be blank')
        with lock, engine.begin() as conn:
            return add_activity(conn,lead_id,payload.version,payload.kind,payload.note.strip(),now())

    @app.get('/api/quality')
    def quality(status:Literal['all','pending','reviewed']='all'):
        with engine.connect() as conn:
            reviews={r['rejection_id']:dict(r) for r in conn.execute(select(m.exception_reviews)).mappings()}
            items=[]
            for row in conn.execute(select(m.import_rejections)).mappings():
                raw=json.loads(row['raw_json'])
                matches=conn.execute(select(m.leads.c.lead_id,m.leads.c.full_name,m.leads.c.company,m.leads.c.email,m.leads.c.phone).where(
                    (m.leads.c.lead_id==raw.get('lead_id')) | (m.leads.c.email==str(raw.get('email','')).strip().casefold()) | (m.leads.c.phone==raw.get('phone')))).mappings().all()
                items.append(dict(row,raw=raw,candidates=[dict(r) for r in matches],review=reviews.get(row['rejection_id'])))
            batches=[dict(r,summary=json.loads(r['summary_json'])) for r in conn.execute(select(m.import_batches).order_by(m.import_batches.c.created_at.desc())).mappings()]
        return dict(items=[r for r in items if status=='all' or bool(r['review'])==(status=='reviewed')],
                    total=len(items),pending=sum(not r['review'] for r in items),batches=batches)

    @app.get('/api/quality/export')
    def export_quality():
        with engine.connect() as conn:
            rows=[dict(r,origin='SYNTHETIC') for r in conn.execute(select(m.import_rejections)).mappings()]
        return csv_response(rows,['rejection_id','batch_id','row_number','reason','raw_json','origin'],'exceptions')

    @app.post('/api/quality/{rejection_id}/review')
    def review(rejection_id:str,payload:Review):
        if len(payload.note.strip())<3:
            raise HTTPException(422,'Review note is required')
        with lock,engine.begin() as conn:
            item=conn.execute(select(m.import_rejections).where(m.import_rejections.c.rejection_id==rejection_id)).mappings().first()
            if not item:
                raise HTTPException(404,'Exception not found')
            collision='duplicate' in item['reason'] or 'collision' in item['reason']
            if (payload.decision=='keep_existing')!=collision:
                raise HTTPException(422,'Choose keep existing for identity collisions, or discard invalid for validation errors')
            if conn.execute(select(m.exception_reviews).where(m.exception_reviews.c.rejection_id==rejection_id)).first():
                raise HTTPException(409,'Exception already reviewed; original decision is preserved')
            result=dict(rejection_id=rejection_id,decision=payload.decision,note=payload.note.strip(),reviewed_at=now())
            conn.execute(m.exception_reviews.insert().values(**result))
            record_event(conn,m.audit_events,None,'exception_reviewed',result,now())
        return result

    @app.get('/api/settings')
    def read_settings():
        with engine.connect() as conn:
            return settings(conn)

    @app.put('/api/settings')
    def write_settings(payload:SettingsEdit):
        dummy={'stage':'New','estimated_value_paise':0}
        priority(dummy,now(),[],payload.scoring_weights)
        with lock,engine.begin() as conn:
            before=settings(conn)
            if payload.version!=before['version']:
                raise HTTPException(409,'Settings changed; reload before saving')
            values=dict(response_sla_hours=payload.response_sla_hours,scoring_weights=payload.scoring_weights,settings_version=payload.version+1)
            for key,value in values.items():
                if conn.execute(select(m.config).where(m.config.c.key==key)).first():
                    conn.execute(m.config.update().where(m.config.c.key==key).values(value_json=json.dumps(value)))
                else:
                    conn.execute(m.config.insert().values(key=key,value_json=json.dumps(value)))
            record_event(conn,m.audit_events,None,'settings_updated',{'before':before,'after':values},now())
            return settings(conn)

    @app.get('/api/audit')
    def audit():
        with engine.connect() as conn:
            return [dict(r,details=json.loads(r['details_json'])) for r in conn.execute(select(m.audit_events).order_by(m.audit_events.c.created_at.desc()).limit(100)).mappings()]

    from backend.app.automation_api import build_router
    app.include_router(build_router(engine,now,lock))

    build=ROOT/'frontend/dist'
    if build.exists():
        app.mount('/assets',StaticFiles(directory=build/'assets'),name='assets')

        @app.get('/',include_in_schema=False)
        def index():
            return FileResponse(build/'index.html')
    return app
