import os

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_api_token


TEST_TOKEN = "test-token"


@pytest.fixture(autouse=True)
def set_api_token_env(monkeypatch):
    monkeypatch.setenv("API_TOKEN", TEST_TOKEN)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(token: str = TEST_TOKEN):
    return {"Authorization": f"Bearer {token}"}


def test_get_api_token_reads_env():
    os.environ["API_TOKEN"] = "abc123"
    assert get_api_token() == "abc123"


def test_health_requires_auth(client):
    response = client.get("/health")
    assert response.status_code == 403 or response.status_code == 401


def test_health_with_valid_token(client):
    response = client.get("/health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_items_with_valid_token(client):
    response = client.get("/items", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("id" in item and "name" in item for item in data)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "AWS Sample Python App" in response.text


def test_items_with_invalid_token(client):
    response = client.get("/items", headers=auth_headers("wrong"))
    assert response.status_code == 401
