# ASW Plan: ProofNode Phase 2 - Telegram Bot & Subscription Paywall Core

## TL;DR
Implement the core business logic for trader cabinet endpoints, the subscription paywall billing verification (supporting TON and Telegram Stars), and the Telegram Community Manager Bot (built with `aiogram 3` to handle automated invite links and user kicks).

---

## Objective
To build a functional B2B/B2C social paywall bot pipeline that:
1. Provides REST APIs for traders to manage profiles, wallets, and subscription tariffs.
2. Implements a payment verification endpoint checking TON transaction confirmations on-chain (using mock/rpc checks) and Telegram Stars transactions.
3. Initializes a Telegram Bot (`bot/main.py`) using `aiogram 3` that dynamically generates one-time invite links for valid subscriptions.
4. Implements a background subscription checker that automatically removes (kicks) expired users from Telegram groups/channels.
5. Validates invitation generation and expiration flows via automated tests.

---

## Non-Goals
- Copy-trading execution (signing transactions, proxy wallets) which is Phase 3.
- Implementing the interactive Frontend Mini App UI (Phase 4).
- Integrating with production live mainnet TON gateways (we will use TON Testnet RPC or local stubs for verification).

---

## Decision Summary
- **Bot Framework**: `aiogram 3` (Python async Telegram bot framework).
- **Payment Verification**: Synchronous or async RPC requests verifying incoming transaction hashes in the TON blockchain.
- **Invite link generation**: Dynamic creation of unique invite links via Telegram Bot API (`create_chat_invite_link` with `member_limit=1`).
- **Access Control**: Periodic scanner querying database for active subscriptions. If `expires_at < current_time` and user is in the channel, kick them using `ban_chat_member` and then `unban_chat_member`.
- **Testing**: Pytest integration tests mocking Telegram Bot API calls to assert correct invite generation and user management.

---

## Files to Edit & Create

### [MODIFY] Configuration & Dependencies
- `backend/requirements.txt` - Add `aiogram` dependency.
- `backend/app/config.py` - Add bot token (`BOT_TOKEN`) and channel/group ID (`CHANNEL_ID`) settings.

### [NEW] FastAPI Subscription & Tariff APIs
- `backend/app/routers/traders.py` - Endpoints for profile management, wallet registration, and tariff configurations.
- `backend/app/routers/subscriptions.py` - Endpoints to request purchase, verify payment (TON transaction / Stars), and fetch invite links.

### [NEW] Telegram Community Bot
- `bot/config.py` - Configuration loading for the Telegram bot.
- `bot/main.py` - Entrypoint for the `aiogram 3` bot. Handles `/start` and registers channel commands.
- `bot/scheduler.py` - Background polling loop that checks for expired subscriptions and executes kicks.

### [NEW] Testing Suite
- `tests/test_paywall.py` - Test case verifying payment confirmation and subscription creation.
- `tests/test_bot.py` - Test case mocking bot interaction, generating invite link, and user kicks on subscription expiration.

---

## TODOs

- [ ] **Dependencies & Configurations**
    - Add `aiogram>=3.4.0` to `backend/requirements.txt`.
    - Run `uv pip install -r backend/requirements.txt` to update the virtual environment.
    - Update `backend/app/config.py` to include:
      - `bot_token: str = Field(default="mock_token", alias="BOT_TOKEN")`
      - `channel_id: int = Field(default=0, alias="CHANNEL_ID")`
    - *Commit guidance*: "infra: add bot and channel settings and aiogram dependency"

- [ ] **FastAPI Trader Cabinet APIs**
    - Create `backend/app/routers/traders.py` implementing:
      - `POST /api/traders/profile` to insert a trader profile.
      - `POST /api/traders/wallets` to attach monitoring wallets.
      - `POST /api/traders/tariffs` to register payment tiers.
    - Mount the router in `backend/app/main.py`.
    - *Commit guidance*: "feat: implement trader profile and tariff management APIs"

- [ ] **Subscription Paywall & Verification**
    - Create `backend/app/routers/subscriptions.py` implementing:
      - `POST /api/subscriptions/purchase` to initiate a payment request.
      - `POST /api/subscriptions/verify` validating payment hash against blockchain RPC (mock/test stub) and creating a unique one-time chat invite link.
    - Mount the router in `backend/app/main.py`.
    - *Commit guidance*: "feat: implement payment verification and subscription endpoints"

- [ ] **Telegram Bot Implementation**
    - Create `bot/main.py` initializing the `aiogram` Bot and Dispatcher.
    - Implement `/start` command handler registering/linking user Telegram ID.
    - Implement bot method calls to generate invite links (`create_chat_invite_link`).
    - *Commit guidance*: "feat: implement telegram bot using aiogram 3"

- [ ] **Subscription Expiration Scheduler**
    - Create `bot/scheduler.py` implementing a background task checking database subscription expirations.
    - Implement logic calling bot `ban_chat_member` and `unban_chat_member` to revoke channel access for expired memberships.
    - Run the scheduler in the bot startup flow.
    - *Commit guidance*: "feat: implement subscription expiration monitoring worker"

- [ ] **Integration Testing**
    - Create `tests/test_paywall.py` verifying payment processing.
    - Create `tests/test_bot.py` using mock Telegram Bot API calls to test invite link creation and kick routines.
    - Run `PYTHONPATH=. uv run pytest -v` to ensure all tests pass.
    - *Commit guidance*: "test: add integration tests for bot and paywall"

---

## QA Scenarios

### Scenario 1: Bot Mock Invocation
- **Command**:
  - Start the bot with a mock token:
    ```bash
    BOT_TOKEN="123456:mock" CHANNEL_ID="-10012345678" uv run python -m bot.main &
    BOT_PID=$!
    sleep 2
    kill $BOT_PID
    ```
- **Expected Evidence**:
  - Terminal logs show bot initialized and started polling successfully.

### Scenario 2: Purchase and Payment Verification
- **Command**:
  - Spin up FastAPI gateway:
    ```bash
    uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
    GATEWAY_PID=$!
    sleep 2
    ```
  - Send POST request to purchase a tariff:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"user_id": 12345, "tariff_id": "some-tariff-uuid"}' \
         http://127.0.0.1:8000/api/subscriptions/purchase
    ```
  - Verify payment:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -d '{"user_id": 12345, "tx_hash": "mock_pay_hash", "tariff_id": "some-tariff-uuid"}' \
         http://127.0.0.1:8000/api/subscriptions/verify
    ```
  - Shut down gateway:
    ```bash
    kill $GATEWAY_PID
    ```
- **Expected Evidence**:
  - Purchase returns HTTP 200 with order confirmation.
  - Verify returns HTTP 200 with active subscription details and the invite link.

### Scenario 3: Complete Integration Test Suite Execution
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest -v
  ```
- **Expected Evidence**:
  - Output displays all tests passed: `tests/test_paywall.py::... PASSED` and `tests/test_bot.py::... PASSED`.

### Cleanup Receipt
- **Command**:
  - Standard process cleanup (killing background PIDs if orphaned).
- **Expected Evidence**:
  - No active backend or bot processes left running.

---

## Privacy & Package Safeguards
- Do not commit production Telegram Bot tokens or channel IDs.
- Ensure that testing uses mock/testnet credentials.

Next: `start-work proofnode_phase2`
