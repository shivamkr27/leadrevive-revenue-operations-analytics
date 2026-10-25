"""Portable, current-state analytics facts. Evaluation time belongs to the snapshot."""
from alembic import op

revision = '0005'
down_revision = '0004'


def upgrade():
    op.execute("""CREATE VIEW v_analytics_leads AS
        SELECT l.*, o.name AS owner_name,
        CASE WHEN o.active THEN 1 ELSE 0 END AS owner_active,
        CASE WHEN l.stage NOT IN ('Won','Lost') THEN 1 ELSE 0 END AS is_open
        FROM leads l LEFT JOIN owners o ON o.owner_id=l.owner_id""")


def downgrade():
    op.execute('DROP VIEW v_analytics_leads')
