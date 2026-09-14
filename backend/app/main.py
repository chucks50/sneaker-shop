from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import create_access_token, hash_password, verify_password, decode_access_token
from app.config import settings
from app.db import Base, SessionLocal, engine, get_db

security = HTTPBearer()


def seed_demo_products():
    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            category = models.Category(name="Running", slug="running")
            db.add(category)
            db.flush()

            product = models.Product(
                name="Air Max Pulse",
                slug="air-max-pulse",
                brand="Nike",
                description="A modern running silhouette with responsive cushioning.",
                base_price=159.99,
                category_id=category.id,
                featured=True,
                is_active=True,
            )
            db.add(product)
            db.flush()

            db.add(
                models.ProductVariant(
                    product_id=product.id,
                    size="42",
                    color="Black",
                    sku="NKE-AM-42-BLK",
                    stock_quantity=10,
                    price_override=None,
                )
            )
            db.add(
                models.ProductVariant(
                    product_id=product.id,
                    size="43",
                    color="Black",
                    sku="NKE-AM-43-BLK",
                    stock_quantity=8,
                    price_override=None,
                )
            )
            db.add(
                models.ProductImage(
                    product_id=product.id,
                    url="https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                    alt_text="Nike Air Max Pulse",
                    is_primary=True,
                )
            )

            db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
seed_demo_products()

app = FastAPI(title="Sneaker Shop API", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}


@app.get("/")
def root():
    return {"message": "Sneaker Shop API"}


@app.get("/api/products", response_model=list[schemas.ProductRead])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products


@app.get("/api/products/{product_id}", response_model=schemas.ProductDetailRead)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/auth/register", response_model=schemas.UserRead)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, str(user_data.email))
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(db, user_data)
    return user


@app.post("/api/auth/login", response_model=schemas.Token)
def login_user(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, str(user_data.email))
    stored_hash = str(user.password_hash) if user else ""
    if not user or not verify_password(user_data.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = int(user.id) # type: ignore
    token = create_access_token({"sub": str(user_id), "email": user.email})
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


@app.get("/api/auth/me", response_model=schemas.UserRead)
def get_authenticated_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/api/addresses", response_model=schemas.AddressRead)
def create_address(
    address_data: schemas.AddressCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    return crud.create_address(db, user_id, address_data)


@app.get("/api/addresses", response_model=list[schemas.AddressRead])
def list_addresses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    return crud.get_addresses(db, user_id)


@app.get("/api/cart", response_model=list[schemas.CartItemRead])
def get_cart(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = int(current_user.id) # type: ignore
    return crud.get_cart_items(db, user_id)


@app.post("/api/cart/items", response_model=schemas.CartItemRead)
def add_item_to_cart(
    item_data: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if item_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    variant = (
        db.query(models.ProductVariant)
        .filter(
            models.ProductVariant.id == item_data.variant_id,
            models.ProductVariant.product_id == item_data.product_id,
        )
        .first()
    )
    if variant is None:
        raise HTTPException(status_code=404, detail="Product variant not found")

    user_id = int(current_user.id) # type: ignore
    existing_item = crud.get_cart_item_by_product_variant(
        db,
        user_id,
        item_data.product_id,
        item_data.variant_id,
    )
    existing_quantity = int(existing_item.quantity) if existing_item else 0 # type: ignore
    requested_quantity = item_data.quantity + existing_quantity
    available_stock = int(variant.stock_quantity) # type: ignore
    if requested_quantity > available_stock:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    if existing_item:
        setattr(existing_item, "quantity", existing_quantity + item_data.quantity)
        db.commit()
        db.refresh(existing_item)
        return existing_item

    return crud.add_cart_item(db, user_id, item_data)


@app.put("/api/cart/items/{item_id}", response_model=schemas.CartItemRead)
def update_cart_item_quantity(
    item_id: int,
    item_data: schemas.CartItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if item_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    user_id = int(current_user.id) # type: ignore
    cart_item = crud.get_cart_item(db, item_id, user_id)
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return crud.update_cart_item_quantity(db, cart_item, item_data.quantity)


@app.delete("/api/cart/items/{item_id}")
def remove_cart_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    cart_item = crud.get_cart_item(db, item_id, user_id)
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()
    return {"detail": "Item removed from cart"}


@app.post("/api/orders/checkout", response_model=schemas.OrderRead)
def checkout_order(
    checkout_data: schemas.CheckoutRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    try:
        order = crud.create_order_from_cart(
            db,
            user_id,
            checkout_data.address_id,
            checkout_data.payment_method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if order is None:
        raise HTTPException(status_code=400, detail="Cart is empty or address is invalid")

    return order


@app.get("/api/orders", response_model=list[schemas.OrderRead])
def list_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    return crud.get_orders(db, user_id)


@app.get("/api/orders/{order_id}", response_model=schemas.OrderRead)
def get_order_detail(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    order = crud.get_order(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/api/orders/{order_id}/status", response_model=schemas.OrderRead)
def update_order_status(
    order_id: int,
    status_data: schemas.OrderStatusUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) # type: ignore
    order = crud.get_order(db, order_id, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    updated_order = crud.update_order_status(db, order, status_data.status)
    return updated_order
