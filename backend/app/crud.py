from sqlalchemy.orm import Session

from app import models
from app.auth import hash_password


def get_products(db: Session, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Product)
        .filter(models.Product.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_admin_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def create_product(db: Session, product_data, category):
    product = models.Product(
        name=product_data.name,
        slug=product_data.slug,
        brand=product_data.brand,
        description=product_data.description,
        base_price=product_data.base_price,
        category_id=category.id,
        featured=product_data.featured,
        is_active=True,
    )
    db.add(product)
    db.flush()

    variants = product_data.variants or [
        {"size": "42", "color": "Black / White", "stock_quantity": 0, "price_override": None}
    ]
    for index, variant_data in enumerate(variants):
        variant = variant_data if isinstance(variant_data, dict) else variant_data.model_dump()
        db.add(models.ProductVariant(
            product_id=product.id,
            size=variant["size"],
            color=variant["color"],
            sku=f"{product.slug}-{variant['size']}-{index}",
            stock_quantity=variant["stock_quantity"],
            price_override=variant["price_override"],
        ))

    if product_data.image_url:
        db.add(models.ProductImage(
            product_id=product.id,
            url=product_data.image_url,
            alt_text=product_data.name,
            is_primary=True,
        ))

    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product, product_data, category=None):
    updates = product_data.model_dump(exclude_unset=True, exclude={"category_slug", "image_url", "variants"})
    for field, value in updates.items():
        setattr(product, field, value)
    if category is not None:
        product.category_id = category.id
    if product_data.image_url is not None:
        image = db.query(models.ProductImage).filter_by(product_id=product.id, is_primary=True).first()
        if image is None:
            image = models.ProductImage(product_id=product.id, is_primary=True, alt_text=product.name)
            db.add(image)
        image.url = product_data.image_url
        image.alt_text = product.name
    if product_data.variants is not None:
        db.query(models.ProductVariant).filter_by(product_id=product.id).delete()
        for index, variant_data in enumerate(product_data.variants):
            db.add(models.ProductVariant(
                product_id=product.id,
                size=variant_data.size,
                color=variant_data.color,
                sku=f"{product.slug}-{variant_data.size}-{index}",
                stock_quantity=variant_data.stock_quantity,
                price_override=variant_data.price_override,
            ))
    db.commit()
    db.refresh(product)
    return product


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
