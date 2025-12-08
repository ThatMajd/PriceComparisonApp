from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class VendorResponse(BaseModel):
    id: int
    name: str
    website_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    traklin_sku: int
    vendor_sku: str
    vendor_id: Optional[int]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScrapedProductSchema(BaseModel):
    SKU: str
    name: str
    offers__price: Optional[int]
    orig_price: Optional[int]
    disc_price: Optional[int]
    currency: str
    url: str
    images: List[str]
    description: Optional[str]
    availability: Optional[str]
    item_condition: Optional[str]
    brand: Optional[str]
    metadata: Optional[Dict[str, Any]]

class ScrapedResult(BaseModel):
    vendor: str
    product: ScrapedProductSchema
