from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Bag, Design, DesignItem, EmbroideryArea, PatternVersion
from app.schemas import DesignIn
def create_design(session: Session, payload: DesignIn) -> Design:
    bag = session.scalar(select(Bag).where(Bag.id == payload.bag_id, Bag.deleted_at.is_(None), Bag.status == 'published'))
    if not bag: raise HTTPException(404, 'Bag is not available')
    area = session.scalar(select(EmbroideryArea).where(EmbroideryArea.bag_id == bag.id))
    if not area: raise HTTPException(409, 'Bag has no embroidery area')
    versions = {version.id: version for version in session.scalars(select(PatternVersion).where(PatternVersion.id.in_([item.pattern_version_id for item in payload.items])))}
    if len(versions) != len({item.pattern_version_id for item in payload.items}): raise HTTPException(422, 'Pattern version does not exist')
    total = bag.base_price_cents
    design = Design(bag_id=bag.id, total_price_cents=0); session.add(design); session.flush()
    for item in payload.items:
        version = versions[item.pattern_version_id]; x = Decimal(str(item.center_x_ratio)); y = Decimal(str(item.center_y_ratio)); half_w = Decimal(version.width_mm) / Decimal(area.width_mm) / 2; half_h = Decimal(version.height_mm) / Decimal(area.height_mm) / 2
        if x < half_w or x > 1-half_w or y < half_h or y > 1-half_h: raise HTTPException(422, 'Pattern must remain completely inside embroidery area')
        session.add(DesignItem(design_id=design.id, pattern_version_id=version.id, center_x_ratio=x, center_y_ratio=y)); total += version.price_cents
    design.total_price_cents = total; session.flush(); return design
