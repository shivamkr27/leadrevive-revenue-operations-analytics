"""Canonical timestamp precision and PostgreSQL money range."""
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'


def upgrade():
    conn = op.get_bind()
    tables = {'leads': ('lead_id', ['created_at','updated_at','first_contacted_at','last_contacted_at','next_action_at']),
              'import_batches': ('batch_id',['created_at'])}
    for name in ['lead_activities','lead_status_history','lead_merge_audit','audit_events']:
        tables[name] = ('event_id',['created_at'])
    for name, (pk, columns) in tables.items():
        table = sa.table(name, sa.column(pk), *[sa.column(c) for c in columns])
        for row in conn.execute(sa.select(table)).mappings().all():
            values = {c:datetime.fromisoformat(row[c].replace('Z','+00:00')).astimezone(timezone.utc)
                      .isoformat(timespec='microseconds').replace('+00:00','Z') for c in columns if row[c]}
            if values:
                conn.execute(table.update().where(table.c[pk] == row[pk]).values(**values))
    if conn.dialect.name == 'postgresql':
        op.execute('DROP VIEW v_open_pipeline')
        op.execute('DROP VIEW v_source_funnel')
        op.alter_column('leads','estimated_value_paise',type_=sa.BigInteger())
        op.execute("CREATE VIEW v_open_pipeline AS SELECT * FROM leads WHERE stage NOT IN ('Won','Lost')")
        op.execute('CREATE VIEW v_source_funnel AS SELECT lead_source, stage, COUNT(*) AS lead_count, SUM(estimated_value_paise) AS pipeline_value_paise FROM leads GROUP BY lead_source,stage')


def downgrade():
    # Precision normalization is lossless and intentionally retained on downgrade.
    # BIGINT is retained to avoid destructive narrowing of existing currency values.
    pass
