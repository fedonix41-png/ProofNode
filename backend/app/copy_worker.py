import asyncio
import json
import logging
import signal
from decimal import Decimal
import aio_pika
from uuid import UUID

from backend.app.config import settings
from backend.app.db import db
from backend.app.services.kms import kms_service
from backend.app.services.dex import dex_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_connection: aio_pika.abc.AbstractConnection | None = None
rabbitmq_channel: aio_pika.abc.AbstractChannel | None = None

async def execute_automated_trade(conn, job: dict) -> None:
    user_id = job["user_id"]
    proxy_wallet_id = UUID(job["proxy_wallet_id"])
    blockchain = job["blockchain"]
    token_in = job["token_in"]
    token_out = job["token_out"]
    amount_in = Decimal(job["amount_in"])
    trader_tx_hash = job["trader_tx_hash"]
    
    # 1. Fetch proxy wallet details
    wallet = await conn.fetchrow(
        "SELECT address, encrypted_private_key, balance FROM user_proxy_wallets WHERE id = $1 AND user_id = $2",
        proxy_wallet_id, user_id
    )
    if not wallet:
        raise ValueError("User proxy wallet not found.")
        
    # 2. Check balance
    if wallet["balance"] < amount_in:
        logger.warning(f"User {user_id} has insufficient proxy wallet balance ({wallet['balance']} < {amount_in}). Recording failure.")
        # Log execution failure
        await conn.execute(
            """
            INSERT INTO copy_trade_executions (user_id, trader_tx_hash, status, error_message, blockchain)
            VALUES ($1, $2, 'FAILED', $3, $4)
            """,
            user_id, trader_tx_hash, "Insufficient proxy wallet balance", blockchain
        )
        return

    # 3. Decrypt key
    try:
        private_key = kms_service.decrypt_key(wallet["encrypted_private_key"])
    except Exception as e:
        logger.error(f"Failed to decrypt key using KMS for wallet {proxy_wallet_id}: {e}")
        await conn.execute(
            """
            INSERT INTO copy_trade_executions (user_id, trader_tx_hash, status, error_message, blockchain)
            VALUES ($1, $2, 'FAILED', $3, $4)
            """,
            user_id, trader_tx_hash, f"KMS key decryption failed: {e}", blockchain
        )
        return

    # 4. Request DEX Swap Quote
    quote = dex_service.get_swap_quote(blockchain, token_in, token_out, amount_in)
    
    # 5. Sign and Broadcast
    try:
        tx_hash = dex_service.sign_and_broadcast_transaction(blockchain, quote, private_key)
    except Exception as e:
        logger.error(f"DEX broadcast failed: {e}")
        await conn.execute(
            """
            INSERT INTO copy_trade_executions (user_id, trader_tx_hash, status, error_message, blockchain)
            VALUES ($1, $2, 'FAILED', $3, $4)
            """,
            user_id, trader_tx_hash, f"DEX transaction broadcast failed: {e}", blockchain
        )
        return

    # 6. Deduct balance from proxy wallet
    await conn.execute(
        "UPDATE user_proxy_wallets SET balance = balance - $1 WHERE id = $2",
        amount_in, proxy_wallet_id
    )

    # 7. Record success
    await conn.execute(
        """
        INSERT INTO copy_trade_executions (user_id, trader_tx_hash, copy_tx_hash, blockchain, status)
        VALUES ($1, $2, $3, $4, 'SUCCESS')
        """,
        user_id, trader_tx_hash, tx_hash, blockchain
    )
    logger.info(f"Successfully executed automated trade copying for user {user_id}. Copy Tx: {tx_hash}")

async def create_1click_signal(conn, job: dict) -> None:
    user_id = job["user_id"]
    blockchain = job["blockchain"]
    token_in = job["token_in"]
    token_out = job["token_out"]
    amount_in = Decimal(job["amount_in"])
    trader_tx_hash = job["trader_tx_hash"]
    
    # 1. Insert pending copy trade
    pending = await conn.fetchrow(
        """
        INSERT INTO pending_copy_trades (user_id, trader_tx_hash, blockchain, token_in_address, token_out_address, amount_in, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'PENDING')
        RETURNING id
        """,
        user_id, trader_tx_hash, blockchain, token_in, token_out, amount_in
    )
    
    # 2. Publish bot notification alert
    global rabbitmq_channel
    if rabbitmq_channel:
        alert_payload = {
            "user_id": user_id,
            "type": "1CLICK_COPY_ALERT",
            "pending_trade_id": str(pending["id"]),
            "trader_tx_hash": trader_tx_hash,
            "blockchain": blockchain,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": str(amount_in)
        }
        await rabbitmq_channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(alert_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="tg_bot_notifications"
        )
        logger.info(f"Published 1-Click copy alert for user {user_id} regarding trade {trader_tx_hash}")

async def process_job(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            job = json.loads(message.body.decode())
            logger.info(f"Consumed copy trade job: {job.get('copy_mode')} for user {job.get('user_id')}")
            
            async for conn in db.get_connection():
                if job.get("copy_mode") == "AUTOMATED":
                    await execute_automated_trade(conn, job)
                elif job.get("copy_mode") == "1-CLICK":
                    await create_1click_signal(conn, job)
                else:
                    logger.error(f"Unknown copy mode: {job.get('copy_mode')}")
                break
        except Exception as e:
            logger.error(f"Failed to process copy job: {e}")
            # Do not requeue poison pills, let context handle it
            raise e

async def main() -> None:
    global rabbitmq_connection, rabbitmq_channel
    # 1. Connect DB
    await db.connect()
    
    # 2. Connect RMQ
    rabbitmq_connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    rabbitmq_channel = await rabbitmq_connection.channel()
    
    await rabbitmq_channel.set_qos(prefetch_count=10)
    
    # Ensure queue exists and bind to it
    queue = await rabbitmq_channel.declare_queue("copy_trade_execution", durable=True)
    
    logger.info("Copy-Trading Execution Worker started. Listening...")
    
    await queue.consume(process_job)
    
    # Shutdown hooks
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def shutdown_handler():
        logger.info("Termination signal received. Shutting down...")
        stop_event.set()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler)
        
    await stop_event.wait()
    
    await rabbitmq_connection.close()
    await db.disconnect()
    logger.info("Copy-Trading Execution Worker shut down successfully.")

if __name__ == "__main__":
    asyncio.run(main())
