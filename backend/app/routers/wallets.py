import logging
import secrets
import hashlib
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from typing import Optional

from backend.app.db import db
from backend.app.services.kms import kms_service
from backend.app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/wallets", tags=["wallets"])

# Pydantic schemas
class SSSRegisterRequest(BaseModel):
    user_id: int
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    address: str = Field(..., max_length=256)
    server_share: str = Field(...)

class SSSRetrieveRequest(BaseModel):
    user_id: int
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    address: str = Field(..., max_length=256)

class ProxyWalletCreateRequest(BaseModel):
    user_id: int
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")

class ProxyWalletDepositRequest(BaseModel):
    proxy_wallet_id: UUID
    amount: Decimal = Field(..., gt=0)

class MonitoredWalletCreateRequest(BaseModel):
    user_id: int
    blockchain: str = Field(..., pattern="^(TON|BASE|SOL)$")
    address: str = Field(..., max_length=256)
    label: Optional[str] = None

# Endpoints
@router.post("/sss/register", status_code=status.HTTP_201_CREATED)
async def register_sss_share(payload: SSSRegisterRequest, current_user: int = Depends(get_current_user)):
    async for conn in db.get_connection():
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            current_user, f"user_{current_user}"
        )
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO user_sss_shares (user_id, blockchain, address, server_share)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, blockchain, address) 
                DO UPDATE SET server_share = EXCLUDED.server_share, created_at = CURRENT_TIMESTAMP
                RETURNING id, user_id, blockchain, address, created_at
                """,
                current_user, payload.blockchain, payload.address, payload.server_share
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error registering SSS share: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

@router.post("/sss/retrieve", status_code=status.HTTP_200_OK)
async def retrieve_sss_share(payload: SSSRetrieveRequest, current_user: int = Depends(get_current_user)):
    async for conn in db.get_connection():
        row = await conn.fetchrow(
            """
            SELECT server_share FROM user_sss_shares
            WHERE user_id = $1 AND blockchain = $2 AND address = $3
            """,
            current_user, payload.blockchain, payload.address
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server-side share not found for specified wallet."
            )
        return {"server_share": row["server_share"]}

@router.post("/proxy/create", status_code=status.HTTP_201_CREATED)
async def create_proxy_wallet(payload: ProxyWalletCreateRequest, current_user: int = Depends(get_current_user)):
    # Generate mock keypair
    private_key_hex = secrets.token_hex(32)
    
    # Generate mock address based on key hash
    key_hash = hashlib.sha256(private_key_hex.encode()).hexdigest()
    if payload.blockchain == "BASE":
        address = "0x" + key_hash[:40]
    elif payload.blockchain == "SOL":
        address = "sol_proxy_" + key_hash[:32]
    else:  # TON
        address = "EQ_proxy_" + key_hash[:32]
        
    # Encrypt private key using KMS
    encrypted_key = kms_service.encrypt_key(private_key_hex)
    
    async for conn in db.get_connection():
        # Ensure user exists
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            current_user, f"user_{current_user}"
        )
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO user_proxy_wallets (user_id, blockchain, address, encrypted_private_key, balance)
                VALUES ($1, $2, $3, $4, 0.0)
                ON CONFLICT (user_id, blockchain)
                DO UPDATE SET address = EXCLUDED.address, encrypted_private_key = EXCLUDED.encrypted_private_key, created_at = CURRENT_TIMESTAMP
                RETURNING id, user_id, blockchain, address, balance, created_at
                """,
                current_user, payload.blockchain, address, encrypted_key
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error creating proxy wallet: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

@router.post("/proxy/deposit", status_code=status.HTTP_200_OK)
async def deposit_proxy_wallet(payload: ProxyWalletDepositRequest, current_user: int = Depends(get_current_user)):
    async for conn in db.get_connection():
        # Update balance
        row = await conn.fetchrow(
            """
            UPDATE user_proxy_wallets
            SET balance = balance + $1
            WHERE id = $2
            RETURNING id, user_id, blockchain, address, balance
            """,
            payload.amount, payload.proxy_wallet_id
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proxy wallet not found."
            )
        return dict(row)

@router.post("/monitor", status_code=status.HTTP_201_CREATED)
async def monitor_wallet(payload: MonitoredWalletCreateRequest, current_user: int = Depends(get_current_user)):
    async for conn in db.get_connection():
        # Ensure user exists
        await conn.execute(
            "INSERT INTO users (id, username, is_premium) VALUES ($1, $2, FALSE) ON CONFLICT (id) DO NOTHING",
            current_user, f"user_{current_user}"
        )
        
        # Check limit
        user = await conn.fetchrow("SELECT is_premium, referral_credits FROM users WHERE id = $1", current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
            
        from backend.app.services.referral import get_max_wallets
        referral_credits = user["referral_credits"] or 0
        max_slots = get_max_wallets(user["is_premium"], referral_credits)
        
        if max_slots != -1:
            count = await conn.fetchval("SELECT COUNT(*) FROM monitored_wallets WHERE user_id = $1", current_user)
            if count >= max_slots:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You can only monitor up to {max_slots} wallets.")
                
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO monitored_wallets (user_id, blockchain, address, label)
                VALUES ($1, $2, $3, $4)
                RETURNING id, user_id, blockchain, address, label, push_enabled, created_at
                """,
                current_user, payload.blockchain, payload.address, payload.label
            )
            return dict(row)
        except Exception as e:
            logger.error(f"Error creating monitored wallet: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to monitor wallet: {e}"
            )

@router.get("/tracker/stats", status_code=status.HTTP_200_OK)
async def get_tracker_stats(current_user: int = Depends(get_current_user)):
    user_id = current_user
    async for conn in db.get_connection():
        wallets = await conn.fetch(
            "SELECT address, blockchain, label FROM monitored_wallets WHERE user_id = $1",
            user_id
        )
        
        results = []
        for w in wallets:
            address = w["address"]
            txs = await conn.fetch(
                "SELECT tx_type, usd_value FROM wallet_transactions WHERE wallet_address = $1",
                address
            )
            
            pnl_usd = Decimal(0)
            if txs:
                for tx in txs:
                    if tx["tx_type"] == "SELL" and tx["usd_value"]:
                        pnl_usd += tx["usd_value"]
                    elif tx["tx_type"] == "BUY" and tx["usd_value"]:
                        pnl_usd -= tx["usd_value"]
                        
            results.append({
                "blockchain": w["blockchain"],
                "address": address,
                "label": w["label"],
                "unrealized_pnl_usd": str(pnl_usd)
            })
            
        return {"monitored_wallets": results}
