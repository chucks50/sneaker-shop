from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login_flow():
    payload = {
        "first_name": "Alice",
        "last_name": "Tester",
        "email": "alice@example.com",
        "password": "secret123",
    }

    register_response = client.post("/api/auth/register", json=payload)
    assert register_response.status_code == 200
    assert register_response.json()["email"] == payload["email"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    token = login_response.json()["access_token"]
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == payload["email"]
