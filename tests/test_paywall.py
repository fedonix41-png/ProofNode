import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.app.main import app
from backend.app.db import db

@pytest.fixture
def client(postgres_server, rabbitmq_server, redis_server):
    with TestClient(app) as c:
        yield c

def test_paywall_flow(client):
    # 1. Create Trader Profile
    profile_payload = {
        "admin_id": 99998888,
        "title": "Crypto VIP Signals",
        "description": "Elite trading signals on TON",
        "public_slug": "crypto-vip"
    }
    response = client.post("/api/traders/profile", json=profile_payload)
    assert response.status_code == 201
    profile = response.json()
    assert profile["admin_id"] == 99998888
    assert profile["title"] == "Crypto VIP Signals"
    profile_id = profile["id"]
    
    # 2. Add Trader Wallet
    wallet_payload = {
        "trader_profile_id": profile_id,
        "blockchain": "TON",
        "address": "EQDtest_trader_wallet_address_123"
    }
    response = client.post("/api/traders/wallets", json=wallet_payload)
    assert response.status_code == 201
    wallet = response.json()
    assert wallet["blockchain"] == "TON"
    assert wallet["address"] == "EQDtest_trader_wallet_address_123"
    
    # 3. Create Tariff Plan
    tariff_payload = {
        "trader_profile_id": profile_id,
        "duration_days": 30,
        "price_crypto": 15.5,
        "price_stars": 500,
        "currency": "TON"
    }
    response = client.post("/api/traders/tariffs", json=tariff_payload)
    assert response.status_code == 201
    tariff = response.json()
    assert tariff["duration_days"] == 30
    assert float(tariff["price_crypto"]) == 15.5
    assert tariff["price_stars"] == 500
    tariff_id = tariff["id"]
    
    # 4. Initiate Purchase
    purchase_payload = {
        "user_id": 11112222,
        "tariff_id": tariff_id
    }
    response = client.post("/api/subscriptions/purchase", json=purchase_payload)
    assert response.status_code == 200
    order = response.json()
    assert order["user_id"] == 11112222
    assert order["tariff_id"] == tariff_id
    assert order["price_stars"] == 500
    assert order["trader_title"] == "Crypto VIP Signals"
    
    # 5. Verify payment confirmation & Subscription creation
    verify_payload = {
        "user_id": 11112222,
        "tariff_id": tariff_id,
        "tx_hash": "mock_tx_hash_for_ton_subscription_test"
    }
    response = client.post("/api/subscriptions/verify", json=verify_payload)
    assert response.status_code == 200
    subscription = response.json()
    assert subscription["user_id"] == 11112222
    assert subscription["status"] == "ACTIVE"
    assert "invite_link" in subscription
    assert subscription["invite_link"].startswith("https://t.me/+") or "fallback" in subscription["invite_link"]
