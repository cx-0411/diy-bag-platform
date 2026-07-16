from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class APIModel(BaseModel): model_config = ConfigDict(extra='forbid', from_attributes=True)
class AssetOut(APIModel): id: UUID; original_name: str; content_type: str; size_bytes: int; url: str
class AreaIn(APIModel): relative_x: float = Field(ge=0, le=1); relative_y: float = Field(ge=0, le=1); relative_width: float = Field(gt=0, le=1); relative_height: float = Field(gt=0, le=1); width_mm: int = Field(gt=0); height_mm: int = Field(gt=0)
class AreaOut(AreaIn): id: UUID; bag_id: UUID
class BagIn(APIModel): name: str = Field(min_length=1, max_length=200); image_asset_id: UUID; width_mm: int = Field(gt=0); height_mm: int = Field(gt=0); base_price_cents: int = Field(ge=0); status: str = 'draft'
class BagOut(BagIn): id: UUID
class CategoryIn(APIModel): name: str = Field(min_length=1, max_length=100); sort_order: int = 0
class CategoryOut(CategoryIn): id: UUID
class PatternIn(APIModel): category_id: UUID; name: str = Field(min_length=1); production_code: str = Field(min_length=1); status: str = 'draft'; image_asset_id: UUID; width_mm: int = Field(gt=0); height_mm: int = Field(gt=0); price_cents: int = Field(ge=0)
class PatternOut(APIModel): id: UUID; category_id: UUID; name: str; production_code: str; status: str; current_version_id: UUID | None
class PatternVersionOut(APIModel): id: UUID; pattern_id: UUID; version_number: int; image_asset_id: UUID; width_mm: int; height_mm: int; price_cents: int
class DesignItemIn(APIModel): pattern_version_id: UUID; center_x_ratio: float = Field(ge=0, le=1); center_y_ratio: float = Field(ge=0, le=1)
class DesignIn(APIModel): bag_id: UUID; items: list[DesignItemIn] = Field(default_factory=list)
class DesignItemOut(DesignItemIn): id: UUID
class DesignOut(APIModel): id: UUID; bag_id: UUID; total_price_cents: int; items: list[DesignItemOut]
