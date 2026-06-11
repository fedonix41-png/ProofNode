import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from typing import Optional

from backend.app.db import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/copytrade", tags=["copytrade"])

# Pydantic schemas
class CopyTradeConfigCreate(BaseModel):
    subscription_id: UUID
    copy_mode: str = Field(..., pattern="^(1-CLICK|AUTOMATED)$")
    proxy_wallet_id: Optional[UUID] = None
    max_allocation_per_trade: Decimal = Field(..., gt=0)
    slippage_bps: int = Field(default=100, ge=1, le=1000) # 0.01% to 10%
    is_active: bool = Field(default=True)

class Execute1ClickRequest(BaseModel):
    pending_trade_id: UUID
    tx_hash: str = Field(..., min_length=5, max_length=128)

# Endpoints
@router.post("/config", status_code=status.HTTP_200_OK)
async def configure_copy_trade(payload: CopyTradeConfigCreate):
    async for conn in db.get_connection():
        # Validate subscription exists
        sub = await conn.fetchrow("SELECT id, user_id FROM subscriptions WHERE id = $1", payload.subscription_id)
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
            
        # Validate proxy wallet if mode is AUTOMATED
        if payload.copy_mode == "AUTOMATED":
            if not payload.proxy_wallet_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="proxy_wallet_id is required when copy_mode is AUTOMATED"
                )
            # Verify proxy wallet exists and belongs to the correct user
            proxy = await conn.fetchrow(
                "SELECT id FROM user_proxy_wallets WHERE id = $1 AND user_id = $2",
                payload.proxy_wallet_id, sub["user_id"]
            )
            if not proxy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Proxy wallet not found or does not belong to the subscriber."
                )

        try:
            row = await conn.fetchrow(
                """
                INSERT INTO copy_trade_configs (
                    subscription_id, copy_mode, proxy_wallet_id, max_allocation_per_trade, slippage_bps, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (subscription_id)
                DO UPDATE SET 
                    copy_mode = EXCLUDED.copy_mode,
                    proxy_wallet_id = EXCLUDED.proxy_wallet_id,
                    max_allocation_per_trade = EXCLUDED.max_allocation_per_trade,
                    slippage_bps = EXCLUDED.slippage_bps,
                    is_active = EXCLUDED.is_active,
                    created_at = CURRENT_TIMESTAMP
                RETURNING id, subscription_id, copy_mode, proxy_wallet_id, max_allocation_per_trade, slippage_bps, is_active
                """,
                payload.subscription_id,
                payload.copy_mode,
                payload.proxy_wallet_id,
                payload.max_allocation_per_trade,
                payload.slippage_bps,
                payload.is_active
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error configuring copy trade: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

@router.get("/config/{subscription_id}", status_code=status.HTTP_200_OK)
async def get_copy_trade_config(subscription_id: UUID):
    async for conn in db.get_connection():
        row = await conn.fetchrow(
            """
            SELECT id, subscription_id, copy_mode, proxy_wallet_id, max_allocation_per_trade, slippage_bps, is_active
            FROM copy_trade_configs
            WHERE subscription_id = $1
            """,
            subscription_id
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Copy trading configuration not found for subscription."
            )
        return dict(row)

@router.post("/execute-1click", status_code=status.HTTP_200_OK)
async def execute_1click_trade(payload: Execute1ClickRequest):
    async for conn in db.get_connection():
        # Get pending copy trade
        pending = await conn.fetchrow(
            "SELECT id, user_id, trader_tx_hash, blockchain FROM pending_copy_trades WHERE id = $1",
            payload.pending_trade_id
        )
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending copy trade signal not found."
            )
            
        try:
            # Update status to EXECUTED
            await conn.execute(
                "UPDATE pending_copy_trades SET status = 'EXECUTED' WHERE id = $1",
                payload.pending_trade_id
            )
            
            # Log execution success
            exec_row = await conn.fetchrow(
                """
                INSERT INTO copy_trade_executions (user_id, trader_tx_hash, copy_tx_hash, blockchain, status)
                VALUES ($1, $2, $3, $4, 'SUCCESS')
                RETURNING id, user_id, trader_tx_hash, copy_tx_hash, blockchain, status, executed_at
                """,
                pending["user_id"], pending["trader_tx_hash"], payload.tx_hash, pending["blockchain"]
            )
            return dict(exec_row)
        except Exception as e:
            logger.error(f"Error executing 1-Click trade: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )
