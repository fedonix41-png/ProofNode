import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app

@pytest.fixture
def client(postgres_server, rabbitmq_server, redis_server):
    with TestClient(app) as c:
        yield c

def test_signal_lifecycle(client):
    # 1. Create a trader profile
    profile_payload = {
        "admin_id": 99991,
        "title": "Signal Tester",
        "public_slug": "signal-tester-1"
    }
    resp = client.post("/api/traders/profile", json=profile_payload)
    assert resp.status_code == 201
    profile_id = resp.json()["id"]

    # 2. Create a signal
    signal_payload = {
        "token_address": "EQDtest_token",
        "blockchain": "TON",
        "direction": "BUY"
    }
    resp = client.post(f"/api/traders/{profile_id}/signals", json=signal_payload)
    assert resp.status_code == 201
    signal = resp.json()
    assert signal["status"] == "OPEN"
    assert signal["direction"] == "BUY"
    assert signal["token_address"] == "EQDtest_token"
    signal_id = signal["id"]

    # 3. Close the signal
    resp = client.post(f"/api/traders/{profile_id}/signals/{signal_id}/close")
    assert resp.status_code == 200
    closed_signal = resp.json()
    assert closed_signal["status"] == "CLOSED"
    assert "pnl_percent" in closed_signal

    # 4. Get trader profile by slug and verify signal is there
    resp = client.get("/api/traders/signal-tester-1")
    assert resp.status_code == 200
    profile_data = resp.json()
    assert profile_data["title"] == "Signal Tester"
    assert "recent_signals" in profile_data
    assert len(profile_data["recent_signals"]) == 1
    assert profile_data["recent_signals"][0]["id"] == signal_id
    assert profile_data["recent_signals"][0]["status"] == "CLOSED"
