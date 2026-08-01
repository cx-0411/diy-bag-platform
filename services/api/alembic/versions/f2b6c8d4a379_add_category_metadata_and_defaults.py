"""add category metadata and the six default mobile categories

Revision ID: f2b6c8d4a379
Revises: e7f6a4d2c591
"""
import uuid

from alembic import op
import sqlalchemy as sa

revision = 'f2b6c8d4a379'
down_revision = 'e7f6a4d2c591'
branch_labels = None
depends_on = None

_CATEGORIES = [
    ('11ec3d49-b415-421e-950a-63e964a6d201', '主角登场', '🐱', '猫咪等可作为主图的图案', 10),
    ('11ec3d49-b415-421e-950a-63e964a6d202', '花园派对', '🌼', '花草、树木、太阳和云朵背景', 20),
    ('11ec3d49-b415-421e-950a-63e964a6d203', '野餐篮子', '🍔', '食物、甜点和饮料', 30),
    ('11ec3d49-b415-421e-950a-63e964a6d204', '假日时光', '🏖️', '房子、泳池、遮阳伞和泳裙', 40),
    ('11ec3d49-b415-421e-950a-63e964a6d205', '装饰杂货铺', '🎀', '星星、爱心、边框、线条和符号', 50),
    ('11ec3d49-b415-421e-950a-63e964a6d206', '心情便签', '🔤', '字母和短语', 60),
]


def upgrade() -> None:
    op.add_column('pattern_categories', sa.Column('icon', sa.String(32), nullable=False, server_default='✨'))
    op.add_column('pattern_categories', sa.Column('description', sa.String(200), nullable=False, server_default=''))
    op.add_column('pattern_categories', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    for category_id, name, icon, description, sort_order in _CATEGORIES:
        op.execute(sa.text("""
            INSERT INTO pattern_categories (id, name, sort_order, icon, description, is_active, created_at, updated_at)
            VALUES (:id, :name, :sort_order, :icon, :description, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (name) DO NOTHING
        """).bindparams(id=uuid.UUID(category_id), name=name, sort_order=sort_order, icon=icon, description=description))


def downgrade() -> None:
    op.drop_column('pattern_categories', 'is_active')
    op.drop_column('pattern_categories', 'description')
    op.drop_column('pattern_categories', 'icon')
