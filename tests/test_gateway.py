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
