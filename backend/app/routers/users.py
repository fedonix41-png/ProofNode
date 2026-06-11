import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.db import db
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])

class ReferralStatsResponse(BaseModel):
    user_id: int
    referral_code: str
    total_referred: int
    referral_credits: int

class ApplyReferralRequest(BaseModel):
    user_id: int
    referral_code: str

@router.get("/referrals", response_model=ReferralStatsResponse, status_code=status.HTTP_200_OK)
async def get_referrals(user_id: int):
    async for conn in db.get_connection():
        # Get or create user referral code
        user = await conn.fetchrow("SELECT referral_code, referral_credits FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
        referral_code = user["referral_code"]
        referral_credits = user["referral_credits"] or 0
        
        if not referral_code:
            # Generate a new referral code
            import secrets
            referral_code = f"{secrets.token_hex(4)}"
            await conn.execute("UPDATE users SET referral_code = $1 WHERE id = $2", referral_code, user_id)
            
        # Count referred
        count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE referred_by = $1", user_id)
        
        return ReferralStatsResponse(
            user_id=user_id,
            referral_code=referral_code,
            total_referred=count,
            referral_credits=referral_credits
        )

@router.post("/apply_referral", status_code=status.HTTP_200_OK)
async def apply_referral_endpoint(req: ApplyReferralRequest):
    async for conn in db.get_connection():
        # Clean prefix if exists
        code = req.referral_code
        if code.startswith("ref_"):
            code = code[4:]
            
        # Find referrer
        referrer = await conn.fetchrow("SELECT id FROM users WHERE referral_code = $1", code)
        if not referrer:
            return {"status": "ignored", "detail": "Invalid referral code"}
            
        referrer_id = referrer["id"]
        if referrer_id == req.user_id:
            return {"status": "ignored", "detail": "Cannot refer yourself"}
            
        # Check if already referred
        current_user = await conn.fetchrow("SELECT referred_by FROM users WHERE id = $1", req.user_id)
        if current_user and current_user["referred_by"] is not None:
            return {"status": "ignored", "detail": "User already referred"}
            
        # Update user's referred_by
        await conn.execute("UPDATE users SET referred_by = $1 WHERE id = $2", referrer_id, req.user_id)
        
        # We don't apply credit immediately; plan says "invited user must connect wallet or complete one trade"
        # However, we can apply credit here for simplicity if the plan meant this action.
        # But wait, plan says "invited user must connect wallet or complete one trade" -> "apply_referral_credit"
        # So we just set `referred_by` here.
        return {"status": "success", "detail": "Referral linked"}
