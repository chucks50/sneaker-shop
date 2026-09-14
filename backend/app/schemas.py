from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


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


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AddressCreate(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str


class AddressRead(AddressCreate):
    id: int
    user_id: int
    is_default: bool = False

    model_config = ConfigDict(from_attributes=True)


class CartItemCreate(BaseModel):
    product_id: int
    variant_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemRead(BaseModel):
    id: int
    user_id: int
    product_id: int
    variant_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderItemRead(BaseModel):
    id: int
    order_id: int
    product_id: int
    variant_id: int
    quantity: int
    unit_price: float
    product_name_snapshot: str

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    address_id: int
    status: str
    subtotal: float
    shipping_fee: float
    total_amount: float
    payment_method: str
    created_at: datetime
    items: list[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)


class CheckoutRequest(BaseModel):
    address_id: int
    payment_method: str = "card"


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "paid", "shipped"]
