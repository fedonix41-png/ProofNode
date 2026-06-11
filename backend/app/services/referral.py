import logging
import asyncpg
from typing import Optional
from backend.app.config import settings

logger = logging.getLogger(__name__)

def generate_referral_link(referral_code: str) -> str:
    """
    Generates a shareable Telegram Mini App link with startapp parameter.
    """
    return f"https://t.me/AlphaHubBot/app?startapp=ref_{referral_code}"

async def apply_referral_credit(pool: asyncpg.Pool, referrer_id: int, referred_id: int) -> bool:
    """
    Apply referral credit to the referrer after the referred user completes an action.
    Returns True if successfully incremented.
    """
    async with pool.acquire() as conn:
        try:
            # Increment referral_credits by 1 for the referrer
            result = await conn.execute(
                "UPDATE users SET referral_credits = referral_credits + 1 WHERE id = $1",
                referrer_id
            )
            
            if result == "UPDATE 1":
                logger.info(f"Successfully applied referral credit to referrer {referrer_id} for user {referred_id}")
                return True
            else:
                logger.warning(f"Failed to apply referral credit to referrer {referrer_id}")
                return False
        except Exception as e:
            logger.error(f"Error applying referral credit: {e}")
            return False

def get_max_wallets(is_premium: bool, referral_credits: int) -> int:
    """
    Returns the maximum number of wallets a user can have.
    3 base slots + (referral_credits * REFERRAL_CREDIT_PER_INVITE).
    Returns -1 for unlimited slots (premium).
    """
    if is_premium:
        return -1  # Represents unlimited
    
    return 3 + (referral_credits * settings.referral_credit_per_invite)
