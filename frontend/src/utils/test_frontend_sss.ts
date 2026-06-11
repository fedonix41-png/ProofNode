import { splitKey, reconstructKey } from './sss';

function assert(condition: boolean, message: string) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

async function runTests() {
    console.log('Running Client-Side SSS Tests...');

    // 1. Valid Hex Key (256-bit representation)
    const testKey = '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    
    // 2. Split into 3 shares
    const shares = splitKey(testKey);
    assert(shares.length === 3, 'Should generate exactly 3 shares');
    console.log('Generated shares successfully.');

    // 3. Reconstruct with Share 1 and Share 2
    const reconstructed12 = reconstructKey(shares[0], shares[1]);
    assert(reconstructed12 === testKey, `Share 1+2 mismatch. Expected ${testKey}, got ${reconstructed12}`);

    // 4. Reconstruct with Share 2 and Share 3
    const reconstructed23 = reconstructKey(shares[1], shares[2]);
    assert(reconstructed23 === testKey, 'Share 2+3 mismatch');

    // 5. Reconstruct with Share 1 and Share 3
    const reconstructed13 = reconstructKey(shares[0], shares[2]);
    assert(reconstructed13 === testKey, 'Share 1+3 mismatch');

    console.log('✅ All SSS sharing and reconstruction tests passed.');
}

runTests().catch(console.error);
