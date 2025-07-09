import pytest
from fastapi.testclient import TestClient
from taskmq.api_server import app, JWT_SECRET, JWT_ALGO
import jwt

client = TestClient(app)

def make_jwt(username, role):
    return jwt.encode({"sub": username, "role": role}, JWT_SECRET, algorithm=JWT_ALGO)

def test_valid_jwt_access():
    token = make_jwt("admin", "admin")
    response = client.post("/add-job", json={"payload": "auth test"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_invalid_jwt_access():
    token = "invalid.token.here"
    response = client.post("/add-job", json={"payload": "auth test"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

def test_protected_endpoint_requires_auth():
    response = client.post("/add-job", json={"payload": "auth test"})
    assert response.status_code == 401
