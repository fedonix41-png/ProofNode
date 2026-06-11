import pytest
import asyncio
import json
import aio_pika
from unittest.mock import AsyncMock, MagicMock

from bot.consumer import start_rabbitmq_consumer, stop_rabbitmq_consumer
from backend.app.config import settings

@pytest.mark.asyncio
async def test_bot_notification_processing(postgres_server, rabbitmq_server):
    """
    Test that a notification payload in RabbitMQ results in a bot message.
    """
    # 1. Setup a Mock Bot
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()

    # 2. Connect DB and Start Consumer
    from backend.app.db import db
    await db.connect()
    conn = await start_rabbitmq_consumer(mock_bot)
    assert conn is not None, "Consumer failed to connect to RabbitMQ"
    
    try:
        # Insert mock user for premium check
        async for db_conn in db.get_connection():
            await db_conn.execute("INSERT INTO users (id, username, is_premium) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING", 999111, "testuser", True)
            break
            
        # 3. Publish a test payload to RabbitMQ
        channel = await conn.channel()
        payload = {
            "user_id": 999111,
            "pending_trade_id": "test-uuid-1234",
            "blockchain": "SOL",
            "token_in_symbol": "SOL",
            "token_out_symbol": "USDC",
            "amount_in": "5.5",
            "trader_alias": "Alpha Whale #1"
        }
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="tg_bot_notifications"
        )
        
        # Give consumer time to process the message
        await asyncio.sleep(1.0)
        
        # 4. Verify mock_bot was called with correct data
        mock_bot.send_message.assert_called_once()
        
        # Inspect arguments
        call_kwargs = mock_bot.send_message.call_args.kwargs
        
        assert call_kwargs["chat_id"] == 999111
        assert "Alpha Whale #1" in call_kwargs["text"]
        assert "5.5 SOL ➔ USDC" in call_kwargs["text"] or ("5.5" in call_kwargs["text"] and "SOL" in call_kwargs["text"] and "USDC" in call_kwargs["text"])
        assert "SOL" in call_kwargs["text"]
        
        # Check inline keyboard
        keyboard = call_kwargs["reply_markup"]
        assert keyboard is not None
        
        inline_button = keyboard.inline_keyboard[0][0]
        assert "Copy Trade" in inline_button.text
        assert "startapp=copy_test-uuid-1234" in inline_button.url
        
    finally:
        await stop_rabbitmq_consumer(conn)
        from backend.app.db import db
        await db.disconnect()
