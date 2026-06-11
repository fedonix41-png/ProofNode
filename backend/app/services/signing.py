import logging
import base58
from solders.keypair import Keypair # type: ignore
from solders.transaction import VersionedTransaction # type: ignore
from solders.message import MessageV0 # type: ignore
from eth_account import Account
import json

logger = logging.getLogger(__name__)

def sign_ed25519(tx_bytes: bytes, private_key_bytes: bytes):
    """
    Sign a transaction using Ed25519.
    Returns (signature, signed_tx)
    For Solana, we deserialize the versioned transaction and sign it.
    """
    keypair = Keypair.from_bytes(private_key_bytes)
    
    # We expect tx_bytes to be the bytes of a VersionedTransaction
    # Since solders API for signing VersionedTransaction is specific:
    try:
        tx = VersionedTransaction.from_bytes(tx_bytes)
        # Sign the message
        # In solders, we can just do:
        signed_tx = VersionedTransaction(tx.message, [keypair])
        return signed_tx.signatures[0], bytes(signed_tx)
    except Exception as e:
        logger.error(f"Failed to sign Ed25519 (Solana): {e}")
        return None, None

def sign_ecdsa(tx_dict: dict, private_key_hex: str) -> str:
    """
    Sign a transaction using ECDSA for EVM (Base).
    Returns signed raw tx hex.
    """
    try:
        if not private_key_hex.startswith('0x'):
            private_key_hex = '0x' + private_key_hex
        signed_tx = Account.sign_transaction(tx_dict, private_key_hex)
        return signed_tx.rawTransaction.hex()
    except Exception as e:
        logger.error(f"Failed to sign ECDSA: {e}")
        return ""

def verify_ed25519_signature(tx_bytes: bytes, signature: bytes, public_key: bytes) -> bool:
    """
    Verify an Ed25519 signature.
    """
    from solders.signature import Signature # type: ignore
    from solders.pubkey import Pubkey # type: ignore
    
    try:
        sig = Signature(list(signature))
        pub = Pubkey(list(public_key))
        
        tx = VersionedTransaction.from_bytes(tx_bytes)
        # solders Signature object has verify
        return sig.verify(pub, tx.message.serialize())
    except Exception as e:
        logger.error(f"Failed to verify Ed25519 signature: {e}")
        return False
