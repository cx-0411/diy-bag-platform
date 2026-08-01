from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AppSetting, Bag, CartItem, Design, EmbroideryArea, FileAsset, Order, Pattern, PatternCategory, PatternVersion, DesignItem
from app.schemas import AdminOrderOut, AreaIn, AreaOut, AssetOut, BagIn, BagOut, CartItemIn, CartItemOut, CatalogBagOut, CatalogPatternOut, CategoryIn, CategoryOut, CategoryUpdateIn, DesignIn, DesignItemOut, DesignLimitIn, DesignLimitOut, DesignOut, OrderCreateIn, OrderOut, OrderStatusIn, PatternIn, PatternOut, PatternVersionOut
from app.services.designs import create_design
from app.services.orders import create_order, mock_pay, update_production_status
from app.services.rendering import render_design_preview, render_order_production
from app.services.storage import StorageService
router = APIRouter()
def active(statement, model): return statement.where(model.deleted_at.is_(None))
@router.get('/settings/design-limit', response_model=DesignLimitOut)
def get_design_limit(db: Session = Depends(get_db)):
    return DesignLimitOut(max_drafts=db.scalar(select(AppSetting.value_int).where(AppSetting.key == 'max_design_drafts')) or 3)
@router.put('/admin/settings/design-limit', response_model=DesignLimitOut)
def set_design_limit(data: DesignLimitIn, db: Session = Depends(get_db)):
    item = db.scalar(select(AppSetting).where(AppSetting.key == 'max_design_drafts'))
    if item: item.value_int = data.max_drafts
    else:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        db.add(AppSetting(key='max_design_drafts', value_int=data.max_drafts, created_at=now, updated_at=now))
    db.commit(); return DesignLimitOut(max_drafts=data.max_drafts)
@router.post('/files', response_model=AssetOut)
def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type or not file.content_type.startswith('image/'): raise HTTPException(415, 'Only image uploads are supported')
    storage = StorageService(); key, size = storage.save_upload(file); asset = FileAsset(original_name=file.filename or key, storage_key=key, content_type=file.content_type, size_bytes=size); db.add(asset); db.commit(); db.refresh(asset); return AssetOut(id=asset.id, original_name=asset.original_name, content_type=asset.content_type, size_bytes=asset.size_bytes, url=storage.url(key))
@router.get('/files/{key}')
def download(key: str, db: Session = Depends(get_db)):
    asset = db.scalar(select(FileAsset).where(FileAsset.storage_key == key))
    if not asset or asset.visibility != 'public': raise HTTPException(404, 'File not found')
    target = Path(StorageService().root) / key
    if not target.is_file(): raise HTTPException(404, 'File not found')
    return FileResponse(target)
@router.get('/file-assets/{asset_id}', response_model=AssetOut)
def get_asset(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.get(FileAsset, asset_id)
    if not asset: raise HTTPException(404, 'File asset not found')
    return AssetOut(id=asset.id, original_name=asset.original_name, content_type=asset.content_type, size_bytes=asset.size_bytes, url=StorageService().url(asset.storage_key))
@router.post('/bags', response_model=BagOut)
def create_bag(data: BagIn, db: Session = Depends(get_db)):
    if not db.get(FileAsset, data.image_asset_id): raise HTTPException(422, 'Bag image does not exist')
    bag = Bag(**data.model_dump()); db.add(bag); db.commit(); db.refresh(bag); return bag
@router.get('/bags', response_model=list[BagOut])
def list_bags(db: Session = Depends(get_db)): return db.scalars(active(select(Bag), Bag)).all()
@router.get('/catalog/bags', response_model=list[CatalogBagOut])
def list_catalog_bags(db: Session = Depends(get_db)):
    rows = db.execute(select(Bag, EmbroideryArea, FileAsset).join(EmbroideryArea, EmbroideryArea.bag_id == Bag.id).join(FileAsset, FileAsset.id == Bag.image_asset_id).where(Bag.deleted_at.is_(None), Bag.status == 'published')).all()
    storage = StorageService()
    return [CatalogBagOut(id=bag.id, name=bag.name, image_url=storage.url(asset.storage_key), width_mm=bag.width_mm, height_mm=bag.height_mm, base_price_cents=bag.base_price_cents, embroidery_area=AreaOut.model_validate(area)) for bag, area, asset in rows]
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
@router.get('/catalog/pattern-categories', response_model=list[CategoryOut])
def list_catalog_categories(db: Session = Depends(get_db)):
    return db.scalars(active(select(PatternCategory).where(PatternCategory.is_active.is_(True)), PatternCategory).order_by(PatternCategory.sort_order, PatternCategory.name)).all()
@router.put('/pattern-categories/{category_id}', response_model=CategoryOut)
def update_category(category_id: UUID, data: CategoryUpdateIn, db: Session = Depends(get_db)):
    category = db.scalar(active(select(PatternCategory).where(PatternCategory.id == category_id), PatternCategory))
    if not category: raise HTTPException(404, 'Pattern category not found')
    for key, value in data.model_dump().items(): setattr(category, key, value)
    db.commit(); db.refresh(category); return category
@router.post('/pattern-categories/{category_id}/archive', response_model=CategoryOut)
def archive_category(category_id: UUID, db: Session = Depends(get_db)):
    category = db.scalar(active(select(PatternCategory).where(PatternCategory.id == category_id), PatternCategory))
    if not category: raise HTTPException(404, 'Pattern category not found')
    from datetime import datetime, timezone
    category.is_active = False; category.deleted_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(category); return category
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
@router.get('/catalog/patterns', response_model=list[CatalogPatternOut])
def list_catalog_patterns(db: Session = Depends(get_db)):
    rows = db.execute(select(Pattern, PatternVersion, FileAsset).join(PatternVersion, PatternVersion.id == Pattern.current_version_id).join(FileAsset, FileAsset.id == PatternVersion.image_asset_id).where(Pattern.deleted_at.is_(None), Pattern.status == 'published')).all()
    storage = StorageService()
    return [CatalogPatternOut(id=pattern.id, category_id=pattern.category_id, name=pattern.name, image_url=storage.url(asset.storage_key), width_mm=version.width_mm, height_mm=version.height_mm, price_cents=version.price_cents, pattern_version_id=version.id) for pattern, version, asset in rows]
@router.get('/patterns/{pattern_id}/versions', response_model=list[PatternVersionOut])
def versions(pattern_id: UUID, db: Session = Depends(get_db)): return db.scalars(select(PatternVersion).where(PatternVersion.pattern_id == pattern_id).order_by(PatternVersion.version_number)).all()
@router.post('/designs', response_model=DesignOut)
def save_design(data: DesignIn, db: Session = Depends(get_db)):
    design = create_design(db, data); db.commit(); db.refresh(design); items = db.scalars(select(DesignItem).where(DesignItem.design_id == design.id)).all(); return DesignOut(id=design.id, bag_id=design.bag_id, total_price_cents=design.total_price_cents, items=[DesignItemOut.model_validate(item) for item in items])
@router.get('/designs', response_model=list[DesignOut])
def list_designs(client_key: str, db: Session = Depends(get_db)):
    # The mobile editor shows customer-facing names as 设计 1、设计 2…,
    # so return saved designs in their original creation order.
    designs = db.scalars(select(Design).where(Design.client_key == client_key).order_by(Design.created_at.asc())).all()
    return [DesignOut(id=design.id, bag_id=design.bag_id, total_price_cents=design.total_price_cents, items=[DesignItemOut.model_validate(item) for item in db.scalars(select(DesignItem).where(DesignItem.design_id == design.id).order_by(DesignItem.z_index, DesignItem.created_at))]) for design in designs]
@router.delete('/designs/{design_id}', status_code=204)
def delete_design(design_id: UUID, client_key: str, db: Session = Depends(get_db)):
    design = db.scalar(select(Design).where(Design.id == design_id, Design.client_key == client_key))
    if not design: raise HTTPException(404, 'Design not found')
    if db.scalar(select(CartItem.id).where(CartItem.design_id == design.id)) or db.scalar(select(Order.id).where(Order.design_id == design.id)):
        raise HTTPException(409, 'Design is referenced by a cart item or order and cannot be deleted')
    db.query(DesignItem).filter(DesignItem.design_id == design.id).delete()
    db.delete(design); db.commit()
@router.post('/cart-items', response_model=CartItemOut)
def add_cart_item(data: CartItemIn, db: Session = Depends(get_db)):
    design = db.scalar(select(Design).where(Design.id == data.design_id, Design.client_key == data.client_key))
    if not design: raise HTTPException(404, 'Design not found')
    item = CartItem(client_key=data.client_key, design_id=design.id); db.add(item); db.commit(); db.refresh(item)
    return CartItemOut(id=item.id, design_id=item.design_id, created_at=item.created_at, total_price_cents=design.total_price_cents)
@router.get('/cart-items', response_model=list[CartItemOut])
def list_cart_items(client_key: str, db: Session = Depends(get_db)):
    rows = db.execute(select(CartItem, Design).join(Design, Design.id == CartItem.design_id).where(CartItem.client_key == client_key).order_by(CartItem.created_at.desc())).all()
    return [CartItemOut(id=item.id, design_id=design.id, created_at=item.created_at, total_price_cents=design.total_price_cents) for item, design in rows]
@router.delete('/cart-items/{cart_item_id}', status_code=204)
def delete_cart_item(cart_item_id: UUID, client_key: str, db: Session = Depends(get_db)):
    item = db.scalar(select(CartItem).where(CartItem.id == cart_item_id, CartItem.client_key == client_key))
    if not item: raise HTTPException(404, 'Cart item not found')
    db.delete(item); db.commit()
@router.post('/designs/{design_id}/preview', response_model=AssetOut)
def render_preview(design_id: UUID, client_key: str, db: Session = Depends(get_db)):
    design = db.scalar(select(Design).where(Design.id == design_id, Design.client_key == client_key))
    if not design: raise HTTPException(404, 'Design not found')
    asset = render_design_preview(db, design); db.commit(); db.refresh(asset)
    return AssetOut(id=asset.id, original_name=asset.original_name, content_type=asset.content_type, size_bytes=asset.size_bytes, url=StorageService().url(asset.storage_key))
@router.post('/orders', response_model=OrderOut)
def create_mock_order(data: OrderCreateIn, db: Session = Depends(get_db)):
    order = create_order(db, data.design_id, data.client_key)
    # Persist a private, watermark-free production image with the immutable order snapshot.
    # The merchant can therefore receive the production material as soon as an order exists.
    render_order_production(db, order)
    db.commit(); db.refresh(order); return order
@router.post('/orders/{order_id}/mock-pay', response_model=OrderOut)
def pay_mock_order(order_id: UUID, client_key: str, db: Session = Depends(get_db)):
    order = mock_pay(db, order_id, client_key); db.commit(); db.refresh(order); return order
@router.get('/orders', response_model=list[OrderOut])
def list_customer_orders(client_key: str, db: Session = Depends(get_db)):
    return db.scalars(select(Order).where(Order.client_key == client_key).order_by(Order.created_at.desc())).all()
@router.get('/admin/orders', response_model=list[AdminOrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order).order_by(Order.created_at.desc())).all()
@router.post('/admin/orders/{order_id}/status', response_model=AdminOrderOut)
def set_order_status(order_id: UUID, data: OrderStatusIn, db: Session = Depends(get_db)):
    order = update_production_status(db, order_id, data.status, data.tracking_no); db.commit(); db.refresh(order); return order
@router.get('/admin/orders/{order_id}/production-image')
def get_production_image(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order: raise HTTPException(404, 'Order not found')
    asset = render_order_production(db, order); db.commit()
    return FileResponse(StorageService().path_for(asset.storage_key), media_type=asset.content_type, filename=asset.original_name)
