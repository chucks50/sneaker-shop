from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    addresses = relationship("Address", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="address")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    brand = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    base_price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")
    images = relationship("ProductImage", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String(20), nullable=False)
    color = Column(String(50), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    stock_quantity = Column(Integer, default=0)
    price_override = Column(Float, nullable=True)

    product = relationship("Product", back_populates="variants")
    cart_items = relationship("CartItem", back_populates="variant")
    order_items = relationship("OrderItem", back_populates="variant")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(200), nullable=True)
    is_primary = Column(Boolean, default=False)

    product = relationship("Product", back_populates="images")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    variant = relationship("ProductVariant", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    subtotal = Column(Float, nullable=False)
    shipping_fee = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="orders")
    address = relationship("Address", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    product_name_snapshot = Column(String(200), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    variant = relationship("ProductVariant", back_populates="order_items")
