import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import MenuButtonWebApp, WebAppInfo
import sentry_sdk

from backend.app.config import settings
from backend.app.db import db

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# Bot /start Command Handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    logger.info(f"User {user_id} (@{username}) triggered /start")
    
    async for conn in db.get_connection():
        # Upsert user in database
        await conn.execute(
            """
            INSERT INTO users (id, username, is_premium)
            VALUES ($1, $2, FALSE)
            ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
            """,
            user_id, username
        )
        break
        
    welcome_text = (
        f"👋 Welcome to **ProofNode**, {message.from_user.first_name}!\n\n"
        "This is your Telegram Social Trading Co-Pilot. Here, you can copy elite traders "
        "and track smart money on-chain safely.\n\n"
        "🔗 Connect your Web3 wallet inside the Mini App to start tracking and subscribing to VIP channels."
    )
    
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Open Mini App 🚀", web_app=WebAppInfo(url=settings.webapp_url))]
        ]
    )
    await message.reply(welcome_text, parse_mode="Markdown", reply_markup=markup)

# Bot /status Command Handler
@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    
    async for conn in db.get_connection():
        subscriptions = await conn.fetch(
            """
            SELECT s.expires_at, p.title as trader_title
            FROM subscriptions s
            JOIN trader_profiles p ON s.trader_profile_id = p.id
            WHERE s.user_id = $1 AND s.status = 'ACTIVE'
            """,
            user_id
        )
        
        if not subscriptions:
            await message.reply("❌ You do not have any active subscriptions. Visit the ProofNode Mini App to subscribe to VIP channels!")
            return
            
        lines = ["✅ **Active Subscriptions:**"]
        for sub in subscriptions:
            expiry = sub["expires_at"].strftime("%Y-%m-%d %H:%M:%S UTC")
            lines.append(f"• **{sub['trader_title']}** - Expiers: `{expiry}`")
            
        await message.reply("\n".join(lines), parse_mode="Markdown")
        return

async def run_bot():
    logger.info("Initializing ProofNode Telegram Bot...")
    
    # Enable database pool
    await db.connect()
    
    # If the token is a mock, run a simulation loop rather than entering real Telegram polling
    if not settings.bot_token or settings.bot_token == "mock_token" or settings.bot_token.endswith("mock"):
        logger.warning("Mock token detected. Running in mock simulator mode...")
        # Start the scheduler background loop in simulated mode
        from bot.scheduler import start_scheduler
        from bot.consumer import start_rabbitmq_consumer, stop_rabbitmq_consumer
        scheduler_task = asyncio.create_task(start_scheduler(bot=None))
        consumer_conn = await start_rabbitmq_consumer(bot=None)
        
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Simulator loop stopped.")
        finally:
            scheduler_task.cancel()
            await stop_rabbitmq_consumer(consumer_conn)
            await db.disconnect()
            logger.info("Database connection closed.")
        return

    # Real bot initialization
    bot = Bot(token=settings.bot_token)
    
    # Set Menu Button
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Open App", 
                web_app=WebAppInfo(url=settings.webapp_url)
            )
        )
    except Exception as e:
        logger.error(f"Failed to set menu button: {e}")
    
    # Start the scheduler background loop
    from bot.scheduler import start_scheduler
    from bot.consumer import start_rabbitmq_consumer, stop_rabbitmq_consumer
    
    scheduler_task = asyncio.create_task(start_scheduler(bot=bot))
    consumer_conn = await start_rabbitmq_consumer(bot=bot)
    
    try:
        logger.info("Starting Telegram Bot long-polling...")
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await stop_rabbitmq_consumer(consumer_conn)
        await bot.session.close()
        await db.disconnect()
        logger.info("Bot components clean shutdown complete.")

if __name__ == "__main__":
    asyncio.run(run_bot())
