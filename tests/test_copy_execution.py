import pytest
import pytest_asyncio
import asyncpg
import json
from decimal import Decimal
from uuid import uuid4

@pytest_asyncio.fixture
async def db_pool():
    from backend.app.config import settings
    pool = await asyncpg.create_pool(
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
        host=settings.postgres_host,
        port=settings.postgres_port
    )
    yield pool
    await pool.close()

@pytest.mark.asyncio
async def test_copy_retry_on_failure(db_pool, monkeypatch):
    from backend.app.copy_worker import execute_automated_trade
    from backend.app.services.dex import dex_service
    
    # Setup mock wallet
    async with db_pool.acquire() as conn:
        user_id = 999
        await conn.execute("INSERT INTO users (id, username, is_premium) VALUES ($1, 'test', FALSE) ON CONFLICT DO NOTHING", user_id)
        
        wallet_id = uuid4()
        from backend.app.services.kms import kms_service
        enc_pk = kms_service.encrypt_key("00" * 32)
        
        await conn.execute(
            """
            INSERT INTO user_proxy_wallets (id, user_id, blockchain, address, encrypted_private_key, balance)
            VALUES ($1, $2, 'SOL', 'mock_sol_addr', $3, 100.0)
            """,
            wallet_id, user_id, enc_pk
        )
        
        job = {
            "user_id": user_id,
            "proxy_wallet_id": str(wallet_id),
            "blockchain": "SOL",
            "token_in": "tokenA",
            "token_out": "tokenB",
            "amount_in": "10.0",
            "trader_tx_hash": "tx123"
        }
        
        # We will mock the Jupiter quote to fail on the first two attempts and succeed on the third
        attempts = 0
        async def mock_get_jupiter_quote(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                return None # simulate failure
            return {"mock": "quote"}
            
        async def mock_get_jupiter_swap_tx(*args, **kwargs):
            return "mock_unsigned_base64"
            
        async def mock_sign_solana(*args, **kwargs):
            return "final_tx_hash_456"
            
        monkeypatch.setattr(dex_service, "get_jupiter_quote", mock_get_jupiter_quote)
        monkeypatch.setattr(dex_service, "get_jupiter_swap_tx", mock_get_jupiter_swap_tx)
        monkeypatch.setattr(dex_service, "sign_and_send_solana_tx", mock_sign_solana)
        
        await execute_automated_trade(conn, job)
        
        # Check that it eventually succeeded
        row = await conn.fetchrow("SELECT * FROM copy_trade_executions WHERE trader_tx_hash = 'tx123'")
        assert row is not None
        assert row["status"] == "SUCCESS"
        assert row["copy_tx_hash"] == "final_tx_hash_456"
        
        # Check attempts
        assert attempts == 3
        
        # Cleanup
        await conn.execute("DELETE FROM copy_trade_executions WHERE trader_tx_hash = 'tx123'")
        await conn.execute("DELETE FROM user_proxy_wallets WHERE id = $1", wallet_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
