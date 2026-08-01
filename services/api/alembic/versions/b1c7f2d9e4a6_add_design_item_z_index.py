"""add design item z index

Revision ID: b1c7f2d9e4a6
Revises: a8c42f9e1b76
"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c7f2d9e4a6'
down_revision = 'a8c42f9e1b76'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('design_items', sa.Column('z_index', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('design_items', 'z_index', server_default=None)

def downgrade() -> None:
    op.drop_column('design_items', 'z_index')
