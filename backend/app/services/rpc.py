import logging
import httpx
from decimal import Decimal
from typing import Optional

from backend.app.config import settings

logger = logging.getLogger(__name__)

class RPCClient:
    def __init__(self):
        # We will share these across requests
        self.httpx_client = httpx.AsyncClient(timeout=10.0)
        
    async def close(self):
        await self.httpx_client.aclose()

    async def get_wallet_balance(self, blockchain: str, address: str) -> Optional[Decimal]:
        """Fetch native token balance for a given address on a blockchain."""
        try:
            if blockchain == "TON":
                # Mock Toncenter request
                resp = await self.httpx_client.get(
                    f"{settings.ton_rpc_url}/getAddressInformation", 
                    params={"address": address}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        return Decimal(data["result"]["balance"]) / Decimal(10**9)
            elif blockchain == "SOL":
                resp = await self.httpx_client.post(
                    settings.solana_rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getBalance",
                        "params": [address]
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        return Decimal(data["result"]["value"]) / Decimal(10**9)
            elif blockchain == "BASE":
                resp = await self.httpx_client.post(
                    settings.base_rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_getBalance",
                        "params": [address, "latest"]
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "result" in data:
                        val = int(data["result"], 16)
                        return Decimal(val) / Decimal(10**18)
        except Exception as e:
            logger.error(f"Error fetching balance for {address} on {blockchain}: {e}")
        return None

    async def get_token_price(self, blockchain: str, token_address: str) -> Optional[Decimal]:
        """Mock implementation to fetch token price in USD."""
        # In a real app we'd use a DEX aggregator API or oracle (e.g., Pyth, Chainlink)
        # For Phase 6 requirements, this is a mock implementation that returns a dummy price
        logger.info(f"Mocking token price for {token_address} on {blockchain}")
        return Decimal("1.50")

    async def verify_transaction(self, blockchain: str, tx_hash: str, expected_receiver: str, expected_amount: Decimal) -> bool:
        """
        Verify that a transaction has completed and sent the expected amount to the receiver.
        Returns True if successful, False otherwise.
        """
        try:
            # Mock implementation for Phase 6
            # In a real app we would decode the transaction log / receipt
            logger.info(f"Verifying transaction {tx_hash} on {blockchain}. Expected: {expected_amount} to {expected_receiver}")
            # We mock that the transaction is valid for testing purposes
            return True
        except Exception as e:
            logger.error(f"Error verifying transaction {tx_hash} on {blockchain}: {e}")
            return False

rpc_client = RPCClient()
