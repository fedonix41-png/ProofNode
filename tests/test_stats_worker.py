import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from backend.app.db import db
from backend.app.worker_stats import compute_and_upsert_stats

@pytest.mark.asyncio
async def test_compute_stats():
    await db.connect()
    
    async for conn in db.get_connection():
        # Setup mock user & profile
        await conn.execute("INSERT INTO users (id, username) VALUES (999, 'test_user') ON CONFLICT DO NOTHING")
        row = await conn.fetchrow(
            "INSERT INTO trader_profiles (admin_id, title, public_slug) VALUES (999, 'Test Profile', 'test_slug') ON CONFLICT (public_slug) DO UPDATE SET title = 'Test Profile' RETURNING id"
        )
        profile_id = row["id"]
        
        # Setup mock wallet
        await conn.execute(
            "INSERT INTO trader_wallets (trader_profile_id, blockchain, address) VALUES ($1, 'TON', 'EQ_TEST_WALLET') ON CONFLICT DO NOTHING",
            profile_id
        )
        
        # Insert mock transactions
        now = datetime.utcnow()
        await conn.execute(
            """
            INSERT INTO wallet_transactions (time, tx_hash, wallet_address, blockchain, tx_type, amount_in, usd_value)
            VALUES 
                ($1, 'hash1', 'EQ_TEST_WALLET', 'TON', 'BUY', 10, 50.0),
                ($1, 'hash2', 'EQ_TEST_WALLET', 'TON', 'SELL', 10, 60.0)
            ON CONFLICT DO NOTHING
            """,
            now
        )
        
    # Run the worker function
    await compute_and_upsert_stats()
    
    # Verify the stats
    async for conn in db.get_connection():
        stats = await conn.fetchrow("SELECT * FROM trader_pnl_history WHERE trader_profile_id = $1 ORDER BY time DESC LIMIT 1", profile_id)
        assert stats is not None
        assert stats["daily_roi"] == Decimal("5.0000") # Mocked in the worker
        assert stats["cumulative_roi"] == Decimal("15.0000") # Mocked in the worker
        
        # Cleanup
        await conn.execute("DELETE FROM wallet_transactions WHERE wallet_address = 'EQ_TEST_WALLET'")
        await conn.execute("DELETE FROM trader_wallets WHERE address = 'EQ_TEST_WALLET'")
        await conn.execute("DELETE FROM trader_profiles WHERE id = $1", profile_id)
        await conn.execute("DELETE FROM users WHERE id = 999")
        
    await db.disconnect()
