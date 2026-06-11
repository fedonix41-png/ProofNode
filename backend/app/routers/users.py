import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.db import db
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])

class ReferralStatsResponse(BaseModel):
    user_id: int
    referral_code: str
    total_referred: int

@router.get("/referrals", response_model=ReferralStatsResponse, status_code=status.HTTP_200_OK)
async def get_referrals(user_id: int):
    async for conn in db.get_connection():
        # Get or create user referral code
        user = await conn.fetchrow("SELECT referral_code FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
        referral_code = user["referral_code"]
        if not referral_code:
            # Generate a new referral code
            import secrets
            referral_code = f"ref_{secrets.token_hex(4)}"
            await conn.execute("UPDATE users SET referral_code = $1 WHERE id = $2", referral_code, user_id)
            
        # Count referred
        count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE referred_by = $1", user_id)
        
        return ReferralStatsResponse(
            user_id=user_id,
            referral_code=referral_code,
            total_referred=count
        )
