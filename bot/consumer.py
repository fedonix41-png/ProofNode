import asyncio
import json
import logging
import aio_pika
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from backend.app.config import settings

logger = logging.getLogger(__name__)

async def start_rabbitmq_consumer(bot: Bot):
    """
    Connects to RabbitMQ and listens for incoming tg_bot_notifications.
    Dispatches rich text Telegram messages with deep-link TMA buttons.
    """
    if not settings.rabbitmq_host:
        logger.warning("RabbitMQ host not set. Skipping bot consumer initialization.")
        return

    logger.info("Initializing RabbitMQ notification consumer for Telegram Bot...")
    
    # Connection retry logic
    connection = None
    for attempt in range(5):
        try:
            connection = await aio_pika.connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_password
            )
            break
        except Exception as e:
            logger.warning(f"RabbitMQ connection failed (attempt {attempt + 1}/5): {e}")
            await asyncio.sleep(2)
            
    if not connection:
        logger.error("Failed to connect to RabbitMQ for bot consumer.")
        return

    channel = await connection.channel()
    # Declare the queue
    queue = await channel.declare_queue("tg_bot_notifications", durable=True)

    async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
        async with message.process():
            payload = json.loads(message.body.decode())
            logger.info(f"Bot Consumer received notification: {payload}")
            
            try:
                user_id = payload["user_id"]
                pending_trade_id = payload["pending_trade_id"]
                blockchain = payload.get("blockchain", "TON")
                token_in = payload.get("token_in_symbol", "Unknown")
                token_out = payload.get("token_out_symbol", "Unknown")
                amount_in = payload.get("amount_in", "0")
                trader_alias = payload.get("trader_alias", "Unknown Trader")
                
                # Format the premium notification text
                text = (
                    f"📊 **{trader_alias}** has executed a trade!\n\n"
                    f"🔄 Swap: `{amount_in} {token_in}` ➔ `{token_out}`\n"
                    f"🌐 Network: `{blockchain}`\n\n"
                    "Click the button below to sign and execute this swap with 1-Click."
                )
                
                # Inline keyboard deep-link
                # e.g., https://t.me/proofnode_bot/app?startapp=copy_uuid
                bot_username = "proofnode_bot" # Ideally from settings, hardcoded here for MVP
                deep_link = f"https://t.me/{bot_username}/app?startapp=copy_{pending_trade_id}"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⚡ Copy Trade (TMA)", url=deep_link)]
                ])
                
                # If bot is mock, just log it. Otherwise dispatch real message.
                if bot is None or (isinstance(bot, str) and bot == "mock_bot"):
                    logger.info(f"[MOCK BOT DISPATCH] To: {user_id} | Text: {text} | URL: {deep_link}")
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error processing notification payload: {e}")

    await queue.consume(on_message)
    logger.info("Bot consumer is now listening on 'tg_bot_notifications' queue.")
    
    # Store connection on bot to close it later, or keep it running in background
    return connection

async def stop_rabbitmq_consumer(connection):
    if connection:
        logger.info("Closing Bot Consumer RabbitMQ connection...")
        await connection.close()
