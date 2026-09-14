from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_products_returns_200():
    response = client.get("/api/products")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)


def test_get_product_detail_returns_200_for_existing_product():
    response = client.get("/api/products/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
