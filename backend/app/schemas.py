from typing import Optional

from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ProductVariantRead(BaseModel):
    id: int
    size: str
    color: str
    sku: str
    stock_quantity: int
    price_override: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ProductImageRead(BaseModel):
    id: int
    url: str
    alt_text: Optional[str] = None
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class ProductRead(BaseModel):
    id: int
    name: str
    slug: str
    brand: str
    description: str
    base_price: float
    category_id: int
    featured: bool
    is_active: bool
    category: Optional[CategoryRead] = None
    variants: list[ProductVariantRead] = []
    images: list[ProductImageRead] = []

    model_config = ConfigDict(from_attributes=True)


class ProductDetailRead(ProductRead):
    pass
