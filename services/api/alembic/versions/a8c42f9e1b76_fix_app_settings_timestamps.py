"""fix app settings timestamps

Revision ID: a8c42f9e1b76
Revises: d3a1fe0b8e21
"""
from alembic import op
import sqlalchemy as sa

revision = 'a8c42f9e1b76'
down_revision = 'd3a1fe0b8e21'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('app_settings', 'created_at', server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('app_settings', 'updated_at', server_default=sa.text('CURRENT_TIMESTAMP'))

def downgrade() -> None:
    op.alter_column('app_settings', 'created_at', server_default=None)
    op.alter_column('app_settings', 'updated_at', server_default=None)
