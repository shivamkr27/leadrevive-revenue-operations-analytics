"""Database-backed recovery, immutable approvals and Mailpit-only SMTP outbox.

n8n orchestrates these services. No generic/live SMTP transport exists.
"""
import hashlib
import json
import os
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from uuid import uuid4,uuid5,NAMESPACE_URL

import httpx
from sqlalchemy import select,text
from backend.app import models as m
from backend.app.foundation import iso,dt,OPEN,record_event
from backend.app.operations import OperationError,all_leads,lead_or_404,create_lead,edit_lead


def hashed(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def atomic(conn):
    # One transaction-scoped lock coordinates reminders/outbox across PostgreSQL workers.
    if conn.dialect.name=='postgresql':
        conn.execute(text('SELECT pg_advisory_xact_lock(72401983)'))


class SinkUnavailable(Exception):pass
class UncertainAcceptance(Exception):pass


class MailpitTransport:
    def __init__(self):
        self.host=os.environ.get('MAILPIT_SMTP_HOST','127.0.0.1')
        self.port=int(os.environ.get('MAILPIT_SMTP_PORT','1025'))
        self.api=os.environ.get('MAILPIT_API_URL','http://127.0.0.1:8025')
        if self.host not in ('mailpit','127.0.0.1','localhost') or self.port!=1025 or self.api not in (
            'http://mailpit:8025','http://127.0.0.1:8025','http://localhost:8025'):
            raise RuntimeError('Only the local Mailpit sink is permitted. External transport is not implemented.')

    def lookup(self,message_id):
        try:
            response=httpx.get(self.api+'/api/v1/search',params={'query':'message-id:'+message_id},timeout=5)
            response.raise_for_status()
            matches=response.json().get('messages',[])
            return matches[0]['ID'] if matches else None
        except (httpx.HTTPError,ValueError,KeyError) as exc:
            raise SinkUnavailable('Mailpit verification API unavailable; no SMTP send attempted.') from exc

    def send(self,draft,message_id):
        if not draft['sink_recipient'].endswith('@leadrevive.test'):
            raise OperationError(422,'Sink envelope must use a reserved leadrevive.test mailbox')
        message=EmailMessage()
        message['From']='LeadRevive Local Test <notifications@leadrevive.test>'
        message['To']=draft['sink_recipient']
        message['Subject']=draft['subject']
        message['Message-ID']='<'+message_id+'>'
        message['X-LeadRevive-Draft']=draft['draft_id']
        message['X-LeadRevive-Mode']='SYNTHETIC-MAILPIT-ONLY'
        message['X-Intended-Recipient']=draft['intended_recipient']
        message.set_content('SYNTHETIC / LOCAL MAILPIT TEST ONLY\nNo external delivery is enabled.\n\n'+draft['body'])
        try:
            client=smtplib.SMTP(self.host,self.port,timeout=5)
        except (OSError,smtplib.SMTPException) as exc:
            raise SinkUnavailable('Mailpit SMTP connection failed before transmission.') from exc
        try:
            client.send_message(message)
        except (smtplib.SMTPRecipientsRefused,smtplib.SMTPSenderRefused,smtplib.SMTPDataError) as exc:
            code=getattr(exc,'smtp_code',None)
            if code is None and isinstance(exc,smtplib.SMTPRecipientsRefused):
                code=next(iter(exc.recipients.values()))[0]
            raise SinkUnavailable(f'Mailpit SMTP rejected the test message ({code or "SMTP error"}).') from exc
        except (OSError,smtplib.SMTPException) as exc:
            raise UncertainAcceptance('SMTP acknowledgement uncertain; reconcile Mailpit before any retry.') from exc
        finally:
            # Once DATA is accepted, a disconnect on QUIT does not mean delivery failed.
            try:client.quit()
            except (OSError,smtplib.SMTPException):client.close()


def content_hash(draft):
    return hashed({key:draft[key] for key in ['kind','intended_recipient','sink_recipient','subject','body','context_json']})


def make_draft(conn,kind,key,now,subject,body,context,run_id=None,lead_id=None,owner_id=None,intended=None):
    draft_id=str(uuid5(NAMESPACE_URL,'leadrevive:'+key))
    old=conn.execute(select(m.notification_drafts).where(m.notification_drafts.c.draft_id==draft_id)).mappings().first()
    if old:return dict(old)
    row=dict(draft_id=draft_id,kind=kind,run_id=run_id,lead_id=lead_id,owner_id=owner_id,
        intended_recipient=intended or f'{owner_id.lower()}@internal.leadrevive.example',
        sink_recipient='approved-preview@leadrevive.test' if kind=='external_preview' else f'{owner_id.lower()}@leadrevive.test',
        subject=subject,body=body,context_json=json.dumps(context,sort_keys=True),version=1,
        created_at=now,updated_at=now,status='pending_approval' if kind=='external_preview' else 'queued')
    row['content_hash']=content_hash(row)
    conn.execute(m.notification_drafts.insert().values(**row))
    record_event(conn,m.audit_events,lead_id,'notification_draft_created',{'draft_id':draft_id,'kind':kind,'mode':'mailpit_only'},now)
    return row


def eligible(lead,now):
    return lead['stage'] in OPEN and bool(lead['owner_id']) and not lead['suppressed'] and bool(
        lead['next_action_at'] and lead['next_action_at']<now) and not bool(
        lead['last_contacted_at'] and lead['last_contacted_at']>=lead['next_action_at'])


def prune_items(conn,now):
    rows=conn.execute(select(m.reminder_items).where(m.reminder_items.c.status=='pending')).mappings().all()
    for item in rows:
        lead=lead_or_404(conn,item['lead_id'])
        if not eligible(lead,now) or lead['owner_id']!=item['owner_id'] or lead['next_action_at']!=item['next_action_at']:
            conn.execute(m.reminder_items.update().where(m.reminder_items.c.item_id==item['item_id']).values(status='cancelled'))
            record_event(conn,m.audit_events,lead['lead_id'],'reminder_cancelled',{'draft_id':item['draft_id'],'reason':'lead completed, closed, reassigned, suppressed or rescheduled'},now)


class Automations:
    def __init__(self,engine,transport=None):
        self.engine=engine
        self.transport=transport or MailpitTransport()

    def run(self,workflow,key,payload,now,callback,execution_id=None):
        now=iso(now)
        business_key=workflow+':'+key
        request_hash=hashed(payload)
        with self.engine.begin() as conn:
            atomic(conn)
            old=conn.execute(select(m.automation_runs).where(m.automation_runs.c.idempotency_key==business_key)).mappings().first()
            if old:
                if old['payload_hash']!=request_hash:
                    raise OperationError(409,'Idempotency key reused with a different payload')
                previous=json.loads(old['result_json'])
                if old['status']=='succeeded' or previous.get('permanent'):
                    return dict(previous,run_id=old['run_id'],status=old['status'],replay=True)
                run_id=old['run_id'];attempts=old['attempts']+1
                conn.execute(m.automation_runs.update().where(m.automation_runs.c.run_id==run_id).values(status='running',attempts=attempts,execution_id=execution_id,started_at=now))
            else:
                run_id=str(uuid4());attempts=1
                conn.execute(m.automation_runs.insert().values(run_id=run_id,workflow=workflow,
                    idempotency_key=business_key,payload_hash=request_hash,execution_id=execution_id,
                    status='running',started_at=now,completed_at=None,attempts=1,processed=0,skipped=0,
                    failed=0,result_json='{}',error=None))
            try:
                with conn.begin_nested():
                    result=callback(conn,run_id,now)
            except Exception as exc:
                result=dict(processed=0,skipped=0,failed=1,error=exc.message if isinstance(exc,OperationError) else f'Operation failed ({type(exc).__name__}).')
            status='partial' if result.get('failed') and result.get('processed') else 'failed' if result.get('failed') else 'succeeded'
            result=dict(result,run_id=run_id,status=status,replay=False,attempts=attempts)
            conn.execute(m.automation_runs.update().where(m.automation_runs.c.run_id==run_id).values(
                status=status,completed_at=now,processed=result.get('processed',0),skipped=result.get('skipped',0),
                failed=result.get('failed',0),result_json=json.dumps(result),error=result.get('error')))
            record_event(conn,m.audit_events,None,'automation_'+status,{'run_id':run_id,'workflow':workflow,'execution_id':execution_id,'attempt':attempts},now)
            return result

    def intake(self,key,payload,now,execution_id=None):
        def action(conn,run_id,at):
            from backend.app.api import NewLead
            from pydantic import ValidationError
            try:
                with conn.begin_nested():
                    data=NewLead.model_validate(payload).model_dump()
                    if not data['owner_id']:
                        active=conn.execute(select(m.owners.c.owner_id).where(m.owners.c.active.is_(True)).order_by(m.owners.c.owner_id)).scalars().all()
                        if not active:raise OperationError(422,'No active owner available')
                        config=conn.execute(select(m.config).where(m.config.c.key=='assignment_cursor')).mappings().first()
                        cursor=json.loads(config['value_json']) if config else 0
                        data['owner_id']=active[cursor%len(active)]
                        if config:conn.execute(m.config.update().where(m.config.c.key=='assignment_cursor').values(value_json=json.dumps(cursor+1)))
                        else:conn.execute(m.config.insert().values(key='assignment_cursor',value_json=json.dumps(cursor+1)))
                    lead=create_lead(conn,data,at,actor='n8n-intake')
            except (OperationError,ValidationError) as exc:
                reason=exc.message if isinstance(exc,OperationError) else 'Webhook validation: '+str(exc)
                collision=isinstance(exc,OperationError) and exc.status==409
                reason=('identity collision; manual review required: ' if collision else 'Webhook validation error: ')+reason
                batch_id=str(uuid5(NAMESPACE_URL,'leadrevive-intake:'+key))
                summary=dict(accepted=0,invalid=int(not collision),duplicates=0,review_required=int(collision))
                conn.execute(m.import_batches.insert().values(batch_id=batch_id,sha256=hashed({'webhook_key':key}),created_at=at,summary_json=json.dumps(summary)))
                conn.execute(m.import_rejections.insert().values(rejection_id=str(uuid4()),batch_id=batch_id,row_number=1,reason=reason,raw_json=json.dumps(payload)))
                return dict(processed=0,skipped=0,failed=1,error=reason,permanent=True)
            draft=make_draft(conn,'internal_intake','intake:'+key,at,
                '[SYNTHETIC] New lead assigned: '+lead['company'],
                f"New lead {lead['lead_id']} / {lead['company']} is assigned to {lead['owner_id']}. Review response SLA and schedule the first action.",
                {'lead_version':lead['version']},run_id,lead['lead_id'],lead['owner_id'])
            return dict(processed=1,skipped=0,failed=0,lead_id=lead['lead_id'],draft_ids=[draft['draft_id']])
        return self.run('intake',key,payload,now,action,execution_id)

    def recovery(self,key,now,execution_id=None,lead_ids=None):
        def action(conn,run_id,at):
            prune_items(conn,at)
            rows=all_leads(conn,at)
            if lead_ids is not None:rows=[r for r in rows if r['lead_id'] in lead_ids]
            active=set(conn.execute(select(m.owners.c.owner_id).where(m.owners.c.active.is_(True))).scalars())
            setting=conn.execute(select(m.config.c.value_json).where(m.config.c.key=='reminder_cooldown_hours')).scalar()
            cutoff=iso((dt(at)-timedelta(hours=json.loads(setting) if setting else 24)).isoformat())
            grouped={};skipped=0
            for lead in rows:
                if not eligible(lead,at) or lead['owner_id'] not in active:
                    skipped+=1;continue
                reminders=conn.execute(select(m.reminder_items).where(m.reminder_items.c.lead_id==lead['lead_id'])).mappings().all()
                if any(r['status']=='pending' or r['status']=='sent' and r['sent_at'] and r['sent_at']>cutoff for r in reminders):
                    skipped+=1;continue
                grouped.setdefault(lead['owner_id'],[]).append(lead)
            draft_ids=[];processed=0
            for owner,leads in sorted(grouped.items()):
                leads.sort(key=lambda r:-r['priority']['score'])
                body='Owner '+owner+' — overdue recovery digest\n\n'+'\n'.join(
                    f"{r['lead_id']} | {r['company']} | priority {r['priority']['score']} | action: {r['recommended_action']}" for r in leads)
                draft=make_draft(conn,'internal_digest',f'digest:{run_id}:{owner}',at,
                    f'[SYNTHETIC] {len(leads)} overdue follow-ups for {owner}',body,{'lead_ids':[r['lead_id'] for r in leads]},run_id,owner_id=owner)
                for lead in leads:
                    conn.execute(m.reminder_items.insert().values(item_id=str(uuid4()),draft_id=draft['draft_id'],
                        lead_id=lead['lead_id'],owner_id=owner,next_action_at=lead['next_action_at'],
                        contact_snapshot=lead['last_contacted_at'],status='pending',created_at=at,sent_at=None))
                    record_event(conn,m.lead_activities,lead['lead_id'],'reminder_queued',{'draft_id':draft['draft_id'],'owner':owner,'priority':lead['priority']['score']},at)
                processed+=len(leads);draft_ids.append(draft['draft_id'])
            return dict(processed=processed,skipped=skipped,failed=0,draft_ids=draft_ids,digests=len(draft_ids))
        return self.run('recovery',key,{'lead_ids':lead_ids},now,action,execution_id)

    def preview(self,lead_id,now):
        now=iso(now)
        with self.engine.begin() as conn:
            atomic(conn)
            lead=lead_or_404(conn,lead_id)
            if lead['stage'] not in OPEN or lead['suppressed']:
                raise OperationError(422,'Closed or suppressed leads cannot receive a follow-up draft')
            body=f"Hello {lead['full_name']},\n\nFollowing up on your enquiry from {lead['company']}. Would you like to arrange a short discussion about your requirements?\n\nRegards,\nLeadRevive demo team\n\nSYNTHETIC PREVIEW — not sent to this contact."
            return make_draft(conn,'external_preview',f"preview:{lead_id}:{lead['version']}",now,
                '[SYNTHETIC PREVIEW] Follow-up for '+lead['company'],body,{'lead_version':lead['version']},lead_id=lead_id,intended=lead['email'])

    def approve(self,draft_id,version,now):
        now=iso(now)
        with self.engine.begin() as conn:
            atomic(conn)
            draft=self._draft(conn,draft_id)
            if draft['version']!=version:raise OperationError(409,'Draft version changed; reload preview')
            if draft['kind']!='external_preview':raise OperationError(422,'Internal tasks do not use external-preview approval')
            lead=lead_or_404(conn,draft['lead_id'])
            if lead['version']!=json.loads(draft['context_json'])['lead_version'] or lead['stage'] not in OPEN or lead['suppressed']:
                raise OperationError(409,'Lead changed; prepare and review a fresh draft')
            if draft['status']!='pending_approval':raise OperationError(409,'Draft is already approved, sent or no longer pending')
            if content_hash(draft)!=draft['content_hash']:raise OperationError(409,'Draft content changed; create a fresh preview')
            conn.execute(m.notification_approvals.insert().values(approval_id=str(uuid4()),draft_id=draft_id,
                approved_hash=draft['content_hash'],approved_by='local-user',approved_at=now,mode='mailpit_only'))
            conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft_id).values(status='approved',updated_at=now))
            record_event(conn,m.audit_events,draft['lead_id'],'sink_preview_approved',{'draft_id':draft_id,'content_hash':draft['content_hash'],'mode':'mailpit_only'},now)
            return self._draft(conn,draft_id)

    def _draft(self,conn,draft_id):
        row=conn.execute(select(m.notification_drafts).where(m.notification_drafts.c.draft_id==draft_id)).mappings().first()
        if not row:raise OperationError(404,'Notification draft not found')
        return dict(row)

    def cancel(self,draft_id,note,now):
        now=iso(now)
        with self.engine.begin() as conn:
            atomic(conn)
            draft=self._draft(conn,draft_id)
            if draft['status']=='sent_to_sink':raise OperationError(409,'An accepted sink message cannot be cancelled retroactively')
            if draft['status']=='cancelled':return draft
            conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft_id).values(status='cancelled',updated_at=now))
            conn.execute(m.reminder_items.update().where(m.reminder_items.c.draft_id==draft_id,m.reminder_items.c.status=='pending').values(status='cancelled'))
            record_event(conn,m.audit_events,draft['lead_id'],'notification_cancelled',{'draft_id':draft_id,'note':note,'actor':'local-user'},now)
            return self._draft(conn,draft_id)

    def _deliver(self,conn,draft,at,force_retry):
        delivery=conn.execute(select(m.notification_deliveries).where(m.notification_deliveries.c.draft_id==draft['draft_id'])).mappings().first()
        if delivery and delivery['status']=='accepted':return 'replay'
        if draft['status'] in ('cancelled','stale'):return 'skipped'
        if draft['kind']=='external_preview':
            approval=conn.execute(select(m.notification_approvals).where(m.notification_approvals.c.draft_id==draft['draft_id'])).mappings().first()
            if not approval or approval['mode']!='mailpit_only' or approval['approved_hash']!=content_hash(draft):
                return 'unapproved'
            lead=lead_or_404(conn,draft['lead_id'])
            if lead['version']!=json.loads(draft['context_json'])['lead_version'] or lead['stage'] not in OPEN or lead['suppressed']:
                conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(status='stale',updated_at=at))
                return 'skipped'
        elif draft['kind']=='internal_digest':
            items=conn.execute(select(m.reminder_items).where(m.reminder_items.c.draft_id==draft['draft_id'],m.reminder_items.c.status=='pending')).mappings().all()
            if not items:
                conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(status='cancelled',updated_at=at))
                return 'skipped'
            draft=dict(draft,subject=f"[SYNTHETIC] {len(items)} overdue follow-ups for {draft['owner_id']}",
                body='Owner '+draft['owner_id']+' — current overdue recovery digest\n\n'+'\n'.join(
                    f"{r['lead_id']} | {lead_or_404(conn,r['lead_id'])['company']} | next action {r['next_action_at']}" for r in items))
            draft['context_json']=json.dumps({'lead_ids':[r['lead_id'] for r in items]},sort_keys=True)
            draft['content_hash']=content_hash(draft)
            conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(
                subject=draft['subject'],body=draft['body'],context_json=draft['context_json'],content_hash=draft['content_hash'],updated_at=at))
        elif draft['kind']=='internal_intake':
            lead=lead_or_404(conn,draft['lead_id'])
            if lead['stage'] not in OPEN or lead['owner_id']!=draft['owner_id'] or lead['suppressed']:
                conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(status='cancelled',updated_at=at))
                return 'skipped'
        if delivery and delivery['attempts']>=3:return 'exhausted'
        if delivery and delivery['retry_at'] and delivery['retry_at']>at and not force_retry:return 'deferred'
        message_id='leadrevive-'+draft['draft_id']+'@leadrevive.test'
        if not delivery:
            delivery=dict(delivery_id=str(uuid4()),draft_id=draft['draft_id'],message_id=message_id,
                status='pending',attempts=0,attempted_at=None,retry_at=None,accepted_at=None,sink_message_id=None,error=None)
            conn.execute(m.notification_deliveries.insert().values(**delivery))
        try:
            sink_id=self.transport.lookup(message_id)
            if delivery['status']=='uncertain' and not sink_id:
                raise UncertainAcceptance('No sink record yet; delivery outcome remains uncertain. Automatic resend is blocked.')
            if not sink_id:
                self.transport.send(draft,message_id)
                # SMTP acceptance is recorded; Mailpit capture is verified independently where available.
                try:sink_id=self.transport.lookup(message_id)
                except SinkUnavailable:sink_id=None
            conn.execute(m.notification_deliveries.update().where(m.notification_deliveries.c.delivery_id==delivery['delivery_id']).values(
                status='accepted',attempts=delivery['attempts']+1,attempted_at=at,accepted_at=at,retry_at=None,error=None,sink_message_id=sink_id))
            conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(status='sent_to_sink',updated_at=at))
            conn.execute(m.reminder_items.update().where(m.reminder_items.c.draft_id==draft['draft_id'],m.reminder_items.c.status=='pending').values(status='sent',sent_at=at))
            record_event(conn,m.audit_events,draft['lead_id'],'mailpit_smtp_accepted',{'draft_id':draft['draft_id'],'message_id':message_id,'sink_verified':bool(sink_id),'external_delivery':False},at)
            return 'accepted'
        except (SinkUnavailable,UncertainAcceptance) as exc:
            uncertain=isinstance(exc,UncertainAcceptance)
            conn.execute(m.notification_deliveries.update().where(m.notification_deliveries.c.delivery_id==delivery['delivery_id']).values(
                status='uncertain' if uncertain else 'failed',attempts=delivery['attempts']+1,attempted_at=at,
                retry_at=iso((dt(at)+timedelta(minutes=2**delivery['attempts'])).isoformat()),error=str(exc)))
            conn.execute(m.notification_drafts.update().where(m.notification_drafts.c.draft_id==draft['draft_id']).values(status='uncertain' if uncertain else 'failed',updated_at=at))
            record_event(conn,m.audit_events,draft['lead_id'],'sink_delivery_uncertain' if uncertain else 'sink_delivery_failed',{'draft_id':draft['draft_id'],'error':str(exc),'external_delivery':False},at)
            return 'failed'

    def dispatch(self,key,now,execution_id=None,draft_ids=None,force_retry=False):
        def action(conn,run_id,at):
            prune_items(conn,at)
            query=select(m.notification_drafts).where(m.notification_drafts.c.status.in_(['queued','approved','failed','uncertain']))
            if draft_ids is not None:query=query.where(m.notification_drafts.c.draft_id.in_(draft_ids))
            drafts=conn.execute(query.order_by(m.notification_drafts.c.created_at).limit(50)).mappings().all()
            results={};processed=skipped=failed=0
            for draft in drafts:
                outcome=self._deliver(conn,dict(draft),at,force_retry)
                results[draft['draft_id']]=outcome
                if outcome=='accepted':processed+=1
                elif outcome in ['failed','exhausted']:failed+=1
                else:skipped+=1
            return dict(processed=processed,skipped=skipped,failed=failed,outcomes=results,
                        error='One or more Mailpit deliveries need attention.' if failed else None)
        return self.run('dispatch',key,{'draft_ids':draft_ids,'force_retry':force_retry},now,action,execution_id)

    def sync(self,key,lead_id,version,changes,now,execution_id=None):
        def action(conn,run_id,at):
            lead=edit_lead(conn,lead_id,version,dict(changes),at)
            prune_items(conn,at)
            return dict(processed=1,skipped=0,failed=0,lead_id=lead_id,version=lead['version'],stage=lead['stage'])
        return self.run('status_sync',key,{'lead_id':lead_id,'version':version,'changes':changes},now,action,execution_id)
