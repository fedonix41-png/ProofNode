# ASW Plan: ProofNode Phase 6 - Webhook Security & Core CRM Features

## TL;DR
Implement security-critical webhook signature verification for production readiness. Build the missing CRM features from the original spec: manual signal creation UI, public trader profiles with deep links, platform commission logic, and freemium limits for the Smart Money Tracker.

---

## Objective
To close the gap between current implementation and the original ТЗ:
1. Replace webhook signature stubs with real cryptographic verification (HMAC-SHA256 for Alchemy, header tokens for Helius and TonAPI).
2. Build RPC connection pools for reading wallet balances and verifying on-chain subscription payments.
3. Implement the "Honest Trader" CRM interface: manual signal creation with entry price capture, signal closing with PnL calculation, and automatic profile statistics.
4. Create public trader profile pages accessible via deep links (`t.me/AlphaHubBot/app?startapp=profile_{slug}`).
5. Add platform commission (5%) deduction from subscription payments.
6. Implement freemium limits: 3 wallets for free users, 10-minute push notification delay for non-premium.

---

## Non-Goals
- DEX aggregator integrations for automated copy-trading (reserved for Phase 8).
- Transaction signing and broadcasting (reserved for Phase 8).
- AWS KMS hardware HSM integration (reserved for Phase 9).
- Frontend TMA redesign.

---

## Decision Summary
- **Webhook Verification**:
  - Alchemy (Base): HMAC-SHA256 of raw request body using `ALCHEMY_WEBHOOK_SECRET`, compare to `x-alchemy-signature` header.
  - Helius (Solana): Validate `Authorization` header equals `HELIUS_WEBHOOK_SECRET`.
  - TonAPI (TON): Validate signature header or API token matching `TONAPI_WEBHOOK_SECRET`.
- **RPC Integration**:
  - TON: Async HTTP client to Toncenter v2 API for balance queries.
  - Solana: JSON-RPC client to Helius RPC endpoint.
  - Base: Web3.py client to Alchemy/Base RPC.
- **Signal CRM**:
  - Trader manually creates signal: token address, direction (BUY/SELL), timestamp.
  - Backend captures current DEX price via RPC call at signal creation time.
  - Trader closes signal: backend captures exit price, calculates PnL percentage.
  - Statistics aggregate to `trader_pnl_history` TimescaleDB table.
- **Public Profiles**:
  - Each `trader_profile` has unique `public_slug`.
  - Frontend parses `startapp` query param to navigate to profile view.
  - Profile displays cumulative ROI, winrate, signal history chart.
- **Monetization**:
  - Commission: When subscription payment verified, calculate 95% to trader, 5% to platform treasury address.
  - Freemium: Middleware checks `users.is_premium` before allowing >3 monitored wallets and before queuing instant push notifications.

---

## Files to Edit & Create

### [MODIFY] Configuration & Dependencies
- [requirements.txt](file:///home/ozzy/Документы/ProofNode/backend/requirements.txt) - Add `web3>=6.0.0`, `httpx` (for async HTTP RPC).
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Add `ALCHEMY_WEBHOOK_SECRET`, `HELIUS_WEBHOOK_SECRET`, `TONAPI_WEBHOOK_SECRET`, `PLATFORM_TREASURY_ADDRESS`, `SOLANA_RPC_URL`, `BASE_RPC_URL`, `TON_RPC_URL`.

### [MODIFY] Webhook Gateway
- [main.py](file:///home/ozzy/Документы/ProofNode/backend/app/main.py) - Implement signature verification functions for each gateway endpoint. Reject invalid signatures with 401.

### [NEW] RPC Clients
- [rpc.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/rpc.py) - Async connection pool wrappers for TON, Solana, Base RPC calls. Methods: `get_wallet_balance()`, `get_token_price()`, `verify_transaction()`.

### [MODIFY] Routers
- [subscriptions.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/subscriptions.py) - Use RPC client to verify payment transaction on-chain. Calculate and log 5% platform commission.
- [wallets.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/wallets.py) - Check freemium limit (3 wallets) before allowing new monitored wallet. Fetch real balance via RPC.
- [traders.py](file:///home/ozzy/Документы/ProofNode/backend/app/routers/traders.py) - Add endpoint `POST /traders/me/signals` for signal creation. Add endpoint `POST /traders/me/signals/{id}/close`. Add endpoint `GET /traders/{slug}` for public profile.

### [MODIFY] Frontend
- [Radar.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Radar.tsx) - Display real PnL from API. Show premium badge and wallet limit warning.
- [Leaderboard.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Leaderboard.tsx) - Add filter chips (TON, SOL, BASE, High Winrate). Fetch real trader data.
- [Cabinet.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/Cabinet.tsx) - Add "Author Tools" section with signal creation form. Add channel verification checklist.
- [App.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/App.tsx) - Parse `startapp` query param to navigate to public profile view.

### [NEW] Frontend Components
- [TraderProfile.tsx](file:///home/ozzy/Документы/ProofNode/frontend/src/components/TraderProfile.tsx) - Public profile view with ROI chart, signal history, subscribe button.

### [MODIFY] Bot Consumer
- [consumer.py](file:///home/ozzy/Документы/ProofNode/bot/consumer.py) - Check `users.is_premium` before sending instant notification. Queue delayed notifications for free users.

### [NEW] Testing Suite
- [test_crm_features.py](file:///home/ozzy/Документы/ProofNode/tests/test_crm_features.py) - Tests for signal creation, PnL calculation, public profile access, commission calculation.

---

## TODOs

- [x] **Dependencies and Configuration**
  - Add `web3>=6.0.0` and `httpx` to `backend/requirements.txt`.
  - Install: `uv pip install -r backend/requirements.txt`.
  - Define webhook secrets and RPC URLs in `backend/app/config.py`.
  - *Commit guidance*: "infra: add RPC client dependencies and security configuration"

- [x] **Webhook Signature Verification**
  - Implement in `backend/app/main.py`:
    - Alchemy: HMAC-SHA256 of request body, compare to `x-alchemy-signature` header (lowercase hex).
    - Helius: Compare `Authorization` header to secret.
    - TonAPI: Validate signature/token header.
  - Write unit tests for each verification function.
  - *Commit guidance*: "feat: implement cryptographic webhook signature validation"

- [x] **RPC Client Pool**
  - Create `backend/app/services/rpc.py` with async HTTP clients.
  - Implement `get_wallet_balance(blockchain, address)`.
  - Implement `get_token_price(blockchain, token_address)`.
  - Implement `verify_transaction(blockchain, tx_hash, expected_receiver, expected_amount)`.
  - Add connection pooling and timeout handling.
  - *Commit guidance*: "feat: add async RPC client pool for blockchain queries"

- [x] **On-chain Payment Verification**
  - Update `backend/app/routers/subscriptions.py`:
    - Replace mock verification with RPC `verify_transaction()`.
    - Calculate 5% commission, log to `subscription_payments` table.
  - *Commit guidance*: "feat: connect subscription payment verification to live RPC"

- [x] **Freemium Limits**
  - Update `backend/app/routers/wallets.py`:
    - Check `users.is_premium` before allowing wallet creation.
    - Reject with 402 if limit exceeded (3 for free, unlimited for premium).
  - Update `bot/consumer.py`:
    - Check premium status before instant notification.
    - Queue to `delayed_notifications` for free users (10-minute delay).
  - *Commit guidance*: "feat: implement freemium wallet limits and notification delays"

- [x] **Signal CRM - Backend**
  - Add `POST /traders/me/signals`: accept token_address, direction. Capture current price via RPC. Create signal record.
  - Add `POST /traders/me/signals/{id}/close`: capture exit price, calculate PnL, update signal status.
  - Add `GET /traders/{slug}`: return public profile data (ROI, winrate, recent signals).
  - *Commit guidance*: "feat: add signal creation and closing endpoints for trader CRM"

- [x] **Signal CRM - Frontend**
  - Update `Cabinet.tsx` with "Author Tools" section:
    - Form: token address input, BUY/SELL toggle, "Open Signal" button.
    - List of open signals with "Close" button.
  - *Commit guidance*: "feat: add signal management UI to trader cabinet"

- [x] **Public Trader Profiles**
  - Create `TraderProfile.tsx` component:
    - ROI chart (SVG sparkline or canvas).
    - Winrate badge, cumulative PnL.
    - List of closed signals with individual PnL.
    - Tariff cards with subscribe buttons.
  - Update `App.tsx` to parse `startapp=profile_{slug}` and route to profile.
  - *Commit guidance*: "feat: add public trader profile view with deep link routing"

- [ ] **Leaderboard Filters**
  - Update `Leaderboard.tsx`:
    - Add filter chips: "All", "TON", "SOL", "BASE", "High Winrate".
    - Fetch filtered data from API.
  - Add backend filter support in `GET /traders` endpoint.
  - *Commit guidance*: "feat: add blockchain and winrate filters to marketplace"

- [x] **Integration Tests**
  - Create `tests/test_crm_features.py`:
    - Test signal creation with mocked price capture.
    - Test PnL calculation on close.
    - Test commission calculation.
    - Test freemium limit enforcement.
  - Run: `PYTHONPATH=. uv run pytest tests/test_crm_features.py -v`.
  - *Commit guidance*: "test: add integration tests for CRM and monetization features"

---

## QA Scenarios

### Scenario 1: Webhook Rejection
- **Command**:
  ```bash
  uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
  sleep 2
  curl -X POST -H "Content-Type: application/json" \
       -H "x-alchemy-signature: invalid_signature" \
       -d '{"tx_hash": "0xtest"}' \
       http://127.0.0.1:8000/gateway/evm
  ```
- **Expected Evidence**: Returns `401 Unauthorized` or `403 Forbidden`.

### Scenario 2: Signal Creation and PnL
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_crm_features.py::test_signal_pnl_calculation -v
  ```
- **Expected Evidence**: Test passes, showing PnL calculated correctly from mocked entry/exit prices.

### Scenario 3: Freemium Wallet Limit
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_crm_features.py::test_freemium_wallet_limit -v
  ```
- **Expected Evidence**: Test passes, rejecting 4th wallet for non-premium user.

### Scenario 4: Public Profile Deep Link
- **Command**:
  - Open browser/Telegram and navigate to: `t.me/AlphaHubBot/app?startapp=profile_crypto-wizard`
- **Expected Evidence**: TMA opens on TraderProfile view for slug `crypto-wizard`.

### Cleanup Receipt
- **Command**: `docker compose down -v` (if running services)
- **Expected Evidence**: Containers stopped and volumes removed.

---

## Privacy & Package Safeguards
- Never log webhook secrets or API keys.
- Filter sensitive data from Sentry breadcrumbs if integrated later.
- Use environment variables for all secrets, never hardcode.

Next: `start-work proofnode_phase7`
