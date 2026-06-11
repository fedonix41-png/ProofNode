import asyncio
import json
import logging
import signal
from decimal import Decimal
import aio_pika
from uuid import UUID
import sentry_sdk

from backend.app.config import settings
from backend.app.db import db
from backend.app.services.kms import kms_service
from backend.app.services.dex import dex_service

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from prometheus_client import Histogram, start_http_server
TRADE_LATENCY = Histogram('copy_trade_latency_seconds', 'Time to execute copy trade')

rabbitmq_connection: aio_pika.abc.AbstractConnection | None = None
rabbitmq_channel: aio_pika.abc.AbstractChannel | None = None

if settings.prometheus_enabled:
    start_http_server(8001)

@TRADE_LATENCY.time()
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

    # 4. Request DEX Swap Quote & Execute with Retry
    max_attempts = 3
    base_slippage = 100
    tx_hash = None
    last_error = None
    
    for attempt in range(max_attempts):
        slippage = base_slippage * (attempt + 1)
        try:
            if blockchain == "SOL":
                quote = await dex_service.get_jupiter_quote(token_in, token_out, int(amount_in), slippage)
                if not quote:
                    raise ValueError("Failed to fetch Jupiter quote")
                unsigned_tx = await dex_service.get_jupiter_swap_tx(quote, wallet["address"])
                if not unsigned_tx:
                    raise ValueError("Failed to get Jupiter unsigned tx")
                pk_bytes = bytes.fromhex(private_key) if isinstance(private_key, str) else private_key
                tx_hash = await dex_service.sign_and_send_solana_tx(unsigned_tx, pk_bytes)
                
            elif blockchain == "BASE":
                quote = await dex_service.get_1inch_quote(token_in, token_out, str(int(amount_in)))
                if not quote:
                    raise ValueError("Failed to fetch 1inch quote")
                # 1inch expects slippage as a percentage (e.g. 1 for 1%)
                slippage_percent = slippage // 100
                unsigned_tx = await dex_service.get_1inch_swap_tx(token_in, token_out, str(int(amount_in)), wallet["address"], slippage_percent)
                if not unsigned_tx:
                    raise ValueError("Failed to get 1inch unsigned tx")
                tx_hash = await dex_service.sign_and_send_base_tx(unsigned_tx, private_key)
                
            elif blockchain == "TON":
                quote = await dex_service.get_stonfi_route(token_in, token_out, str(int(amount_in)))
                if not quote:
                    raise ValueError("Failed to fetch Stonfi quote")
                unsigned_tx = await dex_service.build_stonfi_swap_msg(quote, wallet["address"])
                if not unsigned_tx:
                    raise ValueError("Failed to build Stonfi unsigned tx")
                tx_hash = await dex_service.sign_and_send_ton_tx(unsigned_tx, private_key)
            else:
                raise ValueError(f"Unsupported blockchain: {blockchain}")

            if tx_hash:
                break
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Swap attempt {attempt+1} failed with slippage {slippage} bps: {e}")

    if not tx_hash:
        logger.error(f"DEX broadcast failed after {max_attempts} attempts. Last error: {last_error}")
        await conn.execute(
            """
            INSERT INTO copy_trade_executions (user_id, trader_tx_hash, status, error_message, blockchain)
            VALUES ($1, $2, 'FAILED', $3, $4)
            """,
            user_id, trader_tx_hash, f"DEX transaction broadcast failed: {last_error}", blockchain
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
