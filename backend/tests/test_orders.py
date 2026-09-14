from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app import models

client = TestClient(app)


def test_checkout_flow():
    email = "checkout-user@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Checkout",
            "last_name": "User",
            "email": email,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    add_to_cart_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": 1, "variant_id": 1, "quantity": 2},
    )
    assert add_to_cart_response.status_code == 200

    address_response = client.post(
        "/api/addresses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "street": "Main Street 123",
            "city": "Amsterdam",
            "postal_code": "1000AA",
            "country": "Netherlands",
        },
    )
    assert address_response.status_code == 200
    address_id = address_response.json()["id"]

    checkout_response = client.post(
        "/api/orders/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id, "payment_method": "card"},
    )
    assert checkout_response.status_code == 200
    payload = checkout_response.json()
    assert payload["status"] == "pending"
    assert payload["user_id"] > 0
    assert payload["total_amount"] > 0
    assert len(payload["items"]) >= 1

    orders_response = client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_response.status_code == 200
    assert len(orders_response.json()) >= 1


def test_order_status_update_and_detail():
    email = "order-status@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Order",
            "last_name": "Status",
            "email": email,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    )
    token = login_response.json()["access_token"]

    cart_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": 1, "variant_id": 1, "quantity": 1},
    )
    assert cart_response.status_code == 200

    address_response = client.post(
        "/api/addresses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "street": "Second Street 22",
            "city": "Rotterdam",
            "postal_code": "3000AA",
            "country": "Netherlands",
        },
    )
    assert address_response.status_code == 200

    checkout_response = client.post(
        "/api/orders/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_response.json()["id"], "payment_method": "card"},
    )
    assert checkout_response.status_code == 200
    order_id = checkout_response.json()["id"]

    patch_response = client.patch(
        f"/api/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "paid"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "paid"

    detail_response = client.get(
        f"/api/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "paid"


def test_checkout_rejects_insufficient_stock():
    email = "stock-check@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Stock",
            "last_name": "Check",
            "email": email,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    )
    token = login_response.json()["access_token"]

    db = SessionLocal()
    try:
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == 1).first()
        variant.stock_quantity = 1
        db.commit()
    finally:
        db.close()

    add_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": 1, "variant_id": 1, "quantity": 2},
    )
    assert add_response.status_code == 400
    assert add_response.json()["detail"] == "Not enough stock available"
