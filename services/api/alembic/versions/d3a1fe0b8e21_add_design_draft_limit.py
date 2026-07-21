"""add design draft limit

Revision ID: d3a1fe0b8e21
Revises: 0e8a1ba3cf42
"""
from alembic import op
import sqlalchemy as sa

revision = 'd3a1fe0b8e21'
down_revision = '0e8a1ba3cf42'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('app_settings', sa.Column('key', sa.String(100), nullable=False), sa.Column('value_int', sa.Integer(), nullable=False), sa.Column('id', sa.Uuid(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('key'))
    op.add_column('designs', sa.Column('client_key', sa.String(64), nullable=True))
    op.create_index('ix_designs_client_key', 'designs', ['client_key'])

def downgrade() -> None:
    op.drop_index('ix_designs_client_key', table_name='designs'); op.drop_column('designs', 'client_key'); op.drop_table('app_settings')
