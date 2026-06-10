import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from aiogram import types

from backend.app.db import db
from bot.main import cmd_start
from bot.scheduler import check_expired_subscriptions

@pytest.mark.asyncio
async def test_bot_start_command(postgres_server, rabbitmq_server, redis_server):
    # Initialize DB connection pool
    await db.connect()
    
    # 1. Construct a mock aiogram Message representing a user typing /start
    chat = types.Chat(id=12345, type="private")
    user = types.User(id=12345, is_bot=False, first_name="John", username="john_doe")
    
    # Mock message
    message = MagicMock(spec=types.Message)
    message.chat = chat
    message.from_user = user
    message.reply = AsyncMock()
    
    # 2. Trigger the command handler
    await cmd_start(message)
    
    # 3. Assert welcome message replied
    message.reply.assert_called_once()
    reply_args = message.reply.call_args[0][0]
    assert "Welcome to" in reply_args and "ProofNode" in reply_args
    
    # 4. Verify user was upserted in the database
    async for conn in db.get_connection():
        row = await conn.fetchrow("SELECT * FROM users WHERE id = 12345")
        assert row is not None
        assert row["username"] == "john_doe"
        break
        
    await db.disconnect()

@pytest.mark.asyncio
async def test_subscription_expiration_scheduler(postgres_server, rabbitmq_server, redis_server):
    await db.connect()
    
    # Setup: Create a trader profile and an active subscription that expired 1 hour ago
    async for conn in db.get_connection():
        # Ensure user exists
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            7777, "client_7777"
        )
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            8888, "trader_8888"
        )
        
        # Create trader profile
        trader_id = await conn.fetchval(
            """
            INSERT INTO trader_profiles (admin_id, title, public_slug)
            VALUES ($1, $2, $3)
            ON CONFLICT (public_slug) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
            """,
            8888, "Trader X", "trader-x"
        )
        
        # Insert expired active subscription
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        sub_id = await conn.fetchval(
            """
            INSERT INTO subscriptions (user_id, trader_profile_id, status, expires_at, invite_link)
            VALUES ($1, $2, 'ACTIVE', $3, $4)
            RETURNING id
            """,
            7777, trader_id, expired_time, "https://t.me/+old_link"
        )
        
        # Run expiration check with mock bot
        await check_expired_subscriptions(bot=None)
        
        # Verify status is now 'EXPIRED'
        status = await conn.fetchval("SELECT status FROM subscriptions WHERE id = $1", sub_id)
        assert status == "EXPIRED"
        break
        
    await db.disconnect()
