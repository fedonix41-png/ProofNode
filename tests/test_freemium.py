import pytest
import asyncio
from backend.app.db import db
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_freemium_wallet_limit():
    await db.connect()
    
    # Clean up before test
    async for conn in db.get_connection():
        await conn.execute("DELETE FROM monitored_wallets WHERE user_id = 998")
        await conn.execute("DELETE FROM users WHERE id = 998")
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Add 3 wallets
        for i in range(3):
            response = await ac.post("/api/wallets/monitor", json={
                "user_id": 998,
                "blockchain": "TON",
                "address": f"EQ_FREE_{i}",
                "label": f"Wallet {i}"
            })
            assert response.status_code == 201
            
        # Try to add a 4th wallet, should fail
        response = await ac.post("/api/wallets/monitor", json={
            "user_id": 998,
            "blockchain": "TON",
            "address": "EQ_FREE_3",
            "label": "Wallet 3"
        })
        assert response.status_code == 403
        
    # Clean up after test
    async for conn in db.get_connection():
        await conn.execute("DELETE FROM monitored_wallets WHERE user_id = 998")
        await conn.execute("DELETE FROM users WHERE id = 998")
        
    await db.disconnect()
