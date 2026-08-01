"""add cart items

Revision ID: c5e4a7b9d308
Revises: a91e6c2b7d40
"""
from alembic import op
import sqlalchemy as sa

revision = 'c5e4a7b9d308'
down_revision = 'a91e6c2b7d40'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('cart_items', sa.Column('client_key', sa.String(64), nullable=False), sa.Column('design_id', sa.Uuid(), nullable=False), sa.Column('id', sa.Uuid(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.ForeignKeyConstraint(['design_id'], ['designs.id']), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_cart_items_client_key', 'cart_items', ['client_key'])

def downgrade() -> None:
    op.drop_index('ix_cart_items_client_key', table_name='cart_items'); op.drop_table('cart_items')
