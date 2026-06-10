import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

def parse_blockchain_transaction(blockchain: str, tx_hash: str, wallet_address: str, time_val: datetime, raw_payload: str) -> Optional[Dict[str, Any]]:
    """
    Decodes the raw payload of a transaction into a standardized DEX swap log.
    Supports decoding JSON-encoded transaction structures.
    """
    try:
        # Attempt to parse raw payload as JSON
        data = json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.warning(f"Raw payload for tx {tx_hash} is not valid JSON. Using default fallback parsing.")
        # If payload is raw text/hex, construct a placeholder swap
        return {
            "time": time_val,
            "tx_hash": tx_hash,
            "wallet_address": wallet_address,
            "blockchain": blockchain,
            "dex_name": "UnknownDEX",
            "token_in_address": "unknown_input_token",
            "token_out_address": "unknown_output_token",
            "amount_in": Decimal("0.0"),
            "amount_out": Decimal("0.0"),
            "usd_value": Decimal("0.0"),
            "tx_type": "TRANSFER",
            "trace_id": None,
            "logical_time": None
        }

    # Extract common field values or defaults
    dex_name = data.get("dex_name", "Ston.fi" if blockchain == "TON" else "Uniswap" if blockchain == "BASE" else "Jupiter")
    token_in = data.get("token_in", "token_in_address_placeholder")
    token_out = data.get("token_out", "token_out_address_placeholder")
    
    try:
        amount_in = Decimal(str(data.get("amount_in", 0.0)))
        amount_out = Decimal(str(data.get("amount_out", 0.0)))
        usd_value = Decimal(str(data.get("usd_value", 0.0)))
    except Exception as e:
        logger.warning(f"Error parsing numeric fields in tx {tx_hash}: {e}")
        amount_in = Decimal("0.0")
        amount_out = Decimal("0.0")
        usd_value = Decimal("0.0")

    tx_type = data.get("tx_type", "BUY").upper()
    if tx_type not in ("BUY", "SELL", "TRANSFER"):
        tx_type = "TRANSFER"

    # Block-specific metrics
    trace_id = data.get("trace_id")
    logical_time = data.get("logical_time")

    return {
        "time": time_val,
        "tx_hash": tx_hash,
        "trace_id": trace_id,
        "logical_time": logical_time,
        "wallet_address": wallet_address,
        "blockchain": blockchain,
        "dex_name": dex_name,
        "token_in_address": token_in,
        "token_out_address": token_out,
        "amount_in": amount_in,
        "amount_out": amount_out,
        "usd_value": usd_value,
        "tx_type": tx_type
    }
