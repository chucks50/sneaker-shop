from sqlalchemy.orm import Session

from app import models
from app.auth import hash_password


def get_products(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Product).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_data):
    hashed_password = hash_password(user_data.password)

    new_user = models.User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password_hash=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def create_address(db: Session, user_id: int, address_data):
    new_address = models.Address(
        user_id=user_id,
        street=address_data.street,
        city=address_data.city,
        postal_code=address_data.postal_code,
        country=address_data.country,
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


def get_addresses(db: Session, user_id: int):
    return db.query(models.Address).filter(models.Address.user_id == user_id).all()


def get_cart_items(db: Session, user_id: int):
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()


def get_cart_item(db: Session, item_id: int, user_id: int):
    return (
        db.query(models.CartItem)
        .filter(models.CartItem.id == item_id, models.CartItem.user_id == user_id)
        .first()
    )


def get_cart_item_by_product_variant(db: Session, user_id: int, product_id: int, variant_id: int):
    return (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == user_id,
            models.CartItem.product_id == product_id,
            models.CartItem.variant_id == variant_id,
        )
        .first()
    )


def add_cart_item(db: Session, user_id: int, item_data):
    cart_item = models.CartItem(
        user_id=user_id,
        product_id=item_data.product_id,
        variant_id=item_data.variant_id,
        quantity=item_data.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item_quantity(db: Session, cart_item, new_quantity: int):
    setattr(cart_item, "quantity", int(new_quantity))
    db.commit()
    db.refresh(cart_item)
    return cart_item


def create_order_from_cart(db: Session, user_id: int, address_id: int, payment_method: str):
    cart_items = get_cart_items(db, user_id)
    if not cart_items:
        return None

    address = (
        db.query(models.Address)
        .filter(models.Address.id == address_id, models.Address.user_id == user_id)
        .first()
    )
    if address is None:
        return None

    subtotal = 0.0
    order_items = []

    for cart_item in cart_items:
        product = db.query(models.Product).filter(models.Product.id == cart_item.product_id).first()
        if product is None:
            continue

        variant = (
            db.query(models.ProductVariant)
            .filter(models.ProductVariant.id == cart_item.variant_id)
            .first()
        )
        if variant is None:
            return None

        cart_quantity = int(cart_item.quantity) # type: ignore
        variant_stock = int(variant.stock_quantity) # type: ignore
        if cart_quantity > variant_stock:
            raise ValueError("Not enough stock available")

        unit_price = variant.price_override if variant and variant.price_override is not None else product.base_price
        subtotal += unit_price * cart_quantity

        order_item = models.OrderItem(
            product_id=product.id,
            variant_id=cart_item.variant_id,
            quantity=cart_quantity,
            unit_price=unit_price,
            product_name_snapshot=product.name,
        )
        order_items.append(order_item)

    if not order_items:
        return None

    shipping_fee = 0.0
    total_amount = subtotal + shipping_fee

    order = models.Order(
        user_id=user_id,
        address_id=address_id,
        status="pending",
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total_amount=total_amount,
        payment_method=payment_method,
        created_at=__import__("datetime").datetime.utcnow(),
    )

    db.add(order)
    db.flush()

    for item in order_items:
        item.order_id = order.id
        db.add(item)

    for cart_item in cart_items:
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == cart_item.variant_id).first()
        if variant is not None:
            current_stock = int(variant.stock_quantity) # type: ignore
            new_stock = current_stock - int(cart_item.quantity) # type: ignore
            setattr(variant, "stock_quantity", new_stock)
        db.delete(cart_item)

    db.commit()
    db.refresh(order)
    return order


def get_orders(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).order_by(models.Order.created_at.desc()).all()


def get_order(db: Session, order_id: int, user_id: int):
    return (
        db.query(models.Order)
        .filter(models.Order.id == order_id, models.Order.user_id == user_id)
        .first()
    )


def update_order_status(db: Session, order, new_status: str):
    allowed_statuses = {"pending", "paid", "shipped"}
    if new_status not in allowed_statuses:
        raise ValueError("Status must be one of: pending, paid, shipped")

    setattr(order, "status", new_status)
    db.commit()
    db.refresh(order)
    return order
