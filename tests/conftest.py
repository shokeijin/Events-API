import pytest
import requests
import time

BASE_URL = "http://localhost:5000"


@pytest.fixture
def auth_token():
    """Register a unique user, log in, and return the JWT access token."""
    username = f"testuser_{int(time.time() * 1000)}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": "TestPass123"
    })
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username,
        "password": "TestPass123"
    })
    return response.json()["access_token"]