# ASW Plan: ProofNode Phase 5 - Telegram Bot Notification Consumer Integration

## TL;DR
Integrate a background RabbitMQ consumer into the Telegram Bot (`bot/main.py`). The consumer will listen to the `tg_bot_notifications` queue, process incoming copy-trade alerts (triggered in Phase 3 for `1-CLICK` copy-trade mode), and send rich interactive alerts to subscribers containing inline buttons that deep-link directly into the Telegram Mini App (TMA).

---

## Objective
To close the communications loop between the trading execution engine and the user interface:
1. Establish a background queue consumer task in the `aiogram` bot process that connects to RabbitMQ and listens to the `tg_bot_notifications` queue.
2. Formulate a parser that extracts transaction metadata (monitored wallet alias, network, coin pair, and volume) from notification payloads.
3. Construct rich text alerts with interactive inline buttons (e.g. `[⚡ Confirm 1-Click Copy-Trade]`) that deep-link users into the TMA with contextual query params (`startapp=copy_<pending_trade_id>`).
4. Support clean connection recovery for the consumer task in case of RabbitMQ connection drops.
5. Create automated tests validating queue ingestion and bot message routing.

---

## Non-Goals
- Executing transactions directly from the bot. The bot only acts as a delivery gateway; execution is handled by the React TMA in Phase 4.
- Integrating real mainnet DEX aggregates or node RPC queries (Phase 6).
- Integrating AWS KMS (Phase 7).

---

## Decision Summary
- **Broker Interface**: `aio-pika` (same async AMQP library utilized in FastAPI gateway/worker).
- **Notification Format**: JSON payloads published by `copy_worker.py`:
  ```json
  {
    "user_id": 12345,
    "pending_trade_id": "uuid-v4-string",
    "blockchain": "TON",
    "token_in_symbol": "TON",
    "token_out_symbol": "USDT",
    "amount_in": "15.0",
    "trader_alias": "Alpha Whale #1"
  }
  ```
- **Deep-linking Syntax**: Inline buttons point to `t.me/<bot_username>/app?startapp=copy_<pending_trade_id>`. This allows the Telegram client to pass the parameter directly to the React TMA on launch.
- **Task Management**: Initialize the consumer during `aiogram`'s `on_startup` bot event. Ensure it runs as a non-blocking asyncio task and cleans up during `on_shutdown`.

---

## Files to Edit & Create

### [MODIFY] Bot Core
- [bot/main.py](file:///home/ozzy/Документы/ProofNode/bot/main.py) - Register the RabbitMQ consumer startup/shutdown lifecycle handlers in the `aiogram` Dispatcher.

### [NEW] Bot Consumer Service
- [bot/consumer.py](file:///home/ozzy/Документы/ProofNode/bot/consumer.py) - Asynchronous RabbitMQ consumer client using `aio-pika`. Listens to `tg_bot_notifications`, decodes JSON, constructs messages, and uses the `aiogram.Bot` instance to dispatch alerts.

### [NEW] Testing Suite
- [tests/test_bot_consumer.py](file:///home/ozzy/Документы/ProofNode/tests/test_bot_consumer.py) - Integration test verifying that publishing a notification payload to RabbitMQ results in the bot sending a formatted Telegram message with deep-link buttons.

---

## TODOs

- [ ] **Create the Bot Consumer Module**
  - Implement `bot/consumer.py` using `aio-pika` to:
    - Establish connection to RabbitMQ (`settings.rabbitmq_host`, etc.).
    - Declare and bind to `tg_bot_notifications` queue.
    - Parse JSON payloads into structured objects.
    - Format a premium notification card:
      ```text
      📊 [Trader Alias] has executed a trade!
      
      🔄 Swap: [AmountIn] [TokenIn] -> [TokenOut]
      🌐 Network: [Blockchain]
      
      Click the button below to sign and execute this swap with 1-Click.
      ```
    - Attach an inline keyboard containing:
      `[⚡ Copy Trade (TMA)]` -> `url=https://t.me/{bot_username}/app?startapp=copy_{pending_trade_id}`
    - Dispatch the message using the bot instance.
  - *Commit guidance*: "feat: implement rabbitmq notification consumer service for tg bot"

- [ ] **Integrate Consumer with Bot Lifecycle**
  - Modify `bot/main.py`:
    - Add startup hook `start_rabbitmq_consumer` that launches the consumer as an asynchronous background task.
    - Add shutdown hook `stop_rabbitmq_consumer` to cleanly close channels and connections.
  - *Commit guidance*: "feat: register notification consumer background task in bot startup"

- [ ] **Write Bot Consumer Integration Tests**
  - Create `tests/test_bot_consumer.py` containing a test case that:
    - Set up a mock/test Bot instance.
    - Connect to the RabbitMQ container (via the `rabbitmq_server` fixture).
    - Start the bot consumer task.
    - Publish a mock notification payload to the `tg_bot_notifications` queue.
    - Assert that `bot.send_message` was called with the expected user ID, text content containing "Alpha Whale #1", and inline keyboard button matching the deep-link URL pattern.
  - *Commit guidance*: "test: add integration test for bot rabbitmq notification consumer"

---

## QA Scenarios

### Scenario 1: Bot Notification Pipeline Verification
- **Command**:
  - Start RabbitMQ via docker compose if down:
    ```bash
    docker compose up -d rabbitmq
    ```
  - Run the new bot consumer test:
    ```bash
    PYTHONPATH=. uv run pytest tests/test_bot_consumer.py -v
    ```
- **Expected Evidence**:
  - Pytest logs show `tests/test_bot_consumer.py::test_bot_notification_processing PASSED`.

### Scenario 2: E2E 1-Click Signal Propagation
- **Command**:
  - Spin up API gateway, parser worker, copy worker, and the bot:
    ```bash
    # 1. Start services
    uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
    GATEWAY_PID=$!
    uv run python -m backend.app.worker &
    PARSER_PID=$!
    uv run python -m backend.app.copy_worker &
    COPY_PID=$!
    BOT_TOKEN="123456:mock" CHANNEL_ID="-10012" uv run python -m bot.main &
    BOT_PID=$!
    sleep 3
    
    # 2. Publish a webhook trade matching a 1-CLICK configuration
    curl -X POST -H "Content-Type: application/json" \
         -H "X-Tonapi-Signature: test_sig" \
         -d '{"tx_hash": "ton_tx_999", "wallet_address": "EQ_TRADER_1", "logical_time": 900, "time": "2026-06-11T03:30:00Z", "payload": "raw_hex"}' \
         http://127.0.0.1:8000/gateway/ton
         
    sleep 3
    # 3. Clean up
    kill $GATEWAY_PID $PARSER_PID $COPY_PID $BOT_PID
    ```
- **Expected Evidence**:
  - Terminal logs for the bot show that a notification was received from RabbitMQ and the bot attempted to deliver the deep-link copy button to the user.

### Cleanup Receipt
- **Command**:
  - Stop the containers:
    ```bash
    docker compose down -v
    ```
- **Expected Evidence**:
  - Containers stopped and removed.

---

## Privacy & Package Safeguards
- Confirm that no sensitive transaction hashes or user data are leaked in raw RabbitMQ broker debug logs.

Next: `start-work proofnode_phase5`
