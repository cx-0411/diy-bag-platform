"""add asset visibility and a single asset record per design

Revision ID: e7f6a4d2c591
Revises: c9e4a5b8d271
"""
from alembic import op
import sqlalchemy as sa

revision = 'e7f6a4d2c591'
down_revision = 'c9e4a5b8d271'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('file_assets', sa.Column('visibility', sa.String(20), nullable=False, server_default='public'))
    op.create_unique_constraint('uq_design_assets_design_id', 'design_assets', ['design_id'])


def downgrade() -> None:
    op.drop_constraint('uq_design_assets_design_id', 'design_assets', type_='unique')
    op.drop_column('file_assets', 'visibility')
