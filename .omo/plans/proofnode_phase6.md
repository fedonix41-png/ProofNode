# ASW Plan: ProofNode Phase 6 - Live Blockchain & DEX Aggregator Integrations

## TL;DR
Replace the current sandbox mock layers with production-grade blockchain integrations. Implement cryptographic webhook signature verification (Helius for Solana, Alchemy for Base, TonAPI for TON), establish connection pools to live RPC nodes for balance caching and paywall confirmation, connect to real DEX aggregator APIs (Jupiter V6, 1inch, Ston.fi) to retrieve swap transaction payloads, and execute real transaction signing and broadcasting for KMS-encrypted proxy wallets.

---

## Objective
To enable actual on-chain transaction execution and verification:
1. Replace gateway signature stubs with real header validation (HMAC-SHA256 and API tokens) matching each provider's spec.
2. Integrate real blockchain RPC client wrappers for TON (Toncenter/TonAPI RPC), Solana (JSON-RPC), and Base (Web3.py) to read proxy wallet balances and verify subscription payment tx hashes on-chain.
3. Replace the mock quote router in `dex.py` with live API integrations:
   - **Solana**: Jupiter V6 API to fetch swap quotes and serialized swap transactions.
   - **Base**: 1inch Swap API for EVM routing and transaction payloads.
   - **TON**: Ston.fi / DeDust SDK or HTTP API to fetch jetton routes and transaction parameters.
4. Implement real cryptographic transaction serialization, signing, and broadcasting for proxy wallets (Ed25519 for TON/Solana, ECDSA for Base).
5. Build an integration test suite validating signing maths and mock DEX responses.

---

## Non-Goals
- Connecting to mainnets for development tests. All local testing will use testnets (TON Testnet, Solana Devnet, Base Sepolia) or recorded mock API snapshots.
- AWS KMS hardware HSM integration (reserved for Phase 7).
- Modifying frontend TMA components (Phase 4).

---

## Decision Summary
- **Python Blockchain SDKs**:
  - EVM: `web3` (version 6.x/7.x) for Base.
  - Solana: `solana` (version 0.30+) and `solders` for transaction serialization.
  - TON: Custom async HTTP RPC client matching TON JSON-RPC (Toncenter v2 API) to avoid brittle third-party python-ton library dependencies.
- **Webhook Authenticity Verification**:
  - Base (Alchemy): HMAC-SHA256 signature verification using the request body and the secret signing key.
  - Solana (Helius): Authorization header matching Helius webhook secret.
  - TON (TonAPI): Signature checking or headers authentication tokens.
- **DEX API Integrations**:
  - Jupiter: Call `https://quote-api.jup.ag/v6/quote` and then `https://quote-api.jup.ag/v6/swap` to get the base64-encoded transaction, deserialize it via `VersionedTransaction.deserialize` in `solders`, sign it with the proxy wallet's keypair, and broadcast it.
  - 1inch: Call `https://api.1inch.dev/swap/v6.0/8453/swap` using a platform API token to fetch the transaction payload (`to`, `data`, `value`, `gas`), build the raw transaction in Web3.py, sign it with the ECDSA private key, and broadcast it using `eth.send_raw_transaction`.
  - Ston.fi: Build swap transactions matching Ston.fi router call payloads for TON, sending it via Jetton transfer payload or TON message.

---

## Files to Edit & Create

### [MODIFY] Configuration & Dependencies
- [requirements.txt](file:///home/ozzy/Документы/ProofNode/backend/requirements.txt) - Add `web3`, `solana`, `solders`.
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Declare variables: `SOLANA_RPC_URL`, `BASE_RPC_URL`, `TON_RPC_URL`, `HELIUS_WEBHOOK_SECRET`, `ALCHEMY_WEBHOOK_SECRET`, `TONAPI_WEBHOOK_SECRET`, `ONEINCH_API_KEY`.

### [MODIFY] Webhook Gateway
- [main.py](file:///home/ozzy/Документы/ProofNode/backend/app/main.py) - Implement cryptographic header verification middleware/functions for `/gateway/ton`, `/gateway/sol`, and `/gateway/evm`.

### [MODIFY] Services
- [dex.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/dex.py) - Replace simulated quotes and dummy signers with live API fetches (Jupiter, 1inch, Ston.fi), real keypair initialization, transaction signing, and RPC broadcasting.

### [MODIFY] Routers
- [subscriptions.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/subscriptions.py) - Implement on-chain validation for subscription payments by checking the transaction confirmation, receiver address, and value on testnets.
- [wallets.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/wallets.py) - Implement on-chain balance querying for proxy wallets.

### [NEW] Testing Suite
- [test_live_integrations.py](file:///home/ozzy/Документы/ProofNode/tests/test_live_integrations.py) - Tests validating transaction signing engines, webhook signature math, and mock-stubbed DEX response payloads.

---

## TODOs

- [ ] **Dependencies and Settings Setup**
  - Add `web3>=6.0.0` and `solana>=0.30.0` to `backend/requirements.txt`.
  - Install dependencies: `uv pip install -r backend/requirements.txt`.
  - Define RPC URLs and webhook secrets in `backend/app/config.py`.
  - *Commit guidance*: "infra: add blockchain SDKs dependencies and RPC configuration settings"

- [ ] **Cryptographic Webhook Verification**
  - Implement signature checks in `backend/app/main.py`:
    - Alchemy (EVM): Compute SHA256 HMAC of raw request body using `ALCHEMY_WEBHOOK_SECRET` and compare it to the `x-alchemy-signature` header.
    - Helius (Solana): Validate that the `Authorization` header matches the `HELIUS_WEBHOOK_SECRET`.
    - TonAPI (TON): Validate header tokens against `TONAPI_WEBHOOK_SECRET`.
  - *Commit guidance*: "feat: implement cryptographic webhook signature validation"

- [ ] **On-chain Payment Verification & Balance Checking**
  - Update `backend/app/routers/subscriptions.py`:
    - Connect to the RPC node (Web3.py for Base, Solana RPC for SOL, TON JSON-RPC for TON).
    - Query transaction details by hash. Assert that the transaction was confirmed, the receiver address matches the merchant/trader wallet, and the token value matches the tariff pricing.
  - Update `backend/app/routers/wallets.py` to fetch actual balances of proxy wallets from the network.
  - *Commit guidance*: "feat: connect paywall payment confirmation to live blockchain RPCs"

- [ ] **Base/EVM Signing & 1inch DEX Integration**
  - In `backend/app/services/dex.py`:
    - Implement the 1inch swap quote request.
    - Deserialize private key using Web3.py.
    - Build, sign, and broadcast the Base transaction.
  - *Commit guidance*: "feat: implement 1inch routing and EVM transaction signing"

- [ ] **Solana Signing & Jupiter DEX Integration**
  - In `backend/app/services/dex.py`:
    - Fetch the swap transaction base64 payload from Jupiter V6.
    - Parse using `VersionedTransaction.deserialize` from `solders`.
    - Sign with the proxy wallet's Ed25519 private key.
    - Broadcast using Solana RPC (`send_transaction`).
  - *Commit guidance*: "feat: implement jupiter routing and solana transaction signing"

- [ ] **TON Signing & Ston.fi DEX Integration**
  - In `backend/app/services/dex.py`:
    - Implement swap payload serialization for TON (Ston.fi jetton swap parameters).
    - Construct external message, sign using Ed25519, and broadcast to the TON RPC.
  - *Commit guidance*: "feat: implement stonfi routing and TON transaction signing"

- [ ] **Integration Testing**
  - Create `tests/test_live_integrations.py` to test signature matching and transaction builder math using VCR.py or standard mocks.
  - Execute test suite: `PYTHONPATH=. uv run pytest tests/test_live_integrations.py -v`.
  - *Commit guidance*: "test: add tests for webhook verification and blockchain signing"

---

## QA Scenarios

### Scenario 1: Webhook Signature Rejection
- **Command**:
  - Spin up FastAPI gateway:
    ```bash
    uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
    GATEWAY_PID=$!
    sleep 2
    ```
  - Send request with an invalid signature header:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -H "x-alchemy-signature: invalid_sig" \
         -d '{"event": "test"}' \
         http://127.0.0.1:8000/gateway/evm
    ```
  - Kill gateway:
    ```bash
    kill $GATEWAY_PID
    ```
- **Expected Evidence**:
  - The HTTP POST request returns `401 Unauthorized` or `403 Forbidden` due to invalid signature math.

### Scenario 2: Transaction Signing Test
- **Command**:
  - Run the live integrations pytest suite:
    ```bash
    PYTHONPATH=. uv run pytest tests/test_live_integrations.py -v
    ```
- **Expected Evidence**:
  - All test cases asserting transaction encoding, key generation, and signing verification pass successfully.

### Cleanup Receipt
- **Command**:
  - Standard process check.
- **Expected Evidence**:
  - No orphaned background tasks.

---

## Privacy & Package Safeguards
- Ensure all test keys/seeds are mock credentials and never committed to git.
- Secure RPC nodes endpoints behind HTTPS and avoid logging plain API keys in debug screens.

Next: `start-work proofnode_phase6`
