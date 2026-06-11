import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from backend.app.db import db
from backend.app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/signals", tags=["signals"])

class SignalCreate(BaseModel):
    trader_profile_id: UUID
    token_address: str = Field(..., max_length=256)
    blockchain: str = Field(..., max_length=10)
    type: str = Field(..., pattern="^(BUY|SELL)$")
    target_price: float = Field(None, gt=0)
    stop_loss: float = Field(None, gt=0)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_signal(payload: SignalCreate, current_user: int = Depends(get_current_user)):
    async for conn in db.get_connection():
        # Check if trader profile exists and user owns it
        profile = await conn.fetchrow("SELECT id FROM trader_profiles WHERE id = $1 AND admin_id = $2", payload.trader_profile_id, current_user)
        if not profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trader profile not found or access denied")
            
        # In a real app we'd insert into a signals table, but for now we'll mock the response
        # or we could create the table if we wanted to
        logger.info(f"Signal created for profile {payload.trader_profile_id}: {payload.type} {payload.token_address} on {payload.blockchain}")
        return {
            "status": "success",
            "message": "Signal created successfully",
            "signal": payload.model_dump()
        }
