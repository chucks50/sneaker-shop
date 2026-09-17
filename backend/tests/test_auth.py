import importlib
import os

from fastapi.testclient import TestClient

from app import config, main as main_module

client = TestClient(main_module.app)


def test_cors_allowed_origins_can_be_overridden_for_deployment():
    original = os.environ.get("CORS_ALLOWED_ORIGINS")
    os.environ["CORS_ALLOWED_ORIGINS"] = "https://shop.example.com,https://admin.example.com"

    try:
        importlib.reload(config)
        importlib.reload(main_module)
        cors_origins = next(
            middleware.kwargs["allow_origins"]
            for middleware in main_module.app.user_middleware
            if getattr(middleware, "kwargs", {}).get("allow_origins")
        )
        assert "https://shop.example.com" in cors_origins
        assert "https://admin.example.com" in cors_origins
    finally:
        if original is None:
            os.environ.pop("CORS_ALLOWED_ORIGINS", None)
        else:
            os.environ["CORS_ALLOWED_ORIGINS"] = original
        importlib.reload(config)
        importlib.reload(main_module)


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
