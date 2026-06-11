import pytest
import pytest_asyncio
import asyncpg
from datetime import datetime, timezone
from backend.app.services.referral import apply_referral_credit, get_max_wallets
from backend.app.services.commission import schedule_payout
from decimal import Decimal

@pytest_asyncio.fixture
async def db_pool():
    # Setup test DB pool
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

@pytest_asyncio.fixture
async def setup_users(db_pool):
    async with db_pool.acquire() as conn:
        # Create users
        await conn.execute("INSERT INTO users (id, username, is_premium) VALUES (101, 'user1', FALSE) ON CONFLICT DO NOTHING")
        await conn.execute("INSERT INTO users (id, username, is_premium) VALUES (102, 'user2', FALSE) ON CONFLICT DO NOTHING")
        # Ensure referral_credits is 0
        await conn.execute("UPDATE users SET referral_credits = 0 WHERE id IN (101, 102)")
        yield
        # Cleanup
        await conn.execute("DELETE FROM users WHERE id IN (101, 102)")

@pytest.mark.asyncio
async def test_referral_credit(db_pool, setup_users):
    # Apply credit
    success = await apply_referral_credit(db_pool, 101, 102)
    assert success is True
    
    # Check if credit applied
    async with db_pool.acquire() as conn:
        credits = await conn.fetchval("SELECT referral_credits FROM users WHERE id = 101")
        assert credits == 1

def test_wallet_limit_with_credits():
    from backend.app.config import settings
    settings.referral_credit_per_invite = 2
    
    # Base is 3 + (2 * 2) = 7
    limit = get_max_wallets(is_premium=False, referral_credits=2)
    assert limit == 7
    
    # Premium is unlimited
    limit_premium = get_max_wallets(is_premium=True, referral_credits=0)
    assert limit_premium == -1

@pytest.mark.asyncio
async def test_commission_aggregation(db_pool):
    async with db_pool.acquire() as conn:
        now = datetime.now(timezone.utc)
        
        # We will test the schedule_payout function directly since aggregate_daily_commission relies on past DB states
        await schedule_payout(conn, now, now, Decimal("100.0"), Decimal("5.0"))
        
        # Verify
        row = await conn.fetchrow(
            "SELECT * FROM commission_payouts WHERE total_volume = $1 AND commission_amount = $2",
            Decimal("100.0"), Decimal("5.0")
        )
        assert row is not None
        assert row["status"] == "PENDING"
        
        # Cleanup
        await conn.execute("DELETE FROM commission_payouts WHERE id = $1", row["id"])

