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


# ---------------------------------------------------------------------------
# Fehlerfälle / Randfälle
# ---------------------------------------------------------------------------

def test_duplicate_registration_returns_400():
    """Dieselben Zugangsdaten zweimal registrieren — die zweite Anfrage schlägt fehl."""
    username = f"dup_{int(time.time() * 1000)}"
    payload = {"username": username, "password": "Sicher123"}

    first = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert first.status_code == 201

    second = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert second.status_code == 400
    assert "error" in second.json()


def test_rsvp_to_private_event_without_token_is_rejected(auth_token):
    """RSVP für eine nicht-öffentliche Veranstaltung ohne Authentifizierung → 401."""
    event_response = requests.post(
        f"{BASE_URL}/api/events",
        json={"title": "Privat-Event", "date": "2026-12-20T19:00:00", "is_public": False},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    rsvp_response = requests.post(
        f"{BASE_URL}/api/rsvps/event/{event_id}",
        json={"attending": True}
        # kein Authorization-Header
    )

    assert rsvp_response.status_code == 401
    assert "error" in rsvp_response.json()


def test_login_with_wrong_password_returns_401():
    """Anmeldung mit falschem Passwort wird abgelehnt."""
    username = f"wrongpw_{int(time.time() * 1000)}"
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": username,
        "password": "KorrektesPasswort"
    })

    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username,
        "password": "FalschesPasswort"
    })

    assert response.status_code == 401
    assert "error" in response.json()