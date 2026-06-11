import logging
import httpx
from typing import Dict, Any, Tuple
from backend.app.config import settings

logger = logging.getLogger(__name__)

async def simulate_solana_tx(serialized_tx_base64: str) -> Tuple[bool, str]:
    """
    Simulate a Solana transaction using the RPC simulateTransaction endpoint.
    """
    url = settings.solana_rpc_url
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "simulateTransaction",
        "params": [
            serialized_tx_base64,
            {"encoding": "base64", "replaceRecentBlockhash": True}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            result = data.get("result", {})
            value = result.get("value", {})
            err = value.get("err")
            
            if err:
                return False, str(err)
            return True, "Simulation successful"
        except Exception as e:
            logger.error(f"Failed to simulate Solana tx: {e}")
            return False, str(e)

async def simulate_base_tx(tx_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Simulate a Base transaction using eth_call.
    """
    url = settings.base_rpc_url
    
    call_params = {
        "to": tx_dict.get("to"),
        "data": tx_dict.get("data"),
        "value": hex(tx_dict.get("value", 0)) if isinstance(tx_dict.get("value"), int) else tx_dict.get("value", "0x0"),
        "from": tx_dict.get("from")
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [call_params, "latest"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                return False, data["error"].get("message", str(data["error"]))
            return True, "Simulation successful"
        except Exception as e:
            logger.error(f"Failed to simulate Base tx: {e}")
            return False, str(e)

async def check_gas_price(chain: str) -> Tuple[float, bool]:
    """
    Check current gas price. Returns (current_price_gwei, is_acceptable).
    """
    if chain == "BASE":
        url = settings.base_rpc_url
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_gasPrice",
            "params": []
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, timeout=5.0)
                resp.raise_for_status()
                data = resp.json()
                
                if "result" in data:
                    gas_price_wei = int(data["result"], 16)
                    gas_price_gwei = gas_price_wei / 1e9
                    return gas_price_gwei, gas_price_gwei <= settings.max_gas_price_gwei
            except Exception as e:
                logger.error(f"Failed to check gas price for {chain}: {e}")
                
    # For Solana/TON, fee is mostly fixed or handled differently
    return 0.0, True
