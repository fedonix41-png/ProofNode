# ASW Plan: ProofNode Phase 8 - DEX Aggregator & Copy-Trading Execution

## TL;DR
Implement production-grade DEX aggregator integrations for automated and 1-click copy-trading. Connect to Jupiter V6 (Solana), 1inch (Base), and Ston.fi/DeDust (TON) APIs. Build transaction serialization, signing, and broadcasting for proxy wallets.

---

## Objective
To enable actual on-chain copy-trade execution:
1. Integrate Jupiter V6 API for Solana swap quotes and serialized transactions.
2. Integrate 1inch Swap API for Base routing and transaction payloads.
3. Integrate Ston.fi and DeDust APIs for TON jetton swaps.
4. Implement Ed25519 signing for Solana/TON and ECDSA signing for Base.
5. Broadcast signed transactions via RPC endpoints.
6. Build retry logic with slippage protection and gas price monitoring.

---

## Non-Goals
- AWS KMS hardware HSM (Phase 9).
- Frontend TMA redesign.
- Smart contract development (use existing DEX contracts).

---

## Decision Summary
- **Solana (Jupiter V6)**:
  - Call `https://quote-api.jup.ag/v6/quote` with input/output mint, amount, slippage.
  - Call `https://quote-api.jup.ag/v6/swap` to get base64 serialized `VersionedTransaction`.
  - Deserialize with `solders.transaction.VersionedTransaction.from_base64()`.
  - Sign with proxy wallet's Ed25519 keypair.
  - Broadcast via Solana RPC `sendTransaction`.
- **Base (1inch)**:
  - Call `https://api.1inch.dev/swap/v6.0/8453/swap` with API key.
  - Receive transaction payload: `to`, `data`, `value`, `gas`.
  - Build raw transaction with Web3.py, sign with ECDSA private key.
  - Broadcast via `eth_sendRawTransaction`.
- **TON (Ston.fi)**:
  - Build jetton swap payload matching Ston.fi router contract.
  - Create external message, sign with Ed25519.
  - Broadcast via Toncenter v2 `sendBoc` or TonAPI.
- **Safety**:
  - Pre-execution simulation via RPC `simulateTransaction` (Solana) or `eth_call` (Base).
  - Slippage: retry with increased slippage up to max configured limit.
  - Gas monitoring: reject if gas price exceeds threshold.

---

## Files to Edit & Create

### [MODIFY] Configuration
- [requirements.txt](file:///home/ozzy/Документы/ProofNode/backend/requirements.txt) - Add `solana>=0.30.0`, `solders`, `base58`.
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Add `JUPITER_API_URL`, `ONEINCH_API_KEY`, `STONFI_API_URL`, `MAX_SLIPPAGE_BPS`, `MAX_GAS_PRICE_GWEI`.

### [MODIFY] Services
- [dex.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/dex.py) - Replace mock quote router with real API integrations. Implement quote fetching, transaction building, signing, and broadcasting for each chain.

### [NEW] Services
- [signing.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/signing.py) - Transaction signing utilities: Ed25519 for Solana/TON, ECDSA for Base.
- [simulation.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/simulation.py) - Pre-execution simulation and safety checks.

### [MODIFY] Workers
- [copy_worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/copy_worker.py) - Use real DEX execution instead of mock. Add retry logic with slippage escalation.

### [NEW] Testing
- [test_dex_integrations.py](file:///home/ozzy/Документы/ProofNode/tests/test_dex_integrations.py) - Tests for API quote parsing, transaction serialization, signing math verification.
- [test_copy_execution.py](file:///home/ozzy/Документы/ProofNode/tests/test_copy_execution.py) - End-to-end copy-trade flow tests with mocked RPC responses.

---

## TODOs

- [ ] **Dependencies Setup**
  - Add to `requirements.txt`:
    ```
    solana>=0.30.0
    solders>=0.18.0
    base58>=2.1.1
    ```
  - Install: `uv pip install -r backend/requirements.txt`.
  - Configure API endpoints and keys in `config.py`.
  - *Commit guidance*: "infra: add Solana transaction signing dependencies"

- [ ] **Jupiter V6 Integration (Solana)**
  - In `backend/app/services/dex.py`:
    - Implement `get_jupiter_quote(input_mint, output_mint, amount, slippage_bps)`.
    - Implement `get_jupiter_swap_tx(quote, user_public_key)`.
    - Implement `sign_and_send_solana_tx(serialized_tx_base64, private_key_bytes)`.
  - Use `solders.transaction.VersionedTransaction` for deserialization.
  - Use `solders.signature.Signature` for signature verification in tests.
  - *Commit guidance*: "feat: implement Jupiter V6 swap integration for Solana"

- [ ] **1inch Integration (Base)**
  - In `backend/app/services/dex.py`:
    - Implement `get_1inch_quote(src_token, dst_token, amount)`.
    - Implement `get_1inch_swap_tx(src_token, dst_token, amount, from_address, slippage)`.
    - Implement `sign_and_send_base_tx(tx_dict, private_key_hex)`.
  - Use Web3.py for transaction building and signing.
  - *Commit guidance*: "feat: implement 1inch swap integration for Base"

- [ ] **Ston.fi Integration (TON)**
  - In `backend/app/services/dex.py`:
    - Implement `get_stonfi_route(from_jetton, to_jetton, amount)`.
    - Implement `build_stonfi_swap_msg(route, wallet_address)`.
    - Implement `sign_and_send_ton_tx(message_payload, private_key_hex)`.
  - Use Toncenter v2 API for broadcasting.
  - *Commit guidance*: "feat: implement Ston.fi swap integration for TON"

- [ ] **Transaction Signing Service**
  - Create `backend/app/services/signing.py`:
    - `sign_ed25519(tx_bytes, private_key_bytes)` → returns signature + signed tx.
    - `sign_ecdsa(tx_dict, private_key_hex)` → returns signed raw tx hex.
    - `verify_ed25519_signature(tx_bytes, signature, public_key)`.
  - *Commit guidance*: "feat: add unified transaction signing utilities"

- [ ] **Pre-execution Simulation**
  - Create `backend/app/services/simulation.py`:
    - `simulate_solana_tx(serialized_tx)` using RPC `simulateTransaction`.
    - `simulate_base_tx(tx_dict)` using `eth_call`.
    - `check_gas_price(chain)` → returns current gas price, compare to max.
  - *Commit guidance*: "feat: add pre-execution simulation and gas monitoring"

- [ ] **Copy Worker Integration**
  - Update `backend/app/copy_worker.py`:
    - Replace mock `execute_swap()` with real DEX calls.
    - Add retry loop: up to 3 attempts with slippage escalation (100 → 200 → 300 bps).
    - Log execution outcome to `copy_trade_executions`.
  - *Commit guidance*: "feat: connect copy worker to live DEX execution"

- [ ] **Integration Tests**
  - Create `tests/test_dex_integrations.py`:
    - Test Jupiter quote parsing with recorded response.
    - Test Solana transaction signing math.
    - Test 1inch swap payload parsing.
    - Test Base transaction signing.
    - Test Ston.fi route response handling.
  - Create `tests/test_copy_execution.py`:
    - Test full copy-trade flow with mocked RPC.
    - Test retry logic on simulated failure.
  - Run: `PYTHONPATH=. uv run pytest tests/test_dex_integrations.py tests/test_copy_execution.py -v`.
  - *Commit guidance*: "test: add comprehensive DEX and copy-trade execution tests"

---

## QA Scenarios

### Scenario 1: Solana Quote and Sign
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_dex_integrations.py::test_jupiter_quote_parsing -v
  PYTHONPATH=. uv run pytest tests/test_dex_integrations.py::test_solana_signing_math -v
  ```
- **Expected Evidence**: Tests pass, showing correct quote parsing and Ed25519 signature verification.

### Scenario 2: Base Swap Flow
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_dex_integrations.py::test_1inch_swap_flow -v
  ```
- **Expected Evidence**: Test passes, showing correct transaction construction and ECDSA signing.

### Scenario 3: Copy Execution Retry
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_copy_execution.py::test_copy_retry_on_failure -v
  ```
- **Expected Evidence**: Test passes, showing worker retries with increased slippage on simulated failure.

### Scenario 4: Gas Price Check
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_dex_integrations.py::test_gas_price_rejection -v
  ```
- **Expected Evidence**: Test passes, showing transaction rejected when gas exceeds max threshold.

### Cleanup Receipt
- **Command**: `docker compose down -v`
- **Expected Evidence**: All containers and volumes stopped.

---

## Privacy & Package Safeguards
- Never log decrypted private keys.
- Use environment variables for all API keys.
- Test with testnet/devnet RPC endpoints only.
- Mock RPC responses in CI to avoid rate limiting.

Next: `start-work proofnode_phase9`
