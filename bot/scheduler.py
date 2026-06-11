import asyncio
import logging
from datetime import datetime, timezone
from aiogram import Bot

from backend.app.config import settings
from backend.app.db import db

logger = logging.getLogger(__name__)

async def check_expired_subscriptions(bot: Bot | None) -> None:
    now = datetime.now(timezone.utc)
    
    async for conn in db.get_connection():
        # 1. Retrieve all active subscriptions that have expired
        expired_subs = await conn.fetch(
            """
            SELECT id, user_id, trader_profile_id
            FROM subscriptions
            WHERE status = 'ACTIVE' AND expires_at < $1
            """,
            now
        )
        
        if not expired_subs:
            return
            
        logger.info(f"Found {len(expired_subs)} expired subscriptions to process.")
        
        for sub in expired_subs:
            sub_id = sub["id"]
            user_id = sub["user_id"]
            
            # 2. Update status in database
            await conn.execute(
                "UPDATE subscriptions SET status = 'EXPIRED' WHERE id = $1",
                sub_id
            )
            logger.info(f"Updated subscription {sub_id} status to EXPIRED in database.")
            
            # 3. Revoke access from Telegram Channel/Group
            if bot is None:
                # Simulated kick logic for local sandbox / tests
                logger.info(f"[SIMULATOR] Kicking user {user_id} from Telegram channel {settings.channel_id}.")
            else:
                try:
                    # Ban user to remove them from channel
                    await bot.ban_chat_member(
                        chat_id=settings.channel_id,
                        user_id=user_id
                    )
                    # Immediately unban them so they are not permanently blocked and can rejoin later
                    await bot.unban_chat_member(
                        chat_id=settings.channel_id,
                        user_id=user_id
                    )
                    logger.info(f"Successfully evicted user {user_id} from channel {settings.channel_id}.")
                except Exception as e:
                    logger.warning(
                        f"Failed to evict user {user_id} from Telegram channel {settings.channel_id}: {e}. "
                        "Check bot admin permissions."
                    )
        break

async def check_daily_commission() -> None:
    from backend.app.services.commission import aggregate_daily_commission
    try:
        await aggregate_daily_commission()
    except Exception as e:
        logger.error(f"Error in daily commission aggregation: {e}")

async def start_scheduler(bot: Bot | None) -> None:
    logger.info("Subscription expiration scheduler worker started.")
    
    # 5 seconds interval for fast verification in tests, otherwise 60 seconds
    interval = 5 if settings.env == "testing" else 60
    
    # State for daily task
    from datetime import timedelta
    last_commission_run = None
    
    try:
        while True:
            now = datetime.now(timezone.utc)
            
            # 1. Run subscription checker
            try:
                await check_expired_subscriptions(bot)
            except Exception as e:
                logger.error(f"Error in subscription checker execution loop: {e}")
                
            # 2. Run daily commission at midnight UTC
            if last_commission_run is None or now.date() > last_commission_run.date():
                if now.hour == 0 or settings.env == "testing":
                    await check_daily_commission()
                    last_commission_run = now
                    
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Subscription expiration scheduler worker stopped.")
