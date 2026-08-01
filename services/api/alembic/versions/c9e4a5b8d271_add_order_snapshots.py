"""add order snapshots

Revision ID: c9e4a5b8d271
Revises: b1c7f2d9e4a6
"""
from alembic import op
import sqlalchemy as sa

revision = 'c9e4a5b8d271'
down_revision = 'b1c7f2d9e4a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('design_assets', sa.Column('design_id', sa.Uuid(), nullable=False), sa.Column('preview_asset_id', sa.Uuid(), nullable=True), sa.Column('production_asset_id', sa.Uuid(), nullable=True), sa.Column('id', sa.Uuid(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.ForeignKeyConstraint(['design_id'], ['designs.id']), sa.ForeignKeyConstraint(['preview_asset_id'], ['file_assets.id']), sa.ForeignKeyConstraint(['production_asset_id'], ['file_assets.id']), sa.PrimaryKeyConstraint('id'))
    op.create_table('orders', sa.Column('order_no', sa.String(40), nullable=False), sa.Column('client_key', sa.String(64), nullable=False), sa.Column('design_id', sa.Uuid(), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('total_price_cents', sa.Integer(), nullable=False), sa.Column('snapshot', sa.JSON(), nullable=False), sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True), sa.Column('id', sa.Uuid(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.ForeignKeyConstraint(['design_id'], ['designs.id']), sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('order_no'))
    op.create_index('ix_orders_order_no', 'orders', ['order_no']); op.create_index('ix_orders_client_key', 'orders', ['client_key'])
    op.create_table('order_items', sa.Column('order_id', sa.Uuid(), nullable=False), sa.Column('pattern_version_id', sa.Uuid(), nullable=False), sa.Column('name_snapshot', sa.String(200), nullable=False), sa.Column('width_mm_snapshot', sa.Integer(), nullable=False), sa.Column('height_mm_snapshot', sa.Integer(), nullable=False), sa.Column('price_cents_snapshot', sa.Integer(), nullable=False), sa.Column('center_x_ratio', sa.Numeric(9,6), nullable=False), sa.Column('center_y_ratio', sa.Numeric(9,6), nullable=False), sa.Column('rotation_degrees', sa.Integer(), nullable=False), sa.Column('z_index', sa.Integer(), nullable=False), sa.Column('id', sa.Uuid(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False), sa.ForeignKeyConstraint(['order_id'], ['orders.id']), sa.ForeignKeyConstraint(['pattern_version_id'], ['pattern_versions.id']), sa.PrimaryKeyConstraint('id'))

def downgrade() -> None:
    op.drop_table('order_items'); op.drop_index('ix_orders_client_key', table_name='orders'); op.drop_index('ix_orders_order_no', table_name='orders'); op.drop_table('orders'); op.drop_table('design_assets')
