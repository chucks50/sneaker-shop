from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def admin_token():
    client.post(
        "/api/auth/register",
        json={
            "first_name": "Store",
            "last_name": "Admin",
            "email": "admin@example.com",
            "password": "secret123",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "secret123"},
    )
    return response.json()["access_token"]


def test_admin_can_create_update_and_deactivate_product():
    headers = {"Authorization": f"Bearer {admin_token()}"}
    create_response = client.post(
        "/api/admin/products",
        headers=headers,
        json={
            "name": "Test Runner",
            "slug": "test-runner",
            "brand": "Test Brand",
            "description": "A product created by the admin test.",
            "base_price": 89.99,
            "category_slug": "running",
            "variants": [{"size": "42", "color": "Blue", "stock_quantity": 5}],
        },
    )
    assert create_response.status_code == 200
    product_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/admin/products/{product_id}",
        headers=headers,
        json={"base_price": 99.99, "is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["base_price"] == 99.99

    delete_response = client.delete(f"/api/admin/products/{product_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False

    public_products = client.get("/api/products").json()
    assert all(product["id"] != product_id for product in public_products)


def test_regular_user_cannot_manage_products():
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Regular",
            "last_name": "User",
            "email": "regular@example.com",
            "password": "secret123",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/auth/login",
        json={"email": "regular@example.com", "password": "secret123"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = client.get("/api/admin/products", headers=headers)
    assert response.status_code == 403
