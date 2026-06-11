# ASW Plan: ProofNode Phase 3 - Copy-Trading & Wallet Security Core

## TL;DR
Implement the core security mechanisms and routing engines for Copy-Trading in **ProofNode**. This includes SSS 2-of-3 client-side reconstruction endpoints (managing the server-side Share 2), automated proxy wallet lifecycle management (with KMS key encryption stubs), DEX router routing mocks (Ston.fi, DeDust, Jupiter, 1inch), and a dedicated asynchronous Copy-Trading Execution Worker (`copy_worker.py`) that processes triggered trades in real time (within 1.5–3 seconds of the master event).

---

## Objective
To develop the transaction-signing and copying pipelines:
1. **Shamir's Secret Sharing (SSS) 2-of-3 API:** Endpoints to register and retrieve the server-side share (Share 2) for non-custodial 1-Click Copy-Trading.
2. **KMS-secured Proxy Wallets:** API to create proxy wallets with balance caching and limits, encrypting their private keys using a Pydantic/cryptography-based KMS stub.
3. **DEX Aggregator & Routing Services:** Stub/service layer generating transaction payloads for TON, Solana, and Base (EVM), signing them in-memory, and simulating broadcast/confirmation.
4. **Copy-Trading Trigger Pipeline:** Update the existing Event Parser Worker (`worker.py`) to detect trader transactions and enqueue copy-trading jobs.
5. **Copy-Trading Execution Engine:** Create a dedicated worker (`copy_worker.py`) consuming copy jobs to execute automated trades on proxy wallets and queue notifications for 1-Click trades.
6. **Robust Integration Testing:** Add comprehensive tests (pytest) validating key reconstruction, proxy limits, and end-to-end trade copying inside Testcontainers.

---

## Non-Goals
- Building the frontend user interface (UI) components or integrating the Telegram Mini App (TMA) library in React (Phase 4).
- Integrating with production-grade HSM/AWS KMS/GCP KMS APIs directly (stubs/local symmetric encryption will be used).
- Performing live mainnet transactions on TON, Solana, or Base.

---

## Decision Summary
- **SSS Share 2 Management:** Secure storage of text/hex shares in `user_sss_shares` with access verification.
- **KMS Service Stub:** Uses `cryptography.fernet` with a master key (`KMS_MASTER_KEY`) loaded from environment variables to encrypt/decrypt proxy keys.
- **Proxy Key Generation:** 
  - For EVM/Base: Standard ECDSA keys using `cryptography.hazmat.primitives.asymmetric.ec`.
  - For TON & Solana: Cryptographically secure random 32-byte seeds/hex strings mimicking Ed25519 keypairs.
- **Queue Pipeline:**
  - `raw_blockchain_events` -> **Event Parser Worker** -> DB + evaluates trader list.
  - If Trader match: Publish to `copy_trade_execution` queue.
  - **Copy-Trading Worker** -> Consumes `copy_trade_execution` -> signs/executes (or queues notification).
- **Database Schema Updates:** Add tables for `user_proxy_wallets`, `copy_trade_configs`, `user_sss_shares`, `pending_copy_trades`, and `copy_trade_executions`.

---

## Files to Edit & Create

### [MODIFY] Database & Core
- `database/init_db.sql` - Append table definitions for SSS shares, proxy wallets, configurations, and copy executions.
- `backend/app/config.py` - Add `KMS_MASTER_KEY` settings.
- `backend/app/main.py` - Declare the `copy_trade_execution` queue and mount the new routers.

### [NEW] Services
- [sss.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/sss.py) - SSS mathematics (Lagrange interpolation in finite fields) for testing.
- [kms.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/kms.py) - Local symmetric key encryption mock for KMS.
- [dex.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/dex.py) - DEX quote routing, payload builder, and broadcast stub.

### [NEW] Routers
- [wallets.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/wallets.py) - SSS and Proxy Wallet CRUD APIs.
- [copytrade.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/copytrade.py) - User copy configuration and 1-Click execution endpoint.

### [MODIFY] Workers
- `backend/app/worker.py` - Intercept parsed transactions, lookup subscriptions, and publish to `copy_trade_execution`.

### [NEW] Workers
- [copy_worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/copy_worker.py) - Copy-Trade execution worker.

### [NEW] Testing Suite
- [test_sss.py](file:///home/ozzy/Документы/ProofNode/tests/test_sss.py) - SSS split/reconstruction unit test.
- [test_wallets.py](file:///home/ozzy/Документы/ProofNode/tests/test_wallets.py) - SSS registration & proxy wallet APIs validation.
- [test_copytrade.py](file:///home/ozzy/Документы/ProofNode/tests/test_copytrade.py) - Integration tests for the copy execution pipeline.

---

## TODOs

- [ ] **Database Schema Expansion**
    - Modify `database/init_db.sql` to include tables:
      - `user_sss_shares` (storing Share 2 for user wallet addresses).
      - `user_proxy_wallets` (encrypted proxy keys, balance, budget limits).
      - `copy_trade_configs` (modes: `1-CLICK`/`AUTOMATED`, slippage, max allocation).
      - `pending_copy_trades` (tracking active 1-Click signals).
      - `copy_trade_executions` (archiving completed trade records).
    - *Commit guidance*: "database: add tables for wallet security and copy trading"

- [ ] **KMS and SSS Services Development**
    - Create `backend/app/config.py` updates to define `KMS_MASTER_KEY` (fallback to a generated Fernet key in testing).
    - Create `backend/app/services/kms.py` using `cryptography.fernet` to expose `encrypt_key(private_key_hex: str) -> str` and `decrypt_key(encrypted_str: str) -> str`.
    - Create `backend/app/services/sss.py` implementing 2-of-3 Shamir's Secret Sharing mathematics for test assertions (splitting and reconstructing keys).
    - *Commit guidance*: "feat: implement cryptographic SSS and KMS stub services"

- [ ] **DEX Service Implementation**
    - Create `backend/app/services/dex.py` containing:
      - `get_swap_quote(blockchain: str, token_in: str, token_out: str, amount: Decimal) -> dict` returning estimated routing, fees, and an unsigned transaction payload.
      - `sign_and_broadcast_transaction(blockchain: str, unsigned_payload: dict, private_key: str) -> str` returning a mock transaction hash.
    - *Commit guidance*: "feat: implement mock DEX router routing service"

- [ ] **Wallet Security & Copy-trading Routers**
    - Create `backend/app/routers/wallets.py` containing endpoints:
      - `POST /api/wallets/sss/register` -> save user Share 2.
      - `POST /api/wallets/sss/retrieve` -> retrieve user Share 2.
      - `POST /api/wallets/proxy/create` -> generate proxy keypair, encrypt with KMS, save to DB.
      - `POST /api/wallets/proxy/deposit` -> simulate wallet funding.
    - Create `backend/app/routers/copytrade.py` containing endpoints:
      - `POST /api/copytrade/config` -> create/update configuration.
      - `GET /api/copytrade/config/{subscription_id}` -> retrieve config.
      - `POST /api/copytrade/execute-1click` -> record a user's signed 1-Click transaction hash.
    - Mount routers in `backend/app/main.py`.
    - *Commit guidance*: "feat: add wallet security and copy-trading routers"

- [ ] **Trigger Integration in Event Parser Worker**
    - Update `backend/app/worker.py` to:
      1. Query if parsed transaction `wallet_address` is in `trader_wallets`.
      2. If yes, query all active subscribers in `subscriptions` with an active `copy_trade_configs`.
      3. For each match, enqueue a copy job to RabbitMQ queue `copy_trade_execution` containing user_id, config options, and trade tokens/amounts.
    - *Commit guidance*: "feat: connect event parser worker to copy trade queue triggers"

- [ ] **Copy-Trading Execution Worker**
    - Create `backend/app/copy_worker.py` consuming from `copy_trade_execution`:
      - If `copy_mode == 'AUTOMATED'`:
        1. Fetch user proxy wallet.
        2. Decrypt private key with KMS.
        3. Request mock DEX quote & sign payload.
        4. Sim-broadcast swap transaction.
        5. Record result in `copy_trade_executions`.
      - If `copy_mode == '1-CLICK'`:
        1. Create a row in `pending_copy_trades` (status: `PENDING`).
        2. Publish warning/alert message to `tg_bot_notifications` queue.
    - *Commit guidance*: "feat: implement copy trade execution worker"

- [ ] **Comprehensive Automated Testing**
    - Create `tests/test_sss.py` testing SSS maths correctness.
    - Create `tests/test_wallets.py` validating registration, retrieval, and encryption.
    - Create `tests/test_copytrade.py` simulating full lifecycle:
      - Create trader profile and register wallet.
      - Subscribe user, config AUTOMATED copy, fund proxy wallet.
      - Publish raw webhook trade for trader wallet.
      - Let parser worker run -> triggers copy job -> let copy worker execute -> assert copy trade logged in DB with success.
    - Run the entire test suite using:
      ```bash
      PYTHONPATH=. uv run pytest -v
      ```
    - *Commit guidance*: "test: add unit and integration tests for phase 3"

---

## QA Scenarios

### Scenario 1: SSS 2-of-3 Key Verification
- **Command**:
  - Run the SSS specific test suite:
    ```bash
    PYTHONPATH=. uv run pytest tests/test_sss.py -v
    ```
- **Expected Evidence**:
  - Console prints all SSS math test suites as `PASSED`.

### Scenario 2: End-to-End Automated Copy Trade Execution
- **Command**:
  - Spin up API gateway and both workers:
    ```bash
    # Set up master KMS encryption key
    export KMS_MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # 1. Start gateway
    uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
    GATEWAY_PID=$!
    sleep 2
    
    # 2. Start Event Parser Worker
    uv run python -m backend.app.worker &
    PARSER_PID=$!
    sleep 2
    
    # 3. Start Copy Worker
    uv run python -m backend.app.copy_worker &
    COPY_PID=$!
    sleep 2
    
    # Run integration test scenario or trigger webhook curl
    PYTHONPATH=. uv run pytest tests/test_copytrade.py -v
    
    # Shut down processes
    kill $GATEWAY_PID $PARSER_PID $COPY_PID
    ```
- **Expected Evidence**:
  - Output shows the integration test suite successfully executing a trader webhook swap and validating that the user's proxy wallet performed a matching transaction recorded in the database.

### Cleanup Receipt
- **Command**:
  - Tear down the docker environment (if up) and kill background PIDs:
    ```bash
    docker compose down -v
    ```
- **Expected Evidence**:
  - Clean local directory state, no running docker containers or orphaned python background tasks.

---

## Privacy & Package Safeguards
- The master KMS key must remain an ephemeral runtime secret (either auto-generated in sandbox/testing or loaded from environment variables). Never commit plain keys to Git.
- SSS client shares are never transmitted or processed by the server; the API must only handle Share 2.

Next: `start-work proofnode_phase3`
