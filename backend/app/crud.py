from sqlalchemy.orm import Session

from app import models


def get_products(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Product).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()
