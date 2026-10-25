"""Initial Phase 1 schema. Frozen table definitions live in this revision."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None


def upgrade():
    from backend.migrations.schema_0001 import metadata
    metadata.create_all(op.get_bind())
    op.execute("CREATE VIEW v_open_pipeline AS SELECT * FROM leads WHERE stage NOT IN ('Won','Lost')")
    op.execute('''CREATE VIEW v_source_funnel AS SELECT lead_source, stage, COUNT(*) AS lead_count,
        SUM(estimated_value_paise) AS pipeline_value_paise FROM leads GROUP BY lead_source, stage''')


def downgrade():
    op.execute('DROP VIEW v_source_funnel')
    op.execute('DROP VIEW v_open_pipeline')
    from backend.migrations.schema_0001 import metadata
    metadata.drop_all(op.get_bind())
