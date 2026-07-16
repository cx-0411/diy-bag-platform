from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.models import Bag, EmbroideryArea, FileAsset, Pattern, PatternCategory, PatternVersion
from app.schemas import DesignIn, DesignItemIn
from app.services.designs import create_design

@pytest.fixture()
def session():
    engine = create_engine('sqlite://'); Base.metadata.create_all(engine)
    with Session(engine) as session:
        asset = FileAsset(original_name='x.svg', storage_key='x.svg', content_type='image/svg+xml', size_bytes=1); session.add(asset); session.flush()
        bag = Bag(name='bag', image_asset_id=asset.id, width_mm=280, height_mm=220, base_price_cents=15900, status='published'); session.add(bag); session.flush()
        session.add(EmbroideryArea(bag_id=bag.id, relative_x=.2, relative_y=.2, relative_width=.6, relative_height=.5, width_mm=180, height_mm=120))
        category=PatternCategory(name='cat'); session.add(category); session.flush(); pattern=Pattern(category_id=category.id,name='flower',production_code='P1',status='published'); session.add(pattern); session.flush(); version=PatternVersion(pattern_id=pattern.id,version_number=1,image_asset_id=asset.id,width_mm=42,height_mm=42,price_cents=1200); session.add(version); session.flush(); pattern.current_version_id=version.id; session.commit(); yield session,bag,version
def test_price_and_valid_design(session):
    db, bag, version = session; design=create_design(db, DesignIn(bag_id=bag.id,items=[DesignItemIn(pattern_version_id=version.id,center_x_ratio=.5,center_y_ratio=.5)])); assert design.total_price_cents == 17100
def test_rejects_out_of_bounds(session):
    db, bag, version = session
    with pytest.raises(HTTPException, match='completely'): create_design(db, DesignIn(bag_id=bag.id,items=[DesignItemIn(pattern_version_id=version.id,center_x_ratio=0,center_y_ratio=.5)]))
def test_rejects_unknown_version(session):
    db, bag, _ = session
    with pytest.raises(HTTPException): create_design(db, DesignIn(bag_id=bag.id,items=[DesignItemIn(pattern_version_id=uuid4(),center_x_ratio=.5,center_y_ratio=.5)]))
