"""add design item rotation

Revision ID: 0e8a1ba3cf42
Revises: 3e3f1bea2a32
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa

revision = '0e8a1ba3cf42'
down_revision = '3e3f1bea2a32'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('design_items', sa.Column('rotation_degrees', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('design_items', 'rotation_degrees', server_default=None)


def downgrade() -> None:
    op.drop_column('design_items', 'rotation_degrees')
