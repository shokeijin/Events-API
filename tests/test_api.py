import time
import requests
from tests.conftest import BASE_URL


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_healthy():
    response = requests.get(f"{BASE_URL}/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# User registration
# ---------------------------------------------------------------------------

def test_register_user_creates_new_user():
    username = f"user_{int(time.time() * 1000)}"
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": "Sicher123"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == username


# ---------------------------------------------------------------------------
# User login
# ---------------------------------------------------------------------------

def test_login_returns_jwt_token():
    username = f"user_{int(time.time() * 1000)}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": "Sicher123"
    })

    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username,
        "password": "Sicher123"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()


# ---------------------------------------------------------------------------
# Event creation (authenticated)
# ---------------------------------------------------------------------------

def test_create_public_event_requires_auth_and_succeeds_with_token(auth_token):
    payload = {
        "title": "Test-Event",
        "date": "2026-12-01T18:00:00",
        "location": "Berlin",
        "is_public": True
    }
    response = requests.post(
        f"{BASE_URL}/api/events",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test-Event"
    assert data["location"] == "Berlin"
    assert data["is_public"] is True


def test_create_event_without_token_is_rejected():
    response = requests.post(f"{BASE_URL}/api/events", json={
        "title": "Kein Token",
        "date": "2026-12-01T18:00:00"
    })

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# RSVP for a public event
# ---------------------------------------------------------------------------

def test_rsvp_to_public_event(auth_token):
    # Create an event first
    event_response = requests.post(
        f"{BASE_URL}/api/events",
        json={"title": "RSVP-Event", "date": "2026-12-15T20:00:00", "is_public": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    # RSVP as the same authenticated user
    rsvp_response = requests.post(
        f"{BASE_URL}/api/rsvps/event/{event_id}",
        json={"attending": True},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert rsvp_response.status_code == 201
    data = rsvp_response.json()
    assert data["event_id"] == event_id
    assert data["attending"] is True