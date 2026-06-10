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
    # 1. Connect to Database connection pool
    await db.connect()
    
    # 2. Connect to RabbitMQ
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    
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
    await connection.close()
    await db.disconnect()
    logger.info("Worker shut down successfully.")

if __name__ == "__main__":
    asyncio.run(main())
