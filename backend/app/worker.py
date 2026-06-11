import asyncio
import json
import logging
import signal
from datetime import datetime
import aio_pika
from backend.app.config import settings
from backend.app.db import db
from backend.app.parser import parse_blockchain_transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_connection: aio_pika.abc.AbstractConnection | None = None
rabbitmq_channel: aio_pika.abc.AbstractChannel | None = None

async def insert_wallet_transaction(conn, parsed_tx: dict) -> None:
    query = """
        INSERT INTO wallet_transactions (
            time, tx_hash, trace_id, logical_time, wallet_address, blockchain,
            dex_name, token_in_address, token_out_address, amount_in, amount_out, usd_value, tx_type
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
        ON CONFLICT (time, tx_hash, wallet_address) DO NOTHING
    """
    await conn.execute(
        query,
        parsed_tx["time"],
        parsed_tx["tx_hash"],
        parsed_tx["trace_id"],
        parsed_tx["logical_time"],
        parsed_tx["wallet_address"],
        parsed_tx["blockchain"],
        parsed_tx["dex_name"],
        parsed_tx["token_in_address"],
        parsed_tx["token_out_address"],
        parsed_tx["amount_in"],
        parsed_tx["amount_out"],
        parsed_tx["usd_value"],
        parsed_tx["tx_type"]
    )

async def check_and_trigger_copy_trades(conn, parsed_tx: dict) -> None:
    # Check if the transaction wallet is a registered trader wallet
    trader_wallet = await conn.fetchrow(
        "SELECT trader_profile_id FROM trader_wallets WHERE blockchain = $1 AND address = $2",
        parsed_tx["blockchain"], parsed_tx["wallet_address"]
    )
    if not trader_wallet:
        return
        
    logger.info(f"Transaction {parsed_tx['tx_hash']} matches trader wallet for profile {trader_wallet['trader_profile_id']}. Checking copy-trade subscribers.")
    
    # Query subscribers with active configs
    subscribers = await conn.fetch(
        """
        SELECT s.id as subscription_id, s.user_id, c.copy_mode, c.proxy_wallet_id, c.max_allocation_per_trade, c.slippage_bps
        FROM subscriptions s
        JOIN copy_trade_configs c ON s.id = c.subscription_id
        WHERE s.trader_profile_id = $1 AND s.status = 'ACTIVE' AND s.expires_at > NOW() AND c.is_active = TRUE
        """,
        trader_wallet["trader_profile_id"]
    )
    
    if not subscribers:
        logger.info("No active subscribers with copy-trading enabled for this trader.")
        return
        
    # Enqueue copy job for each subscriber
    global rabbitmq_channel
    if not rabbitmq_channel:
        logger.error("RabbitMQ channel not initialized in worker. Cannot trigger copy trades.")
        return
        
    for sub in subscribers:
        job_payload = {
            "user_id": sub["user_id"],
            "subscription_id": str(sub["subscription_id"]),
            "trader_tx_hash": parsed_tx["tx_hash"],
            "blockchain": parsed_tx["blockchain"],
            "copy_mode": sub["copy_mode"],
            "proxy_wallet_id": str(sub["proxy_wallet_id"]) if sub["proxy_wallet_id"] else None,
            "token_in": parsed_tx["token_in_address"],
            "token_out": parsed_tx["token_out_address"],
            "amount_in": str(sub["max_allocation_per_trade"]),
            "slippage_bps": sub["slippage_bps"]
        }
        logger.info(f"Enqueuing copy trade job for user {sub['user_id']} ({sub['copy_mode']})")
        
        await rabbitmq_channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(job_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="copy_trade_execution"
        )

async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            body = json.loads(message.body.decode())
            blockchain = body.get("blockchain")
            tx_hash = body.get("tx_hash")
            payload = body.get("payload", {})
            
            logger.info(f"Processing transaction event: {blockchain} | {tx_hash}")
            
            # Extract basic params from payload model mapping
            wallet_address = payload.get("wallet_address")
            time_str = payload.get("time")
            raw_payload_str = payload.get("payload", "")
            
            if not wallet_address or not time_str:
                logger.error(f"Poison pill transaction event - missing critical fields: {body}")
                # Requeue=False is automatically handled by the context manager on exception
                return
                
            try:
                # ISO datetime parsing
                time_val = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            except ValueError:
                logger.error(f"Poison pill transaction event - invalid date format: {time_str}")
                return

            # Decode raw transaction
            parsed_tx = parse_blockchain_transaction(
                blockchain=blockchain,
                tx_hash=tx_hash,
                wallet_address=wallet_address,
                time_val=time_val,
                raw_payload=raw_payload_str
            )
            
            if parsed_tx is None:
                logger.error(f"Failed to parse transaction {tx_hash}")
                return

            # Save to Database
            async for conn in db.get_connection():
                await insert_wallet_transaction(conn, parsed_tx)
                logger.info(f"Successfully recorded transaction {tx_hash} to TimescaleDB.")
                
                # Check and trigger copy trades
                await check_and_trigger_copy_trades(conn, parsed_tx)
                break
                
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message body as JSON: {message.body}")
        except Exception as e:
            logger.error(f"Temporary processing failure for message: {e}")
            # If the database or broker connection goes down, we want to requeue this
            # message rather than dropping it.
            # To handle this, we raise an exception to tell the context manager
            # to let RabbitMQ requeue it (or manually reject with requeue=True).
            message.reject(requeue=True)
            raise e

async def main() -> None:
    global rabbitmq_connection, rabbitmq_channel
    # 1. Connect to Database connection pool
    await db.connect()
    
    # 2. Connect to RabbitMQ
    rabbitmq_connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    rabbitmq_channel = await rabbitmq_connection.channel()
    
    # Set prefetch count to limit concurrent message processing
    await channel.set_qos(prefetch_count=10)
    
    queue = await channel.declare_queue("raw_blockchain_events", durable=True)
    
    logger.info("Worker started. Listening for events...")
    
    # Start consuming messages
    await queue.consume(process_message)
    
    # Setup graceful shutdown handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def shutdown_handler():
        logger.info("Received termination signal. Stopping worker...")
        stop_event.set()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler)
        
    await stop_event.wait()
    
    # Clean up
    await rabbitmq_connection.close()
    await db.disconnect()
    logger.info("Worker shut down successfully.")

if __name__ == "__main__":
    asyncio.run(main())
