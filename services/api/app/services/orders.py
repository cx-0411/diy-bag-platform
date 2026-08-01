from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Bag, Design, DesignItem, FileAsset, Order, OrderItem, Pattern, PatternVersion

def create_order(session: Session, design_id, client_key: str) -> Order:
    design = session.scalar(select(Design).where(Design.id == design_id, Design.client_key == client_key))
    if not design: raise HTTPException(404, 'Design not found')
    bag = session.get(Bag, design.bag_id)
    if not bag or bag.deleted_at or bag.status != 'published': raise HTTPException(409, 'Bag is not available')
    items = session.scalars(select(DesignItem).where(DesignItem.design_id == design.id).order_by(DesignItem.z_index)).all()
    versions = {item.id: item for item in session.scalars(select(PatternVersion).where(PatternVersion.id.in_([row.pattern_version_id for row in items])))}
    bag_asset = session.get(FileAsset, bag.image_asset_id)
    total = bag.base_price_cents
    snapshot_items = []
    for row in items:
        version = versions.get(row.pattern_version_id)
        if not version: raise HTTPException(409, 'Pattern version is unavailable')
        pattern = session.get(Pattern, version.pattern_id)
        if not pattern or pattern.deleted_at or pattern.status != 'published':
            raise HTTPException(409, 'Pattern is unavailable')
        image_asset = session.get(FileAsset, version.image_asset_id)
        total += version.price_cents
        item_snapshot = {
            'pattern_version_id': str(version.id), 'name': pattern.name,
            'image_asset_id': str(version.image_asset_id),
            'image_storage_key': image_asset.storage_key if image_asset else None,
            'width_mm': version.width_mm, 'height_mm': version.height_mm,
            'price_cents': version.price_cents,
            'center_x_ratio': float(row.center_x_ratio), 'center_y_ratio': float(row.center_y_ratio),
            'rotation_degrees': row.rotation_degrees, 'z_index': row.z_index,
        }
        snapshot_items.append((version.id, item_snapshot))
    order = Order(
        order_no=f'DIY{datetime.now(timezone.utc):%Y%m%d}{uuid4().hex[:10].upper()}',
        client_key=client_key, design_id=design.id, total_price_cents=total,
        snapshot={
            'bag': {'id': str(bag.id), 'name': bag.name, 'image_asset_id': str(bag.image_asset_id),
                    'image_storage_key': bag_asset.storage_key if bag_asset else None,
                    'price_cents': bag.base_price_cents},
            'items': [snapshot for _, snapshot in snapshot_items],
        },
    )
    session.add(order); session.flush()
    for version_id, item in snapshot_items:
        session.add(OrderItem(order_id=order.id, pattern_version_id=version_id, name_snapshot=item['name'], width_mm_snapshot=item['width_mm'], height_mm_snapshot=item['height_mm'], price_cents_snapshot=item['price_cents'], center_x_ratio=item['center_x_ratio'], center_y_ratio=item['center_y_ratio'], rotation_degrees=item['rotation_degrees'], z_index=item['z_index']))
    return order

def mock_pay(session: Session, order_id, client_key: str) -> Order:
    order = session.scalar(select(Order).where(Order.id == order_id, Order.client_key == client_key))
    if not order: raise HTTPException(404, 'Order not found')
    if order.status != 'PENDING_PAYMENT': raise HTTPException(409, 'Order cannot be paid')
    order.status = 'PAID'; order.paid_at = datetime.now(timezone.utc); return order
