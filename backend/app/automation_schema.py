"""Phase 3 durable automation/outbox schema, shared by SQLite and PostgreSQL."""
from sqlalchemy import Table, Column, String, Integer, Text, ForeignKey, UniqueConstraint, Index


def add_tables(metadata):
    runs=Table('automation_runs',metadata,
        Column('run_id',String,primary_key=True),Column('workflow',String,nullable=False),
        Column('idempotency_key',String,nullable=False,unique=True),Column('payload_hash',String,nullable=False),
        Column('execution_id',String),Column('status',String,nullable=False),
        Column('started_at',String,nullable=False),Column('completed_at',String),
        Column('attempts',Integer,nullable=False),Column('processed',Integer,nullable=False),
        Column('skipped',Integer,nullable=False),Column('failed',Integer,nullable=False),
        Column('result_json',Text,nullable=False),Column('error',Text))
    drafts=Table('notification_drafts',metadata,
        Column('draft_id',String,primary_key=True),Column('run_id',String,ForeignKey('automation_runs.run_id')),
        Column('lead_id',String,ForeignKey('leads.lead_id')),Column('owner_id',String,ForeignKey('owners.owner_id')),
        Column('kind',String,nullable=False),Column('intended_recipient',String,nullable=False),
        Column('sink_recipient',String,nullable=False),Column('subject',String,nullable=False),
        Column('body',Text,nullable=False),Column('content_hash',String,nullable=False),
        Column('version',Integer,nullable=False),Column('created_at',String,nullable=False),
        Column('updated_at',String,nullable=False),Column('status',String,nullable=False),
        Column('context_json',Text,nullable=False))
    approvals=Table('notification_approvals',metadata,
        Column('approval_id',String,primary_key=True),Column('draft_id',String,ForeignKey('notification_drafts.draft_id'),nullable=False,unique=True),
        Column('approved_hash',String,nullable=False),Column('approved_by',String,nullable=False),
        Column('approved_at',String,nullable=False),Column('mode',String,nullable=False))
    deliveries=Table('notification_deliveries',metadata,
        Column('delivery_id',String,primary_key=True),Column('draft_id',String,ForeignKey('notification_drafts.draft_id'),nullable=False,unique=True),
        Column('message_id',String,nullable=False,unique=True),Column('status',String,nullable=False),
        Column('attempts',Integer,nullable=False),Column('attempted_at',String),Column('retry_at',String),
        Column('accepted_at',String),Column('sink_message_id',String),Column('error',Text))
    items=Table('reminder_items',metadata,
        Column('item_id',String,primary_key=True),Column('draft_id',String,ForeignKey('notification_drafts.draft_id'),nullable=False),
        Column('lead_id',String,ForeignKey('leads.lead_id'),nullable=False),
        Column('owner_id',String,ForeignKey('owners.owner_id'),nullable=False),
        Column('next_action_at',String,nullable=False),Column('contact_snapshot',String),
        Column('status',String,nullable=False),Column('created_at',String,nullable=False),Column('sent_at',String),
        UniqueConstraint('draft_id','lead_id',name='uq_reminder_draft_lead'))
    Index('ix_reminder_lead_cooldown',items.c.lead_id,items.c.status,items.c.sent_at)
    Index('ix_drafts_pending',drafts.c.status,drafts.c.created_at)
    return {table.name:table for table in [runs,drafts,approvals,deliveries,items]}
