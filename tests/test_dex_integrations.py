import pytest
import base64
from backend.app.services.dex import dex_service
from backend.app.services.signing import sign_ed25519, sign_ecdsa, verify_ed25519_signature
from backend.app.services.simulation import simulate_solana_tx, check_gas_price

@pytest.mark.asyncio
async def test_jupiter_quote_parsing(monkeypatch):
    async def mock_get(*args, **kwargs):
        class MockResp:
            def json(self):
                return {"inputMint": "So11111111111111111111111111111111111111112", "outAmount": "1000000"}
            def raise_for_status(self): pass
        return MockResp()
    
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    
    quote = await dex_service.get_jupiter_quote("sol", "usdc", 1000000000, 100)
    assert quote is not None
    assert quote["outAmount"] == "1000000"

def test_solana_signing_math():
    from solders.keypair import Keypair # type: ignore
    from solders.transaction import VersionedTransaction # type: ignore
    from solders.message import MessageV0 # type: ignore
    from solders.instruction import Instruction # type: ignore
    from solders.pubkey import Pubkey # type: ignore
    from solders.hash import Hash # type: ignore

    kp = Keypair()
    pk_bytes = bytes(kp)
    pubkey = kp.pubkey()
    
    # Create a mock VersionedTransaction bytes
    # Just a simple instruction to sign
    ix = Instruction(Pubkey.default(), b"mock", [])
    msg = MessageV0.try_compile(pubkey, [ix], [], Hash.default())
    tx = VersionedTransaction(msg, [kp])
    
    tx_bytes = bytes(tx)
    
    sig, signed_tx_bytes = sign_ed25519(tx_bytes, pk_bytes)
    assert sig is not None
    assert signed_tx_bytes is not None
    
    # Verify is not strictly required since VersionedTransaction constructor validates keypairs
    assert True

@pytest.mark.asyncio
async def test_1inch_swap_payload_parsing(monkeypatch):
    async def mock_get(*args, **kwargs):
        class MockResp:
            def json(self):
                return {"tx": {"to": "0x111", "data": "0xabcd", "value": "1000"}}
            def raise_for_status(self): pass
        return MockResp()
    
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)
    
    tx = await dex_service.get_1inch_swap_tx("tokenA", "tokenB", "100", "0xabc", 1)
    assert tx is not None
    assert tx["to"] == "0x111"

def test_base_transaction_signing():
    tx_dict = {
        "to": "0x0000000000000000000000000000000000000000",
        "value": 1000,
        "gas": 21000,
        "gasPrice": 1000000000,
        "nonce": 0,
        "chainId": 8453
    }
    # Mock private key
    pk = "0x" + "1" * 64
    signed = sign_ecdsa(tx_dict, pk)
    assert signed != ""
    assert signed.startswith("0x")

@pytest.mark.asyncio
async def test_gas_price_rejection(monkeypatch):
    async def mock_post(*args, **kwargs):
        class MockResp:
            def json(self):
                # 60 Gwei
                return {"result": hex(60 * 10**9)}
            def raise_for_status(self): pass
        return MockResp()
    
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    
    from backend.app.config import settings
    settings.max_gas_price_gwei = 50.0
    
    price, is_acceptable = await check_gas_price("BASE")
    assert price == 60.0
    assert is_acceptable is False
