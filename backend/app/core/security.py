import hashlib
import hmac
import urllib.parse
import json
import logging
from fastapi import HTTPException, status, Header
from backend.app.config import settings

logger = logging.getLogger(__name__)

def validate_telegram_data(init_data: str, bot_token: str) -> dict:
    """
    Validates the Telegram WebApp initData payload using the HMAC-SHA-256 algorithm.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    
    # Development bypass mock
    if settings.env in ["development", "testing"] and "mock_user_id" in parsed_data:
        return {"id": int(parsed_data["mock_user_id"])}

    if "hash" not in parsed_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash in Telegram initData")
        
    received_hash = parsed_data.pop("hash")
    
    # Data-check-string is a concatenation of all received fields, sorted alphabetically
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    # Secret key is HMAC-SHA-256 of the bot token with the constant string "WebAppData"
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    
    # Compute the hash of the data_check_string using the secret key
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if computed_hash != received_hash:
        logger.warning(f"Invalid Telegram signature attempt: expected {computed_hash}, got {received_hash}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature")
        
    if "user" not in parsed_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User payload missing from initData")
        
    try:
        user_dict = json.loads(parsed_data["user"])
        return user_dict
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user JSON format")

async def get_current_user(authorization: str = Header(None, description="Format: tma <initData> or Bearer <dev_user_id>")) -> int:
    """
    FastAPI Dependency to get the authenticated user's Telegram ID.
    Expects the 'Authorization: tma <initData>' header.
    In development, allows 'Authorization: Bearer <user_id>' for easy testing.
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
        
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")
        
    scheme, payload = parts[0].lower(), parts[1]
    
    # Local Dev override
    if scheme == "bearer" and settings.env in ["development", "testing"]:
        try:
            return int(payload)
        except ValueError:
            pass
            
    if scheme != "tma":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization scheme must be 'tma'")
        
    try:
        user_data = validate_telegram_data(payload, settings.bot_token)
        return int(user_data["id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse Telegram user data: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to parse Telegram user data")
