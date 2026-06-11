/**
 * Client-Side Shamir's Secret Sharing (2-of-3)
 * Note: This uses a simplified arithmetic for 256-bit keys over a large prime field.
 * For production, use GF(2^8) (e.g., secrets.js-grempe).
 */

// A large prime slightly greater than 2^256 for the prime field
// 2^256 + 297 is prime
const PRIME = 115792089237316195423570985008687907853269984665640564039457584007913129640233n;

// Generate a random 256-bit BigInt
function randomBigInt(): bigint {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  let hex = '0x';
  for (const b of bytes) {
    hex += b.toString(16).padStart(2, '0');
  }
  return BigInt(hex);
}

/**
 * Splits a hex private key into 3 shares (2-of-3 required to reconstruct).
 * @param privateKeyHex 64-character hex string (e.g., 256-bit key)
 * @returns Array of 3 shares as hex strings (Share1, Share2, Share3)
 */
export function splitKey(privateKeyHex: string): string[] {
  // Ensure it's a valid hex string
  const cleanHex = privateKeyHex.replace(/^0x/, '');
  if (!/^[0-9a-fA-F]+$/.test(cleanHex)) {
    throw new Error('Invalid hex string');
  }
  
  const secret = BigInt('0x' + cleanHex);
  if (secret >= PRIME) {
    throw new Error('Secret is too large for the prime field');
  }

  // 2-of-3 means polynomial degree is 1: f(x) = secret + a1 * x
  const a1 = randomBigInt() % PRIME;

  // Evaluate at x = 1, 2, 3
  const shares = [];
  for (let x = 1n; x <= 3n; x++) {
    let y = (secret + a1 * x) % PRIME;
    if (y < 0n) y += PRIME;
    shares.push(`${x.toString()}-${y.toString(16).padStart(64, '0')}`);
  }

  return shares;
}

/**
 * Reconstructs the private key from 2 shares.
 * @param shareA Share 1
 * @param shareB Share 2
 * @returns 64-character hex string
 */
export function reconstructKey(shareA: string, shareB: string): string {
  const [x1Str, y1Str] = shareA.split('-');
  const [x2Str, y2Str] = shareB.split('-');

  if (!x1Str || !y1Str || !x2Str || !y2Str) {
    throw new Error('Invalid share format');
  }

  const x1 = BigInt(x1Str);
  const y1 = BigInt('0x' + y1Str);
  const x2 = BigInt(x2Str);
  const y2 = BigInt('0x' + y2Str);

  if (x1 === x2) {
    throw new Error('Shares must have different X coordinates');
  }

  // Lagrange interpolation at x = 0
  // f(0) = y1 * (0 - x2)/(x1 - x2) + y2 * (0 - x1)/(x2 - x1)
  
  // To compute (0 - x2) / (x1 - x2) mod PRIME
  const num1 = (-x2) % PRIME;
  const den1 = (x1 - x2) % PRIME;
  const term1 = (y1 * num1 * modInverse(den1, PRIME)) % PRIME;

  const num2 = (-x1) % PRIME;
  const den2 = (x2 - x1) % PRIME;
  const term2 = (y2 * num2 * modInverse(den2, PRIME)) % PRIME;

  let secret = (term1 + term2) % PRIME;
  if (secret < 0n) secret += PRIME;

  return secret.toString(16).padStart(64, '0');
}

/**
 * Computes modular inverse using Fermat's Little Theorem (since PRIME is prime)
 * a^(p-2) mod p
 */
function modInverse(a: bigint, m: bigint): bigint {
  let power = m - 2n;
  let res = 1n;
  let base = a % m;
  if (base < 0n) base += m;

  while (power > 0n) {
    if (power % 2n === 1n) {
      res = (res * base) % m;
    }
    base = (base * base) % m;
    power /= 2n;
  }
  return res;
}
