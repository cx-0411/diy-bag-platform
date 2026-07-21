from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Bag, EmbroideryArea, FileAsset, Pattern, PatternCategory, PatternVersion, DesignItem
from app.schemas import AreaIn, AreaOut, AssetOut, BagIn, BagOut, CategoryIn, CategoryOut, DesignIn, DesignItemOut, DesignOut, PatternIn, PatternOut, PatternVersionOut
from app.services.designs import create_design
from app.services.storage import StorageService
router = APIRouter()
def active(statement, model): return statement.where(model.deleted_at.is_(None))
@router.post('/files', response_model=AssetOut)
def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type or not file.content_type.startswith('image/'): raise HTTPException(415, 'Only image uploads are supported')
    storage = StorageService(); key, size = storage.save_upload(file); asset = FileAsset(original_name=file.filename or key, storage_key=key, content_type=file.content_type, size_bytes=size); db.add(asset); db.commit(); db.refresh(asset); return AssetOut(id=asset.id, original_name=asset.original_name, content_type=asset.content_type, size_bytes=asset.size_bytes, url=storage.url(key))
@router.get('/files/{key}')
def download(key: str):
    target = Path(StorageService().root) / key
    if not target.is_file(): raise HTTPException(404, 'File not found')
    return FileResponse(target)
@router.post('/bags', response_model=BagOut)
def create_bag(data: BagIn, db: Session = Depends(get_db)):
    if not db.get(FileAsset, data.image_asset_id): raise HTTPException(422, 'Bag image does not exist')
    bag = Bag(**data.model_dump()); db.add(bag); db.commit(); db.refresh(bag); return bag
@router.get('/bags', response_model=list[BagOut])
def list_bags(db: Session = Depends(get_db)): return db.scalars(active(select(Bag), Bag)).all()
@router.get('/bags/{bag_id}', response_model=BagOut)
def get_bag(bag_id: UUID, db: Session = Depends(get_db)):
    bag = db.scalar(active(select(Bag).where(Bag.id == bag_id), Bag))
    if not bag: raise HTTPException(404, 'Bag not found')
    return bag
@router.put('/bags/{bag_id}', response_model=BagOut)
def update_bag(bag_id: UUID, data: BagIn, db: Session = Depends(get_db)):
    bag = db.scalar(active(select(Bag).where(Bag.id == bag_id), Bag))
    if not bag: raise HTTPException(404, 'Bag not found')
    for key, value in data.model_dump().items(): setattr(bag, key, value)
    db.commit(); db.refresh(bag); return bag
@router.post('/bags/{bag_id}/status', response_model=BagOut)
def set_bag_status(bag_id: UUID, status: str, db: Session = Depends(get_db)):
    if status not in {'draft','published','unpublished','archived'}: raise HTTPException(422, 'Invalid bag status')
    bag = db.scalar(active(select(Bag).where(Bag.id == bag_id), Bag))
    if not bag: raise HTTPException(404, 'Bag not found')
    bag.status = status
    if status == 'archived':
        from datetime import datetime, timezone
        bag.deleted_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(bag); return bag
@router.get('/bags/{bag_id}/embroidery-area', response_model=AreaOut)
def get_area(bag_id: UUID, db: Session = Depends(get_db)):
    area = db.scalar(select(EmbroideryArea).where(EmbroideryArea.bag_id == bag_id))
    if not area: raise HTTPException(404, 'Embroidery area not found')
    return area
@router.post('/bags/{bag_id}/embroidery-area', response_model=AreaOut)
def set_area(bag_id: UUID, data: AreaIn, db: Session = Depends(get_db)):
    if not db.get(Bag, bag_id): raise HTTPException(404, 'Bag not found')
    area = db.scalar(select(EmbroideryArea).where(EmbroideryArea.bag_id == bag_id))
    if area:
        for key, value in data.model_dump().items(): setattr(area, key, value)
    else: area = EmbroideryArea(bag_id=bag_id, **data.model_dump()); db.add(area)
    db.commit(); db.refresh(area); return area
@router.post('/pattern-categories', response_model=CategoryOut)
def create_category(data: CategoryIn, db: Session = Depends(get_db)):
    category = PatternCategory(**data.model_dump()); db.add(category); db.commit(); db.refresh(category); return category
@router.get('/pattern-categories', response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)): return db.scalars(active(select(PatternCategory), PatternCategory)).all()
@router.post('/patterns', response_model=PatternOut)
def create_pattern(data: PatternIn, db: Session = Depends(get_db)):
    if not db.get(PatternCategory, data.category_id) or not db.get(FileAsset, data.image_asset_id): raise HTTPException(422, 'Category or image does not exist')
    pattern = Pattern(category_id=data.category_id, name=data.name, production_code=data.production_code, status=data.status); db.add(pattern); db.flush(); version = PatternVersion(pattern_id=pattern.id, version_number=1, image_asset_id=data.image_asset_id, width_mm=data.width_mm, height_mm=data.height_mm, price_cents=data.price_cents); db.add(version); db.flush(); pattern.current_version_id = version.id; db.commit(); db.refresh(pattern); return pattern
@router.put('/patterns/{pattern_id}', response_model=PatternOut)
def update_pattern(pattern_id: UUID, data: PatternIn, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern or pattern.deleted_at: raise HTTPException(404, 'Pattern not found')
    for key in ('category_id','name','production_code','status'): setattr(pattern,key,getattr(data,key))
    current = db.get(PatternVersion, pattern.current_version_id); changed = not current or any(getattr(current,k) != getattr(data,k) for k in ('image_asset_id','width_mm','height_mm','price_cents'))
    if changed:
        version = PatternVersion(pattern_id=pattern.id, version_number=(current.version_number if current else 0)+1, image_asset_id=data.image_asset_id, width_mm=data.width_mm, height_mm=data.height_mm, price_cents=data.price_cents); db.add(version); db.flush(); pattern.current_version_id=version.id
    db.commit(); db.refresh(pattern); return pattern
@router.get('/patterns', response_model=list[PatternOut])
def list_patterns(db: Session = Depends(get_db)): return db.scalars(active(select(Pattern), Pattern)).all()
@router.get('/patterns/{pattern_id}/versions', response_model=list[PatternVersionOut])
def versions(pattern_id: UUID, db: Session = Depends(get_db)): return db.scalars(select(PatternVersion).where(PatternVersion.pattern_id == pattern_id).order_by(PatternVersion.version_number)).all()
@router.post('/designs', response_model=DesignOut)
def save_design(data: DesignIn, db: Session = Depends(get_db)):
    design = create_design(db, data); db.commit(); db.refresh(design); items = db.scalars(select(DesignItem).where(DesignItem.design_id == design.id)).all(); return DesignOut(id=design.id, bag_id=design.bag_id, total_price_cents=design.total_price_cents, items=[DesignItemOut.model_validate(item) for item in items])
