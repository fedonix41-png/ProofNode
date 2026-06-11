import logging
import httpx
import base64
from typing import Optional, Dict, Any
from backend.app.config import settings
from backend.app.services.signing import sign_ed25519, sign_ecdsa

logger = logging.getLogger(__name__)

class DEXService:
    # --- Solana (Jupiter V6) ---
    async def get_jupiter_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict[str, Any]]:
        url = f"{settings.jupiter_api_url}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps)
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to get Jupiter quote: {e}")
                return None

    async def get_jupiter_swap_tx(self, quote: Dict[str, Any], user_public_key: str) -> Optional[str]:
        url = f"{settings.jupiter_api_url}/swap"
        payload = {
            "quoteResponse": quote,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                return data.get("swapTransaction")
            except Exception as e:
                logger.error(f"Failed to get Jupiter swap tx: {e}")
                return None

    async def sign_and_send_solana_tx(self, serialized_tx_base64: str, private_key_bytes: bytes) -> Optional[str]:
        try:
            tx_bytes = base64.b64decode(serialized_tx_base64)
            signature, signed_tx_bytes = sign_ed25519(tx_bytes, private_key_bytes)
            if not signed_tx_bytes:
                return None

            signed_tx_base64 = base64.b64encode(signed_tx_bytes).decode('utf-8')
            
            # Broadcast
            url = settings.solana_rpc_url
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    signed_tx_base64,
                    {"encoding": "base64"}
                ]
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    logger.error(f"RPC error sending Solana tx: {data['error']}")
                    return None
                return data.get("result")
        except Exception as e:
            logger.error(f"Failed to sign and send Solana tx: {e}")
            return None

    # --- Base (1inch) ---
    async def get_1inch_quote(self, src_token: str, dst_token: str, amount: str) -> Optional[Dict[str, Any]]:
        url = "https://api.1inch.dev/swap/v6.0/8453/quote"
        headers = {"Authorization": f"Bearer {settings.oneinch_api_key}"}
        params = {
            "src": src_token,
            "dst": dst_token,
            "amount": amount
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, headers=headers, timeout=10.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to get 1inch quote: {e}")
                return None

    async def get_1inch_swap_tx(self, src_token: str, dst_token: str, amount: str, from_address: str, slippage: int) -> Optional[Dict[str, Any]]:
        url = "https://api.1inch.dev/swap/v6.0/8453/swap"
        headers = {"Authorization": f"Bearer {settings.oneinch_api_key}"}
        params = {
            "src": src_token,
            "dst": dst_token,
            "amount": amount,
            "from": from_address,
            "slippage": str(slippage)
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, headers=headers, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                return data.get("tx")
            except Exception as e:
                logger.error(f"Failed to get 1inch swap tx: {e}")
                return None

    async def sign_and_send_base_tx(self, tx_dict: dict, private_key_hex: str) -> Optional[str]:
        try:
            # Convert values to int
            if 'value' in tx_dict and isinstance(tx_dict['value'], str):
                if tx_dict['value'].startswith('0x'):
                    tx_dict['value'] = int(tx_dict['value'], 16)
                else:
                    tx_dict['value'] = int(tx_dict['value'])
                    
            if 'gasPrice' in tx_dict and isinstance(tx_dict['gasPrice'], str):
                if tx_dict['gasPrice'].startswith('0x'):
                    tx_dict['gasPrice'] = int(tx_dict['gasPrice'], 16)
                else:
                    tx_dict['gasPrice'] = int(tx_dict['gasPrice'])
                    
            # 1inch API might not set nonce or chainId directly in tx
            # In a real impl we fetch nonce via RPC
            # Here we just sign what we have
            tx_dict['chainId'] = 8453
            
            signed_tx_hex = sign_ecdsa(tx_dict, private_key_hex)
            if not signed_tx_hex:
                return None

            url = settings.base_rpc_url
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendRawTransaction",
                "params": [signed_tx_hex]
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    logger.error(f"RPC error sending Base tx: {data['error']}")
                    return None
                return data.get("result")
        except Exception as e:
            logger.error(f"Failed to sign and send Base tx: {e}")
            return None

    # --- TON (Ston.fi) ---
    async def get_stonfi_route(self, from_jetton: str, to_jetton: str, amount: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.stonfi_api_url}/swap/simulate"
        params = {
            "offer_address": from_jetton,
            "ask_address": to_jetton,
            "units": amount,
            "slippage_tolerance": "0.01"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, params=params, timeout=10.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to get Stonfi route: {e}")
                return None

    async def build_stonfi_swap_msg(self, route: Dict[str, Any], wallet_address: str) -> Optional[Dict[str, Any]]:
        # Mock builder since TON message building usually requires tonpy or pytonlib
        logger.info(f"Building Stonfi swap msg for {wallet_address} with route {route}")
        return {"mock_ton_message": "built"}

    async def sign_and_send_ton_tx(self, message_payload: dict, private_key_hex: str) -> Optional[str]:
        # Mock signing and sending since TON signing usually requires a fully constructed BoC
        logger.info(f"Signing and sending TON tx with payload: {message_payload}")
        return "mock_ton_tx_hash_123"

dex_service = DEXService()
