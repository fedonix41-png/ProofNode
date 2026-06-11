import pytest
from backend.app.services.sss import split_secret, reconstruct_secret

def test_sss_correctness():
    # A standard 256-bit private key representation in hex
    secret = "a1b2c3d4e5f60718293a4b5c6d7e8f900112233445566778899aabbccddeeff0"
    
    # Split the secret into 3 shares
    shares = split_secret(secret)
    assert len(shares) == 3
    
    # Reconstruct from shares 1 and 2
    rec12 = reconstruct_secret([shares[0], shares[1]])
    assert rec12 == secret
    
    # Reconstruct from shares 2 and 3
    rec23 = reconstruct_secret([shares[1], shares[2]])
    assert rec23 == secret
    
    # Reconstruct from shares 1 and 3
    rec13 = reconstruct_secret([shares[0], shares[2]])
    assert rec13 == secret

def test_sss_invalid_inputs():
    with pytest.raises(ValueError):
        reconstruct_secret(["1:abc"])
