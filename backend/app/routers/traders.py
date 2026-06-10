import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from backend.app.db import db

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

class TariffCreate(BaseModel):
    trader_profile_id: UUID
    duration_days: int = Field(..., gt=0)
    price_stars: Optional[int] = Field(None, ge=0)
    price_crypto: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("TON", max_length=10)

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
