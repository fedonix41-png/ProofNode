import secrets
from typing import List

# Prime number larger than 2^256 (specifically 2^256 - 189)
PRIME = 115792089237316195423570985008687907853269984665640564039457584007913129639747

def split_secret(secret_hex: str) -> List[str]:
    """
    Splits a hex secret into 3 shares using Shamir's Secret Sharing (2-of-3).
    Returns shares as strings in the format "index:share_hex".
    """
    secret_int = int(secret_hex, 16)
    if secret_int >= PRIME:
        raise ValueError("Secret is too large for the prime field.")
    
    # Choose random coefficient a1
    a1 = secrets.randbelow(PRIME - 1) + 1
    
    # f(x) = secret + a1 * x
    shares = []
    for x in (1, 2, 3):
        y = (secret_int + a1 * x) % PRIME
        shares.append(f"{x}:{hex(y)[2:]}")
    return shares

def reconstruct_secret(shares: List[str]) -> str:
    """
    Reconstructs the hex secret from any 2 or more shares.
    Expects shares in the format "index:share_hex".
    """
    if len(shares) < 2:
        raise ValueError("At least 2 shares are required to reconstruct.")
        
    parsed_shares = []
    for s in shares:
        parts = s.split(":")
        parsed_shares.append((int(parts[0]), int(parts[1], 16)))
        
    # Lagrange interpolation at x = 0
    # For 2-of-3, we interpolate with the first 2 shares
    x1, y1 = parsed_shares[0]
    x2, y2 = parsed_shares[1]
    
    def mod_inverse(n, p):
        return pow(n, p - 2, p)
        
    term1 = (y1 * x2 * mod_inverse((x2 - x1) % PRIME, PRIME)) % PRIME
    term2 = (y2 * x1 * mod_inverse((x1 - x2) % PRIME, PRIME)) % PRIME
    
    secret_int = (term1 + term2) % PRIME
    secret_hex = hex(secret_int)[2:]
    
    # Pad to ensure original length padding isn't lost (standard 64-char key)
    # If the key was originally shorter/longer, we can match length.
    return secret_hex.zfill(64)
