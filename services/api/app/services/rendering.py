from __future__ import annotations

from io import BytesIO
from math import floor

from fastapi import HTTPException
from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bag, Design, DesignAsset, DesignItem, EmbroideryArea, FileAsset, Order, PatternVersion
from app.services.storage import StorageService


def _load_image(storage: StorageService, asset: FileAsset) -> Image.Image:
    try:
        with Image.open(storage.path_for(asset.storage_key)) as source:
            return source.convert('RGBA')
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(422, f'Cannot render image asset: {asset.original_name}') from error


def _load_storage_key(storage: StorageService, key: str | None) -> Image.Image:
    if not key:
        raise HTTPException(409, 'The historical image snapshot is unavailable')
    try:
        with Image.open(storage.path_for(key)) as source:
            return source.convert('RGBA')
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(409, 'The historical image snapshot is unavailable') from error


def _encode(image: Image.Image) -> bytes:
    result = BytesIO()
    image.save(result, 'PNG', optimize=True)
    return result.getvalue()


def render_design_preview(session: Session, design: Design) -> FileAsset:
    """Render a non-production design preview using persisted physical measurements."""
    bag = session.get(Bag, design.bag_id)
    area = session.scalar(select(EmbroideryArea).where(EmbroideryArea.bag_id == design.bag_id))
    if not bag or not area:
        raise HTTPException(409, 'Design source is no longer renderable')
    storage = StorageService()
    bag_asset = session.get(FileAsset, bag.image_asset_id)
    if not bag_asset:
        raise HTTPException(409, 'Bag image is unavailable')
    canvas = _load_image(storage, bag_asset)
    width, height = canvas.size
    area_x, area_y = width * float(area.relative_x), height * float(area.relative_y)
    area_w, area_h = width * float(area.relative_width), height * float(area.relative_height)
    items = session.scalars(select(DesignItem).where(DesignItem.design_id == design.id).order_by(DesignItem.z_index, DesignItem.created_at)).all()
    for item in items:
        version = session.get(PatternVersion, item.pattern_version_id)
        image_asset = session.get(FileAsset, version.image_asset_id) if version else None
        if not version or not image_asset:
            raise HTTPException(409, 'Pattern source is unavailable')
        sticker = _load_image(storage, image_asset)
        fixed_width = max(1, round(area_w * version.width_mm / area.width_mm))
        fixed_height = max(1, round(area_h * version.height_mm / area.height_mm))
        sticker = sticker.resize((fixed_width, fixed_height), Image.Resampling.LANCZOS)
        if item.rotation_degrees:
            sticker = sticker.rotate(-item.rotation_degrees, expand=True, resample=Image.Resampling.BICUBIC)
        center_x = area_x + float(item.center_x_ratio) * area_w
        center_y = area_y + float(item.center_y_ratio) * area_h
        canvas.alpha_composite(sticker, (floor(center_x - sticker.width / 2), floor(center_y - sticker.height / 2)))
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.text((16, max(16, height - 30)), 'DIY PREVIEW', fill=(255, 255, 255, 140), stroke_width=1, stroke_fill=(60, 45, 35, 140))
    canvas = Image.alpha_composite(canvas, overlay)
    key, size = storage.save_bytes(_encode(canvas))
    asset = FileAsset(original_name=f'design-preview-{design.id}.png', storage_key=key, content_type='image/png', size_bytes=size, visibility='public')
    session.add(asset); session.flush()
    design.preview_asset_id = asset.id
    record = session.scalar(select(DesignAsset).where(DesignAsset.design_id == design.id))
    if record:
        record.preview_asset_id = asset.id
    else:
        session.add(DesignAsset(design_id=design.id, preview_asset_id=asset.id))
    return asset


def render_order_production(session: Session, order: Order) -> FileAsset:
    """Render from the order snapshot, so later catalog edits cannot change production artwork."""
    if order.status != 'PAID':
        raise HTTPException(409, 'Production artwork is available after payment')
    existing_id = order.snapshot.get('production_asset_id')
    if existing_id:
        existing = session.get(FileAsset, existing_id)
        if existing:
            return existing
    storage = StorageService()
    bag = order.snapshot.get('bag', {})
    area = order.snapshot.get('embroidery_area', {})
    canvas = _load_storage_key(storage, bag.get('image_storage_key'))
    image_width, image_height = canvas.size
    area_x = image_width * area['relative_x']; area_y = image_height * area['relative_y']
    area_width = image_width * area['relative_width']; area_height = image_height * area['relative_height']
    for item in sorted(order.snapshot.get('items', []), key=lambda value: value.get('z_index', 0)):
        sticker = _load_storage_key(storage, item.get('image_storage_key'))
        fixed_width = max(1, round(area_width * item['width_mm'] / area['width_mm']))
        fixed_height = max(1, round(area_height * item['height_mm'] / area['height_mm']))
        sticker = sticker.resize((fixed_width, fixed_height), Image.Resampling.LANCZOS)
        if item.get('rotation_degrees'):
            sticker = sticker.rotate(-item['rotation_degrees'], expand=True, resample=Image.Resampling.BICUBIC)
        center_x = area_x + item['center_x_ratio'] * area_width
        center_y = area_y + item['center_y_ratio'] * area_height
        canvas.alpha_composite(sticker, (floor(center_x - sticker.width / 2), floor(center_y - sticker.height / 2)))
    key, size = storage.save_bytes(_encode(canvas))
    asset = FileAsset(original_name=f'production-{order.order_no}.png', storage_key=key, content_type='image/png', size_bytes=size, visibility='private')
    session.add(asset); session.flush()
    snapshot = dict(order.snapshot); snapshot['production_asset_id'] = str(asset.id); order.snapshot = snapshot
    return asset
