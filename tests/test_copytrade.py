import pytest
import json
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import aio_pika
import httpx
from uuid import UUID

from backend.app.main import app
from backend.app.db import db
from backend.app.config import settings
from backend.app.worker import process_message
from backend.app.copy_worker import process_job

@pytest.mark.asyncio
async def test_copytrade_automated_flow(postgres_server, rabbitmq_server, redis_server):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Trader Profile
        profile_payload = {
            "admin_id": 12345,
            "title": "Alpha Trader",
            "description": "TON whale",
            "public_slug": "alpha-trader"
        }
        response = await ac.post("/api/traders/profile", json=profile_payload)
        assert response.status_code == 201
        profile = response.json()
        profile_id = profile["id"]
        
        # 2. Register Trader Wallet
        trader_wallet_address = "EQD_trader_wallet_123"
        wallet_payload = {
            "trader_profile_id": profile_id,
            "blockchain": "TON",
            "address": trader_wallet_address
        }
        response = await ac.post("/api/traders/wallets", json=wallet_payload)
        assert response.status_code == 201
        
        # 3. Create Tariff & Subscribe User
        tariff_payload = {
            "trader_profile_id": profile_id,
            "duration_days": 30,
            "price_crypto": 10.0,
            "price_stars": 300,
            "currency": "TON"
        }
        response = await ac.post("/api/traders/tariffs", json=tariff_payload)
        assert response.status_code == 201
        tariff_id = response.json()["id"]
        
        user_id = 99991111
        verify_payload = {
            "user_id": user_id,
            "tariff_id": tariff_id,
            "tx_hash": "mock_sub_pay_hash"
        }
        response = await ac.post("/api/subscriptions/verify", json=verify_payload)
        assert response.status_code == 200
        subscription_id = response.json()["id"]
        
        # 4. Create and fund user proxy wallet
        response = await ac.post("/api/wallets/proxy/create", json={"user_id": user_id, "blockchain": "TON"})
        assert response.status_code == 201
        proxy = response.json()
        proxy_wallet_id = proxy["id"]
        
        response = await ac.post("/api/wallets/proxy/deposit", json={"proxy_wallet_id": proxy_wallet_id, "amount": 100.00})
        assert response.status_code == 200
        assert float(response.json()["balance"]) == 100.00
        
        # 5. Configure AUTOMATED copy trading
        config_payload = {
            "subscription_id": subscription_id,
            "copy_mode": "AUTOMATED",
            "proxy_wallet_id": proxy_wallet_id,
            "max_allocation_per_trade": 15.0,
            "slippage_bps": 100,
            "is_active": True
        }
        response = await ac.post("/api/copytrade/config", json=config_payload)
        assert response.status_code == 200
        
        # Set up RabbitMQ channel to verify queues
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            raw_events_queue = await channel.declare_queue("raw_blockchain_events", durable=True)
            copy_execution_queue = await channel.declare_queue("copy_trade_execution", durable=True)
            
            # 6. Publish raw event webhook representing Trader Swap
            trader_tx_hash = "trader_swap_tx_hash_1"
            event_payload = {
                "blockchain": "TON",
                "tx_hash": trader_tx_hash,
                "payload": {
                    "wallet_address": trader_wallet_address,
                    "time": "2026-06-11T13:00:00Z",
                    "payload": '{"dex_name": "Ston.fi", "token_in": "TON", "token_out": "SCALE", "amount_in": 100.0, "amount_out": 550.0, "usd_value": 150.0, "tx_type": "BUY"}'
                }
            }
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event_payload).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="raw_blockchain_events"
            )
            
            # 7. Consume and process raw event using Parser Worker
            msg = await raw_events_queue.get()
            assert msg is not None
            
            # Set worker globals
            import backend.app.worker as worker_module
            worker_module.rabbitmq_connection = connection
            worker_module.rabbitmq_channel = channel
            
            await process_message(msg)
            
            # 8. Let parser worker trigger the copy-trade job. Check copy_trade_execution queue.
            copy_msg = await copy_execution_queue.get()
            assert copy_msg is not None
            
            # 9. Let Copy Worker process the copy job
            import backend.app.copy_worker as copy_worker_module
            copy_worker_module.rabbitmq_connection = connection
            copy_worker_module.rabbitmq_channel = channel
            
            await process_job(copy_msg)
            
            # 10. Assert results: Balance deducted by max_allocation (15.0), execution recorded as success
            async for conn in db.get_connection():
                # Check balance
                proxy_wallet = await conn.fetchrow(
                    "SELECT balance FROM user_proxy_wallets WHERE id = $1", UUID(proxy_wallet_id)
                )
                assert float(proxy_wallet["balance"]) == 85.0  # 100 - 15
                
                # Check execution
                exec_record = await conn.fetchrow(
                    "SELECT * FROM copy_trade_executions WHERE user_id = $1 AND trader_tx_hash = $2",
                    user_id, trader_tx_hash
                )
                assert exec_record is not None
                assert exec_record["status"] == "SUCCESS"
                assert exec_record["blockchain"] == "TON"
                assert exec_record["copy_tx_hash"].startswith("mock_copy_tx_")
                break

@pytest.mark.asyncio
async def test_copytrade_1click_flow(postgres_server, rabbitmq_server, redis_server):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Trader Profile and subscribe user
        profile_payload = {
            "admin_id": 54321,
            "title": "Beta Trader",
            "description": "Base trader",
            "public_slug": "beta-trader"
        }
        response = await ac.post("/api/traders/profile", json=profile_payload)
        profile_id = response.json()["id"]
        
        trader_wallet_address = "0x_trader_wallet_base"
        wallet_payload = {
            "trader_profile_id": profile_id,
            "blockchain": "BASE",
            "address": trader_wallet_address
        }
        await ac.post("/api/traders/wallets", json=wallet_payload)
        
        tariff_payload = {
            "trader_profile_id": profile_id,
            "duration_days": 30,
            "price_crypto": 5.0,
            "price_stars": 150,
            "currency": "USDT"
        }
        response = await ac.post("/api/traders/tariffs", json=tariff_payload)
        tariff_id = response.json()["id"]
        
        user_id = 99992222
        response = await ac.post("/api/subscriptions/verify", json={"user_id": user_id, "tariff_id": tariff_id, "tx_hash": "mock_sub_pay_hash_2"})
        subscription_id = response.json()["id"]
        
        # 2. Configure 1-CLICK copy trading
        config_payload = {
            "subscription_id": subscription_id,
            "copy_mode": "1-CLICK",
            "max_allocation_per_trade": 5.0,
            "slippage_bps": 100,
            "is_active": True
        }
        await ac.post("/api/copytrade/config", json=config_payload)
        
        # Connect RMQ
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            raw_events_queue = await channel.declare_queue("raw_blockchain_events", durable=True)
            copy_execution_queue = await channel.declare_queue("copy_trade_execution", durable=True)
            bot_notif_queue = await channel.declare_queue("tg_bot_notifications", durable=True)
            
            # 3. Publish trader swap webhook
            trader_tx_hash = "trader_base_swap_tx_1"
            event_payload = {
                "blockchain": "BASE",
                "tx_hash": trader_tx_hash,
                "payload": {
                    "wallet_address": trader_wallet_address,
                    "time": "2026-06-11T13:05:00Z",
                    "payload": '{"dex_name": "Uniswap", "token_in": "WETH", "token_out": "USDC", "amount_in": 1.0, "amount_out": 3500.0, "usd_value": 3500.0, "tx_type": "BUY"}'
                }
            }
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event_payload).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="raw_blockchain_events"
            )
            
            # 4. Parse raw event
            msg = await raw_events_queue.get()
            import backend.app.worker as worker_module
            worker_module.rabbitmq_connection = connection
            worker_module.rabbitmq_channel = channel
            await process_message(msg)
            
            # 5. Let copy worker process copy job
            copy_msg = await copy_execution_queue.get()
            import backend.app.copy_worker as copy_worker_module
            copy_worker_module.rabbitmq_connection = connection
            copy_worker_module.rabbitmq_channel = channel
            await process_job(copy_msg)
            
            # 6. Assert pending trade created in DB and bot notification emitted
            async for conn in db.get_connection():
                pending_trade = await conn.fetchrow(
                    "SELECT * FROM pending_copy_trades WHERE user_id = $1 AND trader_tx_hash = $2",
                    user_id, trader_tx_hash
                )
                assert pending_trade is not None
                assert pending_trade["status"] == "PENDING"
                assert float(pending_trade["amount_in"]) == 5.0
                pending_trade_id = pending_trade["id"]
                break
                
            # Verify message exists in bot notifications queue
            bot_msg = await bot_notif_queue.get()
            assert bot_msg is not None
            bot_body = json.loads(bot_msg.body.decode())
            assert bot_body["user_id"] == user_id
            assert bot_body["type"] == "1CLICK_COPY_ALERT"
            assert bot_body["pending_trade_id"] == str(pending_trade_id)
            
            # 7. Execute 1-Click signed trade via endpoint
            execute_payload = {
                "pending_trade_id": str(pending_trade_id),
                "tx_hash": "mock_user_signed_tx_hash_999"
            }
            response = await ac.post("/api/copytrade/execute-1click", json=execute_payload)
            assert response.status_code == 200
            exec_data = response.json()
            assert exec_data["status"] == "SUCCESS"
            assert exec_data["copy_tx_hash"] == "mock_user_signed_tx_hash_999"
            
            # Verify updated DB state
            async for conn in db.get_connection():
                pending_trade = await conn.fetchrow(
                    "SELECT status FROM pending_copy_trades WHERE id = $1", pending_trade_id
                )
                assert pending_trade["status"] == "EXECUTED"
                break
