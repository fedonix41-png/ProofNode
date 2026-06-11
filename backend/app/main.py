import logging
import json
from contextlib import asynccontextmanager
import hmac
import hashlib
from fastapi import FastAPI, HTTPException, Header, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aio_pika
import redis.asyncio as aioredis

from backend.app.config import settings
from backend.app.db import db
from backend.app.schemas import TonWebhookPayload, SolWebhookPayload, EvmWebhookPayload
from backend.app.routers import traders, subscriptions, wallets, copytrade, users, signals
from backend.app.services.rpc import rpc_client

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[FastApiIntegration()])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state holders
rabbitmq_connection: aio_pika.abc.AbstractConnection | None = None
rabbitmq_channel: aio_pika.abc.AbstractChannel | None = None
rabbitmq_queue: aio_pika.abc.AbstractQueue | None = None
rabbitmq_copy_queue: aio_pika.abc.AbstractQueue | None = None
rabbitmq_bot_queue: aio_pika.abc.AbstractQueue | None = None
redis_client: aioredis.Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_queue, rabbitmq_copy_queue, rabbitmq_bot_queue, redis_client
    
    # 1. Initialize DB Connection Pool
    await db.connect()
    
    # 2. Initialize Redis client
    redis_url = f"redis://{settings.redis_host}:{settings.redis_port}"
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    logger.info("Connected to Redis.")
    
    # 3. Initialize RabbitMQ connection and channel
    try:
        rabbitmq_connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        rabbitmq_channel = await rabbitmq_connection.channel()
        # Declare queue for raw transaction events
        rabbitmq_queue = await rabbitmq_channel.declare_queue(
            "raw_blockchain_events",
            durable=True
        )
        # Declare queue for copy-trade executions
        rabbitmq_copy_queue = await rabbitmq_channel.declare_queue(
            "copy_trade_execution",
            durable=True
        )
        # Declare queue for bot notifications
        rabbitmq_bot_queue = await rabbitmq_channel.declare_queue(
            "tg_bot_notifications",
            durable=True
        )
        logger.info("Connected to RabbitMQ and declared raw_blockchain_events, copy_trade_execution, and tg_bot_notifications queues.")
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ connection: {e}")
        # In a real environment, we'd fall back or handle connection failures.
        
    yield
    
    # Clean up resources on shutdown
    if rabbitmq_connection:
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed.")
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis client closed.")
    await rpc_client.close()
    await db.disconnect()

app = FastAPI(
    title="ProofNode Gateway API",
    description="Stateless Webhook Ingestion Gateway for ProofNode blockchain transaction event tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "https://proof.vdkgame.sbs"
    ],
    allow_origin_regex=r"https://.*\.trycloudflare\.com|https://.*\.ngrok-free\.app|https://.*\.t\.me",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traders.router)
app.include_router(subscriptions.router)
app.include_router(wallets.router)
app.include_router(copytrade.router)
app.include_router(users.router)
app.include_router(signals.router)

if settings.prometheus_enabled:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Health endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    health_status = {"status": "ok", "db": "disconnected", "redis": "disconnected", "rabbitmq": "disconnected"}
    
    # Check DB pool
    try:
        async for conn in db.get_connection():
            await conn.execute("SELECT 1")
            health_status["db"] = "connected"
            break
    except Exception:
        health_status["db"] = "error"
            
    # Check Redis
    if redis_client:
        try:
            if await redis_client.ping():
                health_status["redis"] = "connected"
        except Exception:
            health_status["redis"] = "error"
            
    # Check RabbitMQ
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        health_status["rabbitmq"] = "connected"
        
    if "error" in health_status.values() or "disconnected" in health_status.values():
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)
        
    return health_status

# Deduplication check helper using Redis
async def is_duplicate_transaction(tx_hash: str) -> bool:
    if not redis_client:
        return False
    # Set with 1-hour expiration to prevent processing duplicate webhooks
    key = f"proofnode:tx:{tx_hash}"
    is_new = await redis_client.set(key, "1", ex=3600, nx=True)
    return is_new is None

# RabbitMQ enqueue helper
async def enqueue_raw_event(blockchain: str, tx_hash: str, payload: dict) -> None:
    if not rabbitmq_channel:
        logger.error("RabbitMQ channel is offline. Ingestion failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Queue service unavailable. Local write fallback triggered."
        )
        
    message_body = {
        "blockchain": blockchain,
        "tx_hash": tx_hash,
        "payload": payload
    }
    
    await rabbitmq_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message_body, default=str).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key="raw_blockchain_events"
    )
    logger.info(f"Enqueued {blockchain} transaction {tx_hash} to RabbitMQ.")

@app.post("/gateway/ton", status_code=status.HTTP_202_ACCEPTED)
async def ingest_ton_webhook(
    payload: TonWebhookPayload,
    authorization: str = Header(None, alias="Authorization"),
    x_tonapi_signature: str = Header(None, alias="X-Tonapi-Signature")
):
    # Signature checking
    if settings.env != "testing":
        valid_auth = authorization == f"Bearer {settings.tonapi_webhook_secret}"
        valid_sig = x_tonapi_signature == settings.tonapi_webhook_secret
        if not (valid_auth or valid_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Deduplication
    if await is_duplicate_transaction(payload.tx_hash):
        logger.info(f"Duplicate TON transaction ignored: {payload.tx_hash}")
        return {"status": "ignored", "reason": "duplicate", "tx_hash": payload.tx_hash}
        
    # Ingestion
    await enqueue_raw_event("TON", payload.tx_hash, payload.model_dump())
    return {"status": "queued", "tx_hash": payload.tx_hash}

@app.post("/gateway/sol", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sol_webhook(
    payload: SolWebhookPayload,
    authorization: str = Header(None, alias="Authorization")
):
    # Signature checking
    if settings.env != "testing":
        if not authorization or authorization != settings.helius_webhook_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Deduplication
    if await is_duplicate_transaction(payload.tx_hash):
        logger.info(f"Duplicate Solana transaction ignored: {payload.tx_hash}")
        return {"status": "ignored", "reason": "duplicate", "tx_hash": payload.tx_hash}
        
    # Ingestion
    await enqueue_raw_event("SOL", payload.tx_hash, payload.model_dump())
    return {"status": "queued", "tx_hash": payload.tx_hash}

@app.post("/gateway/evm", status_code=status.HTTP_202_ACCEPTED)
async def ingest_evm_webhook(
    request: Request,
    payload: EvmWebhookPayload,
    x_alchemy_signature: str = Header(None, alias="X-Alchemy-Signature")
):
    # Signature checking
    if settings.env != "testing":
        if not x_alchemy_signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")
            
        body = await request.body()
        secret = settings.alchemy_webhook_secret.encode("utf-8")
        computed_sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(computed_sig, x_alchemy_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    # Deduplication
    if await is_duplicate_transaction(payload.tx_hash):
        logger.info(f"Duplicate EVM transaction ignored: {payload.tx_hash}")
        return {"status": "ignored", "reason": "duplicate", "tx_hash": payload.tx_hash}
        
    # Ingestion
    await enqueue_raw_event("BASE", payload.tx_hash, payload.model_dump())
    return {"status": "queued", "tx_hash": payload.tx_hash}
