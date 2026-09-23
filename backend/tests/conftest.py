import os

import pytest

os.environ["DATABASE_URL"] = "sqlite://"

from app import models
from app.db import SessionLocal, Base, engine
from app.main import seed_demo_products

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_database():
    db = SessionLocal()
    try:
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.CartItem).delete()
        db.query(models.Address).delete()
        db.query(models.Review).delete()
        db.query(models.User).delete()
        db.query(models.ProductImage).delete()
        db.query(models.ProductVariant).delete()
        db.query(models.Product).delete()
        db.query(models.Category).delete()
        db.commit()
        seed_demo_products()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.CartItem).delete()
        db.query(models.Address).delete()
        db.query(models.Review).delete()
        db.query(models.User).delete()
        db.query(models.ProductImage).delete()
        db.query(models.ProductVariant).delete()
        db.query(models.Product).delete()
        db.query(models.Category).delete()
        db.commit()
    finally:
        db.close()
