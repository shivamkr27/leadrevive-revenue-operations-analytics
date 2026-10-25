"""Append-only, versioned data-quality review decisions."""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'


def upgrade():
    op.create_table('exception_reviews',
        sa.Column('rejection_id', sa.String(), sa.ForeignKey('import_rejections.rejection_id'),primary_key=True),
        sa.Column('decision',sa.String(),nullable=False),
        sa.Column('note',sa.Text(),nullable=False),
        sa.Column('reviewed_at',sa.String(),nullable=False))


def downgrade():
    op.drop_table('exception_reviews')
