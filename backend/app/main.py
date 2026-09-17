from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import create_access_token, hash_password, verify_password, decode_access_token
from app.config import settings
from app.db import Base, SessionLocal, engine, get_db

security = HTTPBearer()


def seed_demo_products():
    db = SessionLocal()
    try:
        if db.query(models.Product).count() >= 0:
            categories = {}
            for name, slug in [
                ("Lifestyle", "lifestyle"),
                ("Running", "running"),
                ("Basketball", "basketball"),
                ("Trail", "trail"),
            ]:
                category = db.query(models.Category).filter_by(slug=slug).first()
                if category is None:
                    category = models.Category(name=name, slug=slug)
                    db.add(category)
                    db.flush()
                categories[slug] = category

            catalog = [
                {
                    "name": "Air Max Pulse",
                    "slug": "air-max-pulse",
                    "brand": "Nike",
                    "description": "A modern lifestyle runner with responsive cushioning and a bold streetwear shape.",
                    "price": 159.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                },
                {
                    "name": "Air Jordan 1 Retro High",
                    "slug": "air-jordan-1-retro-high",
                    "brand": "Jordan",
                    "description": "The iconic high-top basketball silhouette that continues to define sneaker culture.",
                    "price": 189.99,
                    "category": "basketball",
                    "image": "https://images.unsplash.com/photo-1552346154-21d32810aba3",
                },
                {
                    "name": "Dunk Low Retro",
                    "slug": "dunk-low-retro",
                    "brand": "Nike",
                    "description": "A low-profile classic with clean color blocking and everyday versatility.",
                    "price": 119.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519",
                },
                {
                    "name": "Samba OG",
                    "slug": "samba-og",
                    "brand": "adidas",
                    "description": "A terrace classic with a streamlined profile, gum sole, and unmistakable three stripes.",
                    "price": 119.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1518002171953-7f7b0f6fb686",
                },
                {
                    "name": "Campus 00s",
                    "slug": "campus-00s",
                    "brand": "adidas",
                    "description": "A relaxed skate-inspired sneaker with a padded tongue and oversized retro proportions.",
                    "price": 109.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77",
                },
                {
                    "name": "550",
                    "slug": "new-balance-550",
                    "brand": "New Balance",
                    "description": "A vintage basketball-inspired low top with a clean, easy-to-style everyday look.",
                    "price": 129.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1554062614-6da4fa0e0c7a",
                },
                {
                    "name": "990v6",
                    "slug": "new-balance-990v6",
                    "brand": "New Balance",
                    "description": "Premium made-for-running comfort with a refined shape and soft performance cushioning.",
                    "price": 209.99,
                    "category": "running",
                    "image": "https://images.unsplash.com/photo-1539185441755-769473a23570",
                },
                {
                    "name": "Gel-Kayano 31",
                    "slug": "gel-kayano-31",
                    "brand": "ASICS",
                    "description": "A supportive daily trainer designed for stable, comfortable miles.",
                    "price": 199.99,
                    "category": "running",
                    "image": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5",
                },
                {
                    "name": "Cloud 5",
                    "slug": "on-cloud-5",
                    "brand": "On",
                    "description": "Lightweight everyday comfort with a distinctive sole built for smooth city movement.",
                    "price": 149.99,
                    "category": "running",
                    "image": "https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3",
                },
                {
                    "name": "Clifton 9",
                    "slug": "hoka-clifton-9",
                    "brand": "HOKA",
                    "description": "A cushioned road runner with a smooth ride for daily training and long walks.",
                    "price": 149.99,
                    "category": "running",
                    "image": "https://images.unsplash.com/photo-1534653299134-96a44d8b90a0",
                },
                {
                    "name": "Speedcross 6",
                    "slug": "salomon-speedcross-6",
                    "brand": "Salomon",
                    "description": "A trail favorite with aggressive grip and confident footing on rough ground.",
                    "price": 139.99,
                    "category": "trail",
                    "image": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256",
                },
                {
                    "name": "574 Core",
                    "slug": "new-balance-574-core",
                    "brand": "New Balance",
                    "description": "A dependable heritage runner with balanced cushioning and timeless styling.",
                    "price": 99.99,
                    "category": "lifestyle",
                    "image": "https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3",
                },
            ]

            for item in catalog:
                product = db.query(models.Product).filter_by(slug=item["slug"]).first()
                if product is not None:
                    continue

                product = models.Product(
                    name=item["name"],
                    slug=item["slug"],
                    brand=item["brand"],
                    description=item["description"],
                    base_price=item["price"],
                    category_id=categories[item["category"]].id,
                    featured=item["slug"] in {"air-max-pulse", "samba-og", "new-balance-550"},
                    is_active=True,
                )
                db.add(product)
                db.flush()

                for size in ("41", "42", "43"):
                    db.add(
                        models.ProductVariant(
                            product_id=product.id,
                            size=size,
                            color="Black / White",
                            sku=f"{item['slug']}-{size}",
                            stock_quantity=8,
                            price_override=None,
                        )
                    )

                db.add(
                    models.ProductImage(
                        product_id=product.id,
                        url=item["image"],
                        alt_text=item["name"],
                        is_primary=True,
                    )
                )

            db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
seed_demo_products()

app = FastAPI(title="Sneaker Shop API", version="0.1.0")
allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
]
if not allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"access_token": token, "token_type": "bearer", "user": user}


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
    if user is None or not bool(int(user.is_active)): # type: ignore[arg-type]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_admin(current_user: models.User = Depends(get_current_user)):
    if str(current_user.email).lower() != settings.admin_email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@app.get("/api/admin/products", response_model=list[schemas.ProductRead])
def list_admin_products(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return crud.get_admin_products(db)


@app.post("/api/admin/products", response_model=schemas.ProductDetailRead)
def create_admin_product(
    product_data: schemas.ProductAdminCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(models.Product).filter(models.Product.slug == product_data.slug).first():
        raise HTTPException(status_code=400, detail="Product slug already exists")
    category = db.query(models.Category).filter(models.Category.slug == product_data.category_slug).first()
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    return crud.create_product(db, product_data, category)


@app.put("/api/admin/products/{product_id}", response_model=schemas.ProductDetailRead)
def edit_admin_product(
    product_id: int,
    product_data: schemas.ProductAdminUpdate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product_data.slug and product_data.slug != product.slug:
        duplicate = db.query(models.Product).filter(models.Product.slug == product_data.slug).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Product slug already exists")
    category = None
    if product_data.category_slug:
        category = db.query(models.Category).filter(models.Category.slug == product_data.category_slug).first()
        if category is None:
            raise HTTPException(status_code=400, detail="Category not found")
    return crud.update_product(db, product, product_data, category)


@app.delete("/api/admin/products/{product_id}", response_model=schemas.ProductDetailRead)
def deactivate_admin_product(
    product_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, "is_active", False)
    db.commit()
    db.refresh(product)
    return product


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
