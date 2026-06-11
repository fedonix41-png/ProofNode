import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from backend.app.db import db
from backend.app.services.rpc import rpc_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/traders", tags=["traders"])

# Pydantic schemas for requests
class TraderProfileCreate(BaseModel):
    admin_id: int
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    public_slug: str = Field(..., max_length=50)

class TraderWalletCreate(BaseModel):
    trader_profile_id: UUID
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    address: str = Field(..., max_length=256)

class TraderWalletCreatePath(BaseModel):
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    address: str = Field(..., max_length=256)

class TariffCreate(BaseModel):
    trader_profile_id: UUID
    duration_days: int = Field(..., gt=0)
    price_stars: Optional[int] = Field(None, ge=0)
    price_crypto: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("TON", max_length=10)

class SignalCreateRequest(BaseModel):
    token_address: str = Field(..., max_length=256)
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    direction: str = Field(..., pattern="^(BUY|SELL)$")

# Endpoints
@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_trader_profile(payload: TraderProfileCreate):
    # Ensure user exists first (or create user implicitly for ease of setup/testing)
    async for conn in db.get_connection():
        # First make sure the admin user exists
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            payload.admin_id, f"trader_{payload.admin_id}"
        )
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO trader_profiles (admin_id, title, description, public_slug)
                VALUES ($1, $2, $3, $4)
                RETURNING id, admin_id, title, description, is_verified, public_slug, created_at
                """,
                payload.admin_id, payload.title, payload.description, payload.public_slug
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error creating trader profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug '{payload.public_slug}' might already be taken or invalid payload: {e}"
            )

@router.get("", status_code=status.HTTP_200_OK)
async def list_traders(category: Optional[str] = None):
    async for conn in db.get_connection():
        query = "SELECT id, title, description, category, is_verified, public_slug, created_at FROM trader_profiles"
        args = []
        if category:
            query += " WHERE category = $1"
            args.append(category)
        
        query += " ORDER BY created_at DESC"
        
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]

@router.post("/wallets", status_code=status.HTTP_201_CREATED)
async def add_trader_wallet(payload: TraderWalletCreate):
    async for conn in db.get_connection():
        # Check if profile exists
        profile = await conn.fetchrow("SELECT id FROM trader_profiles WHERE id = $1", payload.trader_profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
            
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO trader_wallets (trader_profile_id, blockchain, address)
                VALUES ($1, $2, $3)
                RETURNING id, trader_profile_id, blockchain, address, created_at
                """,
                payload.trader_profile_id, payload.blockchain, payload.address
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error registering trader wallet: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Wallet for {payload.blockchain} address {payload.address} already registered: {e}"
            )

@router.post("/{id}/wallets", status_code=status.HTTP_201_CREATED)
async def add_trader_wallet_by_id(id: UUID, payload: TraderWalletCreatePath):
    return await add_trader_wallet(
        TraderWalletCreate(
            trader_profile_id=id,
            blockchain=payload.blockchain,
            address=payload.address
        )
    )

@router.post("/tariffs", status_code=status.HTTP_201_CREATED)
async def create_tariff(payload: TariffCreate):
    async for conn in db.get_connection():
        # Check if profile exists
        profile = await conn.fetchrow("SELECT id FROM trader_profiles WHERE id = $1", payload.trader_profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
            
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO tariffs (trader_profile_id, duration_days, price_stars, price_crypto, currency)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, trader_profile_id, duration_days, price_stars, price_crypto, currency
                """,
                payload.trader_profile_id, payload.duration_days, payload.price_stars, payload.price_crypto, payload.currency
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error creating tariff: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create tariff: {e}"
            )

@router.get("/{slug}", status_code=status.HTTP_200_OK)
async def get_trader_by_slug(slug: str):
    async for conn in db.get_connection():
        row = await conn.fetchrow(
            """
            SELECT id, admin_id, title, description, category, is_verified, public_slug, created_at 
            FROM trader_profiles WHERE public_slug = $1
            """,
            slug
        )
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader not found")
            
        trader_dict = dict(row)
        
        # Get recent signals
        signals = await conn.fetch(
            "SELECT id, blockchain, token_address, direction, entry_price, exit_price, pnl_percent, status, created_at, closed_at FROM signals WHERE trader_profile_id = $1 ORDER BY created_at DESC LIMIT 10",
            trader_dict["id"]
        )
        trader_dict["recent_signals"] = [dict(s) for s in signals]
        
        # Mock stats (in a real app, query trader_pnl_history)
        trader_dict["stats"] = {
            "cumulative_roi": "15.0",
            "winrate": "65.0",
            "drawdown": "10.0"
        }
        
        return trader_dict

@router.post("/{id}/signals", status_code=status.HTTP_201_CREATED)
async def create_signal(id: UUID, payload: SignalCreateRequest):
    async for conn in db.get_connection():
        # Check if profile exists
        profile = await conn.fetchrow("SELECT id FROM trader_profiles WHERE id = $1", id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
            
        # Capture current price via RPC
        entry_price = await rpc_client.get_token_price(payload.blockchain, payload.token_address)
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO signals (trader_profile_id, blockchain, token_address, direction, entry_price, status)
                VALUES ($1, $2, $3, $4, $5, 'OPEN')
                RETURNING id, trader_profile_id, blockchain, token_address, direction, entry_price, status, created_at
                """,
                id, payload.blockchain, payload.token_address, payload.direction, entry_price
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create signal: {e}"
            )

@router.post("/{id}/signals/{signal_id}/close", status_code=status.HTTP_200_OK)
async def close_signal(id: UUID, signal_id: UUID):
    async for conn in db.get_connection():
        signal = await conn.fetchrow(
            "SELECT id, blockchain, token_address, direction, entry_price, status FROM signals WHERE id = $1 AND trader_profile_id = $2",
            signal_id, id
        )
        if not signal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")
            
        if signal["status"] != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signal is already closed")
            
        # Capture exit price
        exit_price = await rpc_client.get_token_price(signal["blockchain"], signal["token_address"])
        
        pnl_percent = Decimal(0)
        if signal["entry_price"] and exit_price:
            entry = Decimal(signal["entry_price"])
            exit_p = Decimal(exit_price)
            if signal["direction"] == "BUY":
                pnl_percent = ((exit_p - entry) / entry) * Decimal(100)
            else:
                pnl_percent = ((entry - exit_p) / entry) * Decimal(100)
                
        now = datetime.now()
        row = await conn.fetchrow(
            """
            UPDATE signals 
            SET status = 'CLOSED', exit_price = $1, pnl_percent = $2, closed_at = $3
            WHERE id = $4
            RETURNING id, status, exit_price, pnl_percent, closed_at
            """,
            exit_price, pnl_percent, now, signal_id
        )
        return dict(row)

import json
import redis.asyncio as redis
from backend.app.config import settings

redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

@router.get("/top-week", status_code=status.HTTP_200_OK)
async def get_top_traders_week():
    cache_key = "traders:top-week"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
        
    async for conn in db.get_connection():
        # In a real app we'd query trader_pnl_history or calculate from signals in the last 7 days.
        # For this MVP, we will return some mock data or calculate from `trader_pnl_history` if it exists.
        # Let's mock it according to the schema since we don't have actual trades populated.
        # The plan says: "Include basic stats: slug, name, ROI, winrate."
        
        query = """
            SELECT p.public_slug as slug, p.title as name, 
                   COALESCE((SELECT cumulative_roi FROM trader_pnl_history h WHERE h.trader_profile_id = p.id ORDER BY time DESC LIMIT 1), 0) as roi,
                   COALESCE((SELECT winrate FROM trader_pnl_history h WHERE h.trader_profile_id = p.id ORDER BY time DESC LIMIT 1), 50.0) as winrate
            FROM trader_profiles p
            ORDER BY roi DESC
            LIMIT 10
        """
        rows = await conn.fetch(query)
        
        # If no real data, provide placeholder mock data for UI testing
        results = [dict(r) for r in rows]
        if not results:
            results = [
                {"slug": "crypto-wizard", "name": "Crypto Wizard", "roi": 142.5, "winrate": 78.5},
                {"slug": "sniper-bot", "name": "TON Sniper", "roi": 85.2, "winrate": 65.0},
                {"slug": "whale-tracker", "name": "Whale Tracker", "roi": 45.1, "winrate": 60.0}
            ]
            
        await redis_client.set(cache_key, json.dumps(results), ex=3600) # 1 hour TTL
        return results
