import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Timestamped(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
class SoftDeleted(Timestamped):
    __abstract__ = True
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Admin(Timestamped):
    __tablename__ = 'admins'
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
class FileAsset(Timestamped):
    __tablename__ = 'file_assets'
    original_name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
class Bag(SoftDeleted):
    __tablename__ = 'bags'
    name: Mapped[str] = mapped_column(String(200))
    image_asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('file_assets.id'))
    width_mm: Mapped[int] = mapped_column(Integer)
    height_mm: Mapped[int] = mapped_column(Integer)
    base_price_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='draft')
class EmbroideryArea(Timestamped):
    __tablename__ = 'embroidery_areas'
    bag_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('bags.id'), unique=True)
    relative_x: Mapped[float] = mapped_column(Numeric(9, 6))
    relative_y: Mapped[float] = mapped_column(Numeric(9, 6))
    relative_width: Mapped[float] = mapped_column(Numeric(9, 6))
    relative_height: Mapped[float] = mapped_column(Numeric(9, 6))
    width_mm: Mapped[int] = mapped_column(Integer)
    height_mm: Mapped[int] = mapped_column(Integer)
class PatternCategory(SoftDeleted):
    __tablename__ = 'pattern_categories'
    name: Mapped[str] = mapped_column(String(100), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
class Pattern(SoftDeleted):
    __tablename__ = 'patterns'
    category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('pattern_categories.id'))
    name: Mapped[str] = mapped_column(String(200))
    production_code: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
class PatternVersion(Timestamped):
    __tablename__ = 'pattern_versions'
    pattern_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('patterns.id'))
    version_number: Mapped[int] = mapped_column(Integer)
    image_asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('file_assets.id'))
    width_mm: Mapped[int] = mapped_column(Integer)
    height_mm: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
class Design(Timestamped):
    __tablename__ = 'designs'
    bag_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('bags.id'))
    total_price_cents: Mapped[int] = mapped_column(Integer)
    preview_asset_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey('file_assets.id'), nullable=True)
class DesignItem(Timestamped):
    __tablename__ = 'design_items'
    design_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('designs.id'))
    pattern_version_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('pattern_versions.id'))
    center_x_ratio: Mapped[float] = mapped_column(Numeric(9, 6))
    center_y_ratio: Mapped[float] = mapped_column(Numeric(9, 6))
