from __future__ import annotations

from io import BytesIO
from math import floor
from uuid import UUID

from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont
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


def _preview_watermark(canvas: Image.Image) -> Image.Image:
    """Make preview-only artwork unmistakable without changing production files."""
    width, height = canvas.size
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    try:
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', max(24, min(width, height) // 19))
        text = '设计已完成，付款后不支持退款'
    except OSError:
        # Local unit-test machines may not have a CJK font. Production Docker
        # images install Noto CJK and therefore use the Chinese customer copy.
        font = ImageFont.load_default()
        text = 'DESIGN COMPLETE - NO REFUNDS'

    text_box = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    tile = Image.new('RGBA', (text_width + 64, text_height + 46), (0, 0, 0, 0))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.text((32 - text_box[0], 20 - text_box[1]), text, font=font, fill=(255, 255, 255, 126))
    tilted_tile = tile.rotate(28, expand=True, resample=Image.Resampling.BICUBIC)
    row_step = max(tilted_tile.height + 22, height // 5)
    column_step = max(tilted_tile.width - 30, width // 2)
    for row, top in enumerate(range(-tilted_tile.height, height + tilted_tile.height, row_step)):
        offset = -(tilted_tile.width // 2) if row % 2 else 0
        for left in range(-tilted_tile.width + offset, width + tilted_tile.width, column_step):
            overlay.alpha_composite(tilted_tile, (left, top))
    return Image.alpha_composite(canvas, overlay)


def render_design_preview(session: Session, design: Design) -> FileAsset:
    """Render a non-production design preview using persisted physical measurements."""
    if design.preview_asset_id:
        existing = session.get(FileAsset, design.preview_asset_id)
        if existing:
            return existing
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
    canvas = _preview_watermark(canvas)
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
    existing_id = order.snapshot.get('production_asset_id')
    if existing_id:
        existing = session.get(FileAsset, UUID(str(existing_id)))
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
