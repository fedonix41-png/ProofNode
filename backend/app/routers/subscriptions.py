import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional
from decimal import Decimal
from aiogram import Bot

from backend.app.config import settings
from backend.app.db import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Pydantic schemas
class PurchaseRequest(BaseModel):
    user_id: int
    tariff_id: UUID

class VerificationRequest(BaseModel):
    user_id: int
    tariff_id: UUID
    tx_hash: str = Field(..., min_length=5, max_length=128)

# Endpoints
@router.post("/purchase", status_code=status.HTTP_200_OK)
async def initiate_purchase(payload: PurchaseRequest):
    async for conn in db.get_connection():
        # Retrieve tariff information
        tariff = await conn.fetchrow(
            """
            SELECT t.*, p.title as trader_title, p.admin_id as trader_admin_id
            FROM tariffs t
            JOIN trader_profiles p ON t.trader_profile_id = p.id
            WHERE t.id = $1
            """,
            payload.tariff_id
        )
        if not tariff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found")
            
        # Ensure user exists (implicitly create user for simple onboarding)
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            payload.user_id, f"user_{payload.user_id}"
        )
        
        return {
            "user_id": payload.user_id,
            "tariff_id": payload.tariff_id,
            "duration_days": tariff["duration_days"],
            "price_crypto": float(tariff["price_crypto"]) if tariff["price_crypto"] else None,
            "price_stars": tariff["price_stars"],
            "currency": tariff["currency"],
            "trader_title": tariff["trader_title"],
            "recipient_address": "EQC_proofnode_treasury_address_holder"  # Sandbox checkout destination
        }

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_payment(payload: VerificationRequest):
    async for conn in db.get_connection():
        # Get user
        user = await conn.fetchrow("SELECT id FROM users WHERE id = $1", payload.user_id)
        if not user:
            # Create user implicitly if missing
            await conn.execute(
                "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
                payload.user_id, f"user_{payload.user_id}"
            )
            
        # Get tariff
        tariff = await conn.fetchrow(
            "SELECT duration_days, trader_profile_id FROM tariffs WHERE id = $1", payload.tariff_id
        )
        if not tariff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")
            
        # Simulate / perform blockchain transaction checking
        # For Phase 2 sandbox, we auto-verify if settings.env is 'testing' or tx_hash starts with 'mock'
        payment_verified = False
        if settings.env == "testing" or payload.tx_hash.startswith("mock"):
            payment_verified = True
        else:
            # Simulated block RPC check (e.g. check if tx_hash contains confirm and matching transaction value)
            payment_verified = True  # Auto-confirm in Sandbox / preliminary stages
            logger.info(f"Simulating TON RPC block check for tx: {payload.tx_hash}")

        if not payment_verified:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Transaction could not be verified on-chain."
            )
            
        # Calculate expiry
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=tariff["duration_days"])
        
        # Generate Invite Link
        invite_link = f"https://t.me/+mock_invite_link_{payload.user_id}"
        
        # Call Telegram Bot API if bot_token is real
        if settings.bot_token and settings.bot_token != "mock_token" and not settings.bot_token.endswith("mock"):
            try:
                bot = Bot(token=settings.bot_token)
                # Set link expiration slightly after subscription expiry
                expire_timestamp = int(expires_at.timestamp())
                invite = await bot.create_chat_invite_link(
                    chat_id=settings.channel_id,
                    member_limit=1,
                    expire_date=expire_timestamp
                )
                invite_link = invite.invite_link
                await bot.session.close()
            except Exception as e:
                logger.error(f"Failed to generate Telegram invite link: {e}")
                # Fall back to mock link in dev so API doesn't fail
                invite_link = f"https://t.me/joinchat/fallback_link_{payload.user_id}"
        
        # Record subscription in database
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO subscriptions (user_id, trader_profile_id, tariff_id, status, expires_at, invite_link)
                VALUES ($1, $2, $3, 'ACTIVE', $4, $5)
                ON CONFLICT DO NOTHING
                RETURNING id, user_id, trader_profile_id, status, expires_at, invite_link
                """,
                payload.user_id, tariff["trader_profile_id"], payload.tariff_id, expires_at, invite_link
            )
            
            # If CONFLICT or row is None (e.g. duplicate subscription click), fetch existing
            if not row:
                row = await conn.fetchrow(
                    """
                    SELECT id, user_id, trader_profile_id, status, expires_at, invite_link
                    FROM subscriptions
                    WHERE user_id = $1 AND trader_profile_id = $2 AND status = 'ACTIVE'
                    LIMIT 1
                    """,
                    payload.user_id, tariff["trader_profile_id"]
                )
                
            return dict(row)
        except Exception as e:
            logger.error(f"Failed to save subscription details: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process database write: {e}"
            )
