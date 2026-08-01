from decimal import Decimal
from math import cos, radians, sin
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import AppSetting, Bag, Design, DesignItem, EmbroideryArea, PatternVersion
from app.schemas import DesignIn
def create_design(session: Session, payload: DesignIn) -> Design:
    limit = session.scalar(select(AppSetting.value_int).where(AppSetting.key == 'max_design_drafts')) or 3
    saved_count = session.scalar(select(func.count(Design.id)).where(Design.client_key == payload.client_key)) or 0
    if saved_count >= limit: raise HTTPException(409, f'Design draft limit reached ({limit})')
    bag = session.scalar(select(Bag).where(Bag.id == payload.bag_id, Bag.deleted_at.is_(None), Bag.status == 'published'))
    if not bag: raise HTTPException(404, 'Bag is not available')
    area = session.scalar(select(EmbroideryArea).where(EmbroideryArea.bag_id == bag.id))
    if not area: raise HTTPException(409, 'Bag has no embroidery area')
    versions = {version.id: version for version in session.scalars(select(PatternVersion).where(PatternVersion.id.in_([item.pattern_version_id for item in payload.items])))}
    if len(versions) != len({item.pattern_version_id for item in payload.items}): raise HTTPException(422, 'Pattern version does not exist')
    total = bag.base_price_cents
    design = Design(bag_id=bag.id, client_key=payload.client_key, total_price_cents=0); session.add(design); session.flush()
    for item in payload.items:
        version = versions[item.pattern_version_id]; x = Decimal(str(item.center_x_ratio)); y = Decimal(str(item.center_y_ratio)); angle = radians(item.rotation_degrees); rotated_width = Decimal(str(abs(version.width_mm * cos(angle)) + abs(version.height_mm * sin(angle)))); rotated_height = Decimal(str(abs(version.width_mm * sin(angle)) + abs(version.height_mm * cos(angle)))); half_w = rotated_width / Decimal(area.width_mm) / 2; half_h = rotated_height / Decimal(area.height_mm) / 2
        if x < half_w or x > 1-half_w or y < half_h or y > 1-half_h: raise HTTPException(422, 'Pattern must remain completely inside embroidery area')
        session.add(DesignItem(design_id=design.id, pattern_version_id=version.id, center_x_ratio=x, center_y_ratio=y, rotation_degrees=item.rotation_degrees, z_index=item.z_index)); total += version.price_cents
    design.total_price_cents = total; session.flush(); return design
