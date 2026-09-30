from fastapi.testclient import TestClient
import stripe

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app import models

client = TestClient(app)


def stub_checkout_session(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_checkout")

    class FakeSession:
        id = "cs_test_order_flow"
        url = "https://checkout.stripe.com/cs_test_order_flow"

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(lambda **kwargs: FakeSession()))


def test_checkout_flow(monkeypatch):
    stub_checkout_session(monkeypatch)
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
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )
    assert checkout_response.status_code == 200
    assert checkout_response.json()["checkout_url"].startswith("https://checkout.stripe.com/")
    orders_response = client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_response.status_code == 200
    assert len(orders_response.json()) == 1
    assert orders_response.json()[0]["payment_method"] == "stripe"
    assert orders_response.json()[0]["payment_status"] == "pending"



def test_order_status_update_and_detail(monkeypatch):
    stub_checkout_session(monkeypatch)
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
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_response.json()["id"]},
    )
    assert checkout_response.status_code == 200
    order_id = checkout_response.json()["order_id"]

    patch_response = client.patch(
        f"/api/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "paid"},
    )
    assert patch_response.status_code == 403

    detail_response = client.get(
        f"/api/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["payment_status"] == "pending"


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
