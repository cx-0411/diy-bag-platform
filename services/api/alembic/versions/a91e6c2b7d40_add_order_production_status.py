"""add order shipment data

Revision ID: a91e6c2b7d40
Revises: f2b6c8d4a379
"""
from alembic import op
import sqlalchemy as sa

revision = 'a91e6c2b7d40'
down_revision = 'f2b6c8d4a379'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('tracking_no', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'tracking_no')
