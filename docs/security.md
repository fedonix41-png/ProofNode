# Security Architecture

## Hybrid Copy-Trading Security Model

ProofNode handles sensitive financial operations through a hybrid security model to minimize risks associated with private key management.

### 1-Click Copy-Trading (Non-Custodial)
Designed for users who want manual control over trade execution when they receive a push notification.
- **Mechanism:** Shamir's Secret Sharing (SSS) 2-of-3.
- **Share 1 (Client):** Stored locally in the Telegram Mini App (IndexedDB), encrypted by a user PIN.
- **Share 2 (Server):** Stored in the PostgreSQL `user_sss_shares` table.
- **Share 3 (Backup):** Encrypted with a master password and stored in Telegram Cloud Storage.
- **Execution:** When the user clicks "Copy", Share 1 and Share 2 are combined inside the client's WebAssembly (WASM) environment. The transaction is signed locally. The server never sees the reconstructed private key.

### Automated Cloud Copy-Trading (Proxy-Custodial)
Designed for background execution while the user is offline.
- **Mechanism:** KMS-Encrypted Proxy Wallets.
- **Implementation:** 
  - A dedicated "Proxy Wallet" is generated for the user with a strict budget limit (e.g., 20 TON).
  - The private key is encrypted using a Key Management Service (KMS) master key (currently implemented as a `cryptography.fernet` stub using `KMS_MASTER_KEY` environment variable).
  - The encrypted key is stored in the `user_proxy_wallets` table.
- **Execution:** The backend Copy-Trade Execution Worker decrypts the key in-memory only at the exact moment of signing a transaction routed via a DEX aggregator.

### Operational Hazards & Constraints
- **KMS Keys:** The master KMS key must remain an ephemeral runtime secret. It must never be committed to source control.
- **Database Exposure:** Even in the event of a database dump leak, automated proxy wallet keys remain securely encrypted, and SSS Share 2 is useless without the client's Share 1.
