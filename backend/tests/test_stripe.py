import hashlib
import hmac
import json
import time

import stripe
from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app import models

client = TestClient(app)


def stub_stripe_checkout(monkeypatch, session_id: str):
    class FakeSession:
        def __init__(self, session_id_: str):
            self.id = session_id_
            self.url = f"https://checkout.stripe.com/{session_id_}"

    def fake_create(**kwargs):
        return FakeSession(session_id)

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))


def register_and_login(email: str):
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Stripe",
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
    return login_response.json()["access_token"]


def create_address(token: str):
    response = client.post(
        "/api/addresses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "street": "North Street 10",
            "city": "Utrecht",
            "postal_code": "3511AA",
            "country": "Netherlands",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_checkout_event(order_id: int, session_id: str = "cs_test_123"):
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        amount_total = int(round(order.total_amount * 100))
    finally:
        db.close()

    payload = {
        "id": "evt_test_123",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "payment_intent": "pi_test_123",
                "payment_status": "paid",
                "metadata": {"order_id": str(order_id), "user_id": "1"},
                "amount_total": amount_total,
                "currency": settings.stripe_currency,
            }
        },
    }
    secret = settings.stripe_webhook_secret or "whsec_test_secret"
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return raw_body, f"t={timestamp},v1={signature}"


def test_checkout_session_requires_authentication():
    response = client.post(
        "/api/checkout/create-session",
        json={"address_id": 1},
    )
    assert response.status_code == 401


def test_checkout_session_rejects_empty_cart(monkeypatch):
    token = register_and_login("empty-cart@example.com")
    address_id = create_address(token)

    response = client.post(
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_checkout_session_uses_database_prices_not_frontend(monkeypatch):
    stub_stripe_checkout(monkeypatch, "cs_test_db_price")
    token = register_and_login("db-price@example.com")
    address_id = create_address(token)

    db = SessionLocal()
    try:
        product = db.query(models.Product).first()
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.id).first()
        product_id = product.id
        variant_id = variant.id
        variant.price_override = 49.99
        db.commit()
    finally:
        db.close()

    cart_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product_id, "variant_id": variant_id, "quantity": 1},
    )
    assert cart_response.status_code == 200

    response = client.post(
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] > 0
    assert body["checkout_url"].startswith("https://checkout.stripe.com/")
    assert body["session_id"] == "cs_test_db_price"


def test_checkout_session_uses_stripe_dynamic_payment_methods(monkeypatch):
    captured = {}

    class FakeSession:
        def __init__(self, session_id_: str):
            self.id = session_id_
            self.url = f"https://checkout.stripe.com/{session_id_}"

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakeSession("cs_dashboard_methods")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    token = register_and_login("dashboard-payment-methods@example.com")
    address_id = create_address(token)

    db = SessionLocal()
    try:
        product = db.query(models.Product).first()
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.id).first()
        product_id = product.id
        variant_id = variant.id
    finally:
        db.close()

    cart_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product_id, "variant_id": variant_id, "quantity": 1},
    )
    assert cart_response.status_code == 200

    response = client.post(
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )

    assert response.status_code == 200
    assert "payment_method_types" not in captured
    assert captured["metadata"]["order_id"] == str(response.json()["order_id"])
    assert captured["metadata"]["user_id"]

    monkeypatch.setattr(
        stripe.checkout.Session,
        "retrieve",
        staticmethod(lambda session_id: {
            "id": session_id,
            "payment_status": "paid",
            "metadata": {"order_id": str(response.json()["order_id"]), "user_id": captured["metadata"]["user_id"]},
        }),
    )
    status_response = client.get(
        "/api/checkout/session-status",
        params={"session_id": "cs_dashboard_methods"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["payment_status"] == "paid"


def test_valid_successful_webhook_marks_order_paid(monkeypatch):
    stub_stripe_checkout(monkeypatch, "cs_test_success")
    token = register_and_login("webhook-success@example.com")
    address_id = create_address(token)

    db = SessionLocal()
    try:
        product = db.query(models.Product).first()
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.id).first()
        product_id = product.id
        variant_id = variant.id
    finally:
        db.close()

    cart_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product_id, "variant_id": variant_id, "quantity": 1},
    )
    assert cart_response.status_code == 200

    checkout_response = client.post(
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )
    assert checkout_response.status_code == 200
    order_id = checkout_response.json()["order_id"]

    payload_body, payload_signature = create_checkout_event(order_id, session_id="cs_test_success")
    webhook_response = client.post(
        "/api/webhooks/stripe",
        content=payload_body,
        headers={"stripe-signature": payload_signature},
    )

    assert webhook_response.status_code == 200

    order = SessionLocal().query(models.Order).filter(models.Order.id == order_id).first()
    assert order is not None
    assert order.status == "paid"
    assert order.payment_status == "paid"
    assert order.stripe_checkout_session_id == "cs_test_success"
    assert order.stripe_payment_intent_id == "pi_test_123"


def test_repeated_webhook_events_are_idempotent(monkeypatch):
    stub_stripe_checkout(monkeypatch, "cs_test_repeat")
    token = register_and_login("webhook-idempotent@example.com")
    address_id = create_address(token)

    db = SessionLocal()
    try:
        product = db.query(models.Product).first()
        variant = db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product.id).first()
        product_id = product.id
        variant_id = variant.id
    finally:
        db.close()

    client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": product_id, "variant_id": variant_id, "quantity": 2},
    )

    checkout_response = client.post(
        "/api/checkout/create-session",
        headers={"Authorization": f"Bearer {token}"},
        json={"address_id": address_id},
    )
    order_id = checkout_response.json()["order_id"]

    event_body, signature = create_checkout_event(order_id, session_id="cs_test_repeat")
    first = client.post("/api/webhooks/stripe", content=event_body, headers={"stripe-signature": signature})
    second = client.post("/api/webhooks/stripe", content=event_body, headers={"stripe-signature": signature})

    assert first.status_code == 200
    assert second.status_code == 200

    order = SessionLocal().query(models.Order).filter(models.Order.id == order_id).first()
    assert order.status == "paid"
    assert order.payment_status == "paid"
    assert order.stripe_checkout_session_id == "cs_test_repeat"
