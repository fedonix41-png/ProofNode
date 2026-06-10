import pytest
import json
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import aio_pika
import asyncpg

from backend.app.config import settings
from backend.app.db import db
from backend.app.parser import parse_blockchain_transaction
from backend.app.worker import process_message

@pytest.mark.asyncio
async def test_parser_decoder():
    time_val = datetime.now(timezone.utc)
    raw_payload = '{"dex_name": "DeDust", "token_in": "TON", "token_out": "SCALE", "amount_in": 5.0, "amount_out": 25.0, "usd_value": 7.5, "tx_type": "SELL", "trace_id": "t1", "logical_time": 999}'
    
    parsed = parse_blockchain_transaction(
        blockchain="TON",
        tx_hash="tx_999",
        wallet_address="EQC_wallet",
        time_val=time_val,
        raw_payload=raw_payload
    )
    
    assert parsed is not None
    assert parsed["blockchain"] == "TON"
    assert parsed["tx_hash"] == "tx_999"
    assert parsed["dex_name"] == "DeDust"
    assert parsed["token_in_address"] == "TON"
    assert parsed["token_out_address"] == "SCALE"
    assert parsed["amount_in"] == Decimal("5.0")
    assert parsed["amount_out"] == Decimal("25.0")
    assert parsed["usd_value"] == Decimal("7.5")
    assert parsed["tx_type"] == "SELL"
    assert parsed["trace_id"] == "t1"
    assert parsed["logical_time"] == 999

@pytest.mark.asyncio
async def test_worker_processing(postgres_server, rabbitmq_server, redis_server):
    # Initialize DB connection pool
    await db.connect()
    
    # 1. Publish mock event payload directly to RabbitMQ raw_blockchain_events queue
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("raw_blockchain_events", durable=True)
        
        event_payload = {
            "blockchain": "SOL",
            "tx_hash": "sol_tx_hash_1",
            "payload": {
                "wallet_address": "sol_wallet_addr_123",
                "time": "2026-06-11T12:00:00Z",
                "payload": '{"dex_name": "Raydium", "token_in": "SOL", "token_out": "WIF", "amount_in": 2.0, "amount_out": 400.0, "usd_value": 300.0, "tx_type": "BUY"}'
            }
        }
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="raw_blockchain_events"
        )
        
        # 2. Consume and process message using worker logic
        message = await queue.get()
        assert message is not None
        
        # Run process_message
        await process_message(message)
        
        # 3. Query TimescaleDB to assert the row exists
        async for conn in db.get_connection():
            row = await conn.fetchrow(
                "SELECT * FROM wallet_transactions WHERE tx_hash = $1", "sol_tx_hash_1"
            )
            assert row is not None
            assert row["blockchain"] == "SOL"
            assert row["wallet_address"] == "sol_wallet_addr_123"
            assert row["dex_name"] == "Raydium"
            assert row["token_in_address"] == "SOL"
            assert row["token_out_address"] == "WIF"
            assert row["amount_in"] == Decimal("2.0")
            assert row["amount_out"] == Decimal("400.0")
            assert row["usd_value"] == Decimal("300.0")
            assert row["tx_type"] == "BUY"
            break
            
    await db.disconnect()

@pytest.mark.asyncio
async def test_worker_poison_pill(postgres_server, rabbitmq_server, redis_server):
    # Initialize DB connection pool
    await db.connect()
    
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("raw_blockchain_events", durable=True)
        
        # Malformed event missing 'time' and 'wallet_address'
        event_payload = {
            "blockchain": "SOL",
            "tx_hash": "sol_tx_hash_poison",
            "payload": {
                "payload": '{"dex_name": "Raydium"}'
            }
        }
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="raw_blockchain_events"
        )
        
        # Consume and process
        message = await queue.get()
        assert message is not None
        
        # process_message should log error and not crash/requeue the poison pill
        await process_message(message)
        
        # Assert it was not recorded in DB
        async for conn in db.get_connection():
            row = await conn.fetchrow(
                "SELECT * FROM wallet_transactions WHERE tx_hash = $1", "sol_tx_hash_poison"
            )
            assert row is None
            break
            
    await db.disconnect()
