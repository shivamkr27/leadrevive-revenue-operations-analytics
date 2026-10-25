"""Durable runs, reminder reservations, exact-content approvals and sink delivery ledger."""
from alembic import op
from sqlalchemy import MetaData, Table, Column, String
from backend.migrations.schema_0004 import add_tables

revision='0004'
down_revision='0003'


def tables():
    meta=MetaData()
    for name,key in [('leads','lead_id'),('owners','owner_id')]:
        Table(name,meta,Column(key,String,primary_key=True))
    new=add_tables(meta)
    return [table for table in meta.sorted_tables if table.name in new]


def upgrade():
    for table in tables():
        table.create(op.get_bind())


def downgrade():
    for table in reversed(tables()):
        table.drop(op.get_bind())
