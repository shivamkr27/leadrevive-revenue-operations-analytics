"""Portable SQLAlchemy schema. Currency is stored as integer INR paise."""
from sqlalchemy import (MetaData, Table, Column, String, Integer, Boolean, ForeignKey,
                        CheckConstraint, Index, Text)

metadata = MetaData()
owners = Table('owners', metadata, Column('owner_id', String, primary_key=True),
               Column('name', String, nullable=False), Column('active', Boolean, nullable=False))
leads = Table('leads', metadata,
    Column('lead_id', String, primary_key=True),
    *[Column(name, String, nullable=False) for name in ['created_at', 'updated_at', 'full_name',
        'company', 'email', 'phone', 'lead_source', 'campaign', 'industry', 'company_size',
        'stage', 'created_by', 'scenario_label']],
    Column('owner_id', String, ForeignKey('owners.owner_id')),
    Column('estimated_value_paise', Integer, nullable=False),
    Column('consent_to_email', Boolean, nullable=False, default=False),
    Column('email_verified', Boolean, nullable=False, default=False),
    Column('last_contacted_at', String), Column('first_contacted_at', String),
    Column('next_action_at', String), Column('response_sla_hours', Integer, nullable=False),
    Column('lost_reason', String), Column('suppressed', Boolean, nullable=False, default=False),
    Column('version', Integer, nullable=False, default=1),
    CheckConstraint('estimated_value_paise >= 0'), CheckConstraint('response_sla_hours > 0'),
    CheckConstraint("stage IN ('New','Contacted','Qualified','Meeting','Proposal','Won','Lost')"))
Index('ix_leads_email', leads.c.email)
Index('ix_leads_phone', leads.c.phone)
Index('ix_leads_queue', leads.c.stage, leads.c.owner_id, leads.c.next_action_at)
Index('ix_leads_created', leads.c.created_at)

import_batches = Table('import_batches', metadata,
    Column('batch_id', String, primary_key=True), Column('sha256', String, unique=True, nullable=False),
    Column('created_at', String, nullable=False), Column('summary_json', Text, nullable=False))
import_rejections = Table('import_rejections', metadata,
    Column('rejection_id', String, primary_key=True),
    Column('batch_id', String, ForeignKey('import_batches.batch_id'), nullable=False),
    Column('row_number', Integer, nullable=False), Column('reason', Text, nullable=False),
    Column('raw_json', Text, nullable=False))


def event_table(name):
    return Table(name, metadata, Column('event_id', String, primary_key=True),
        Column('lead_id', String, ForeignKey('leads.lead_id')),
        Column('created_at', String, nullable=False), Column('event_type', String, nullable=False),
        Column('details_json', Text, nullable=False))

lead_activities = event_table('lead_activities')
lead_status_history = event_table('lead_status_history')
lead_merge_audit = event_table('lead_merge_audit')
audit_events = event_table('audit_events')
config = Table('config', metadata, Column('key', String, primary_key=True),
               Column('value_json', Text, nullable=False))
