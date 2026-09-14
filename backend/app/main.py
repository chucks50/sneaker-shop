from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db import Base, SessionLocal, engine, get_db


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
