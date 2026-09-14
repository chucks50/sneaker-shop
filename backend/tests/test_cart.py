from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cart_flow():
    email = "cart-user@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Cart",
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

    product_response = client.get("/api/products/1")
    assert product_response.status_code == 200
    variant_id = product_response.json()["variants"][0]["id"]

    add_response = client.post(
        "/api/cart/items",
        headers={"Authorization": f"Bearer {token}"},
        json={"product_id": 1, "variant_id": variant_id, "quantity": 2},
    )
    assert add_response.status_code == 200
    added_item = add_response.json()
    assert added_item["quantity"] == 2
    assert added_item["product_id"] == 1

    cart_response = client.get(
        "/api/cart",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cart_response.status_code == 200
    payload = cart_response.json()
    assert len(payload) >= 1
    item_id = payload[0]["id"]

    update_response = client.put(
        f"/api/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"quantity": 3},
    )
    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 3

    delete_response = client.delete(
        f"/api/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["detail"] == "Item removed from cart"
