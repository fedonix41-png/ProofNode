import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.app.main import app
from backend.app.db import db

@pytest.fixture
def client(postgres_server, rabbitmq_server, redis_server):
    with TestClient(app) as c:
        yield c

def test_sss_wallet_endpoints(client):
    # Register SSS Share
    payload = {
        "user_id": 12345,
        "blockchain": "TON",
        "address": "EQDtest_wallet_address",
        "server_share": "2:share_value_abc"
    }
    response = client.post("/api/wallets/sss/register", json=payload)
    assert response.status_code == 201
    reg = response.json()
    assert reg["user_id"] == 12345
    assert reg["blockchain"] == "TON"
    assert reg["address"] == "EQDtest_wallet_address"
    
    # Retrieve SSS Share
    retrieve_payload = {
        "user_id": 12345,
        "blockchain": "TON",
        "address": "EQDtest_wallet_address"
    }
    response = client.post("/api/wallets/sss/retrieve", json=retrieve_payload)
    assert response.status_code == 200
    ret = response.json()
    assert ret["server_share"] == "2:share_value_abc"
    
    # Non-existent share
    bad_payload = {
        "user_id": 12345,
        "blockchain": "TON",
        "address": "EQDtest_wallet_address_non_existent"
    }
    response = client.post("/api/wallets/sss/retrieve", json=bad_payload)
    assert response.status_code == 404

def test_proxy_wallet_endpoints(client):
    # Create proxy wallet
    payload = {
        "user_id": 12345,
        "blockchain": "TON"
    }
    response = client.post("/api/wallets/proxy/create", json=payload)
    assert response.status_code == 201
    wallet = response.json()
    assert wallet["user_id"] == 12345
    assert wallet["blockchain"] == "TON"
    assert wallet["address"].startswith("EQ_proxy_")
    assert wallet["balance"] == 0.0
    wallet_id = wallet["id"]
    
    # Deposit funds
    deposit_payload = {
        "proxy_wallet_id": wallet_id,
        "amount": 50.5
    }
    response = client.post("/api/wallets/proxy/deposit", json=deposit_payload)
    assert response.status_code == 200
    dep = response.json()
    assert dep["id"] == wallet_id
    assert float(dep["balance"]) == 50.5
