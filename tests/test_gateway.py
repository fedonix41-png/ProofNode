import pytest
import json
from fastapi.testclient import TestClient
from backend.app.main import app, settings
import aio_pika
import redis.asyncio as aioredis

@pytest.fixture
def client(postgres_server, rabbitmq_server, redis_server):
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert data["redis"] == "connected"
    assert data["rabbitmq"] == "connected"

def test_ton_webhook_ingestion(client):
    payload = {
        "tx_hash": "test_ton_tx_hash_1",
        "wallet_address": "EQCtestwalletaddress12345",
        "time": "2026-06-11T00:00:00Z",
        "payload": '{"dex_name": "Ston.fi", "token_in": "TON", "token_out": "USDT", "amount_in": 10.0, "amount_out": 22.0, "usd_value": 22.0, "tx_type": "BUY"}',
        "logical_time": 12345,
        "trace_id": "trace_id_abc"
    }
    
    # 1. Post webhook first time - should be queued
    response = client.post("/gateway/ton", json=payload)
    assert response.status_code == 202
    assert response.json() == {"status": "queued", "tx_hash": "test_ton_tx_hash_1"}
    
    # 2. Post webhook second time - should be ignored as duplicate
    response = client.post("/gateway/ton", json=payload)
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"

@pytest.mark.asyncio
async def test_rabbitmq_message_content(postgres_server, rabbitmq_server, redis_server):
    # Retrieve messages directly from RabbitMQ to assert correct routing
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("raw_blockchain_events", durable=True)
        
        # Get message from queue
        message = await queue.get(no_ack=True)
        assert message is not None
        
        body = json.loads(message.body.decode())
        assert body["blockchain"] == "TON"
        assert body["tx_hash"] == "test_ton_tx_hash_1"
        assert body["payload"]["wallet_address"] == "EQCtestwalletaddress12345"
        assert "trace_id_abc" in body["payload"]["trace_id"]

def test_webhook_signatures(client, monkeypatch):
    import hmac
    import hashlib
    from backend.app.config import settings
    
    # Enable signature checking for this test
    monkeypatch.setattr(settings, "env", "production")
    
    # 1. Test Alchemy (EVM)
    payload = {"tx_hash": "test_alchemy_1", "wallet_address": "0x123", "time": "2026-06-11T00:00:00Z", "payload": "{}", "block_number": 100}
    body_bytes = json.dumps(payload).encode("utf-8")
    secret = settings.alchemy_webhook_secret.encode("utf-8")
    valid_sig = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
    
    # Invalid sig
    response = client.post("/gateway/evm", json=payload, headers={"X-Alchemy-Signature": "invalid"})
    assert response.status_code == 401
    
    # Valid sig
    # Have to bypass redis deduplication somehow, or it will just say 202
    response = client.post("/gateway/evm", content=body_bytes, headers={"X-Alchemy-Signature": valid_sig, "Content-Type": "application/json"})
    assert response.status_code == 202

    # 2. Test Helius (SOL)
    payload_sol = {"tx_hash": "test_helius_1", "wallet_address": "sol123", "time": "2026-06-11T00:00:00Z", "payload": "{}", "slot": 100}
    
    # Invalid sig
    response = client.post("/gateway/sol", json=payload_sol, headers={"Authorization": "invalid"})
    assert response.status_code == 401
    
    # Valid sig
    response = client.post("/gateway/sol", json=payload_sol, headers={"Authorization": settings.helius_webhook_secret})
    assert response.status_code == 202

    # 3. Test TonAPI (TON)
    payload_ton = {"tx_hash": "test_ton_1", "wallet_address": "ton123", "time": "2026-06-11T00:00:00Z", "payload": "{}", "logical_time": 100, "trace_id": "abc"}
    
    # Invalid sig
    response = client.post("/gateway/ton", json=payload_ton, headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    
    # Valid sig (Auth header)
    response = client.post("/gateway/ton", json=payload_ton, headers={"Authorization": f"Bearer {settings.tonapi_webhook_secret}"})
    assert response.status_code == 202
