# Technical Reference

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_HOST` | PostgreSQL host | Yes |
| `POSTGRES_PORT` | PostgreSQL port (default: 5432) | No |
| `POSTGRES_USER` | Database user | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `RABBITMQ_HOST` | RabbitMQ host | Yes |
| `RABBITMQ_PORT` | RabbitMQ port (default: 5672) | No |
| `RABBITMQ_USER` | RabbitMQ user | Yes |
| `RABBITMQ_PASSWORD` | RabbitMQ password | Yes |
| `REDIS_HOST` | Redis host | Yes |
| `REDIS_PORT` | Redis port (default: 6379) | No |
| `BOT_TOKEN` | Telegram Bot API token | Yes |
| `CHANNEL_ID` | Telegram channel ID for subscriptions | Yes |
| `KMS_MASTER_KEY` | Fernet key for proxy wallet encryption | Yes |
| `ALCHEMY_WEBHOOK_SECRET` | Alchemy webhook signature | Yes |
| `HELIUS_WEBHOOK_SECRET` | Helius webhook signature | Yes |
| `TONAPI_WEBHOOK_SECRET` | TonAPI webhook signature | Yes |
| `SOLANA_RPC_URL` | Solana RPC endpoint for queries | Yes |
| `BASE_RPC_URL` | Base RPC endpoint for queries | Yes |
| `TON_RPC_URL` | TON RPC endpoint for queries | Yes |
| `PLATFORM_TREASURY_ADDRESS` | Address receiving 5% platform commssion | Yes |
| `ENV` | Environment (`development`/`production`/`testing`) | No |
| `KMS_PROVIDER` | `aws`, `vault`, or `local` | No |
| `AWS_KMS_KEY_ID` | Key ID for AWS KMS envelope encryption | No |
| `VAULT_URL` | HashiCorp Vault URL | No |
| `VAULT_TOKEN` | HashiCorp Vault Token | No |
| `SENTRY_DSN` | Sentry DSN for exception tracking | No |
| `PROMETHEUS_ENABLED` | Set to `true` to enable `/metrics` | No |

---

## Webhook Endpoints

All endpoints return `202 Accepted` on success.

| Endpoint | Blockchain | Header |
|----------|------------|--------|
| `POST /gateway/ton` | TON | `X-Tonapi-Signature` |
| `POST /gateway/sol` | Solana | `X-Helius-Signature` |
| `POST /gateway/evm` | Base | `X-Alchemy-Signature` |

### Payload Examples

**TON Webhook:**
```json
{
  "tx_hash": "0xabc123...",
  "wallet_address": "EQD...abc",
  "time": "2024-01-15T10:30:00Z",
  "logical_time": 3849203000,
  "trace_id": "trace_abc123",
  "payload": "{\"dex_name\":\"Ston.fi\",\"token_in\":\"EQ...\",\"token_out\":\"EQ...\",\"amount_in\":100.0,\"amount_out\":250.0,\"tx_type\":\"BUY\"}"
}
```

**Solana Webhook:**
```json
{
  "tx_hash": "5Kq3...",
  "wallet_address": "Gh9...",
  "time": "2024-01-15T10:30:00Z",
  "signature_ver": "ed25519:...",
  "payload": "{\"dex_name\":\"Jupiter\",\"token_in\":\"...\",\"token_out\":\"...\",\"amount_in\":10.0,\"amount_out\":150.0,\"tx_type\":\"SELL\"}"
}
```

**EVM (Base) Webhook:**
```json
{
  "tx_hash": "0xdef456...",
  "wallet_address": "0x123...",
  "time": "2024-01-15T10:30:00Z",
  "block_number": 12345678,
  "payload": "{\"dex_name\":\"Uniswap\",\"token_in\":\"0x...\",\"token_out\":\"0x...\",\"amount_in\":0.5,\"amount_out\":1800.0,\"tx_type\":\"BUY\"}"
}
```

---

## RabbitMQ Queues

| Queue | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `raw_blockchain_events` | Gateway API | Event Parser | Ingestion buffer |
| `copy_trade_execution` | Event Parser | Copy Worker | Trade execution jobs |
| `tg_bot_notifications` | Various | Bot Worker | User push notifications |

### Message Schemas

**raw_blockchain_events:**
```json
{
  "blockchain": "TON",
  "tx_hash": "0xabc123...",
  "payload": { /* WebhookPayload object */ }
}
```

**copy_trade_execution:**
```json
{
  "user_id": 123456789,
  "subscription_id": "uuid-v4",
  "trader_tx_hash": "0xabc123...",
  "blockchain": "TON",
  "copy_mode": "1-CLICK",
  "proxy_wallet_id": "uuid-v4 | null",
  "token_in": "EQ...",
  "token_out": "EQ...",
  "amount_in": "10.5",
  "slippage_bps": 100
}
```

---

## Critical Database Tables

### `wallet_transactions` (TimescaleDB Hypertable)

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMPTZ | Transaction timestamp (partition key) |
| `tx_hash` | VARCHAR(128) | Blockchain transaction hash |
| `trace_id` | VARCHAR(128) | TON logical trace correlation |
| `logical_time` | BIGINT | TON message ordering |
| `wallet_address` | VARCHAR(256) | Trader wallet |
| `blockchain` | VARCHAR(10) | `TON` / `BASE` / `SOL` |
| `dex_name` | VARCHAR(50) | DEX identifier |
| `token_in_address` | VARCHAR(256) | Input token contract |
| `token_out_address` | VARCHAR(256) | Output token contract |
| `amount_in` | NUMERIC(40,18) | Input amount |
| `amount_out` | NUMERIC(40,18) | Output amount |
| `usd_value` | NUMERIC(15,2) | USD equivalent |
| `tx_type` | VARCHAR(10) | `BUY` / `SELL` / `TRANSFER` |

Retention: 90 days. Compression after 14 days.

### `copy_trade_configs`

| Column | Type | Description |
|--------|------|-------------|
| `subscription_id` | UUID | FK to subscriptions |
| `copy_mode` | VARCHAR(20) | `1-CLICK` / `AUTOMATED` |
| `proxy_wallet_id` | UUID | FK for automated mode |
| `max_allocation_per_trade` | NUMERIC(40,18) | Budget limit |
| `slippage_bps` | INT | Slippage tolerance (basis points) |
| `is_active` | BOOLEAN | Enable flag |

### `user_proxy_wallets`

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | BIGINT | Telegram user ID |
| `blockchain` | VARCHAR(10) | Chain identifier |
| `address` | VARCHAR(256) | Wallet public address |
| `encrypted_private_key` | TEXT | KMS-encrypted private key |
| `balance` | NUMERIC(40,18) | Current balance |

### `signals`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `trader_profile_id` | UUID | FK to `trader_profiles` |
| `blockchain` | VARCHAR(10) | Chain identifier (`TON`, `BASE`, `SOL`) |
| `token_address` | VARCHAR(256) | Token contract address |
| `direction` | VARCHAR(4) | `BUY` or `SELL` |
| `entry_price` | NUMERIC | Captured Entry price via RPC |
| `exit_price` | NUMERIC | Captured Exit price via RPC |
| `pnl_percent` | NUMERIC | Calculated PnL upon close |
| `status` | VARCHAR(20) | `OPEN` or `CLOSED` |

---

## DEX Parsers

| Blockchain | DEX | Identification |
|------------|-----|----------------|
| TON | Ston.fi | Contract opcodes |
| TON | DeDust | Contract opcodes |
| Solana | Jupiter | Program ID |
| Base | Uniswap v3 | Router address |
| Base | 1inch | Aggregator signature |

---

## Deployment

```bash
# Start infrastructure
docker-compose up -d

# Check service health
curl http://localhost:8000/health

# RabbitMQ management UI
open http://localhost:15672  # guest:guest
```

Services startup order:
1. PostgreSQL + TimescaleDB
2. RabbitMQ
3. Redis
4. FastAPI Gateway
5. Workers (parser, copy-trade, bot)

---

## Security & Observability (Phase 9+)

### KMS & Envelope Encryption
Private keys for proxy wallets are encrypted using Envelope Encryption:
- The Master Key is stored securely via AWS KMS (`KMS_PROVIDER=aws`) or HashiCorp Vault (`KMS_PROVIDER=vault`).
- A Data Encryption Key (DEK) is decrypted at application startup and stored in memory.
- The DEK is used with AES-256-GCM (`cryptography.fernet`) to encrypt/decrypt individual proxy wallet keys in `user_proxy_wallets.encrypted_private_key`.
- In development mode, `KMS_PROVIDER=local` is used for basic Fernet encryption without remote KMS calls.

### Observability
- **Sentry**: Integrated across FastAPI gateway, workers, and bot for unhandled exception capture and stack tracing.
- **Prometheus & Grafana**: 
  - FastAPI Gateway metrics exposed via `prometheus-fastapi-instrumentator` at `/metrics` (port 8000).
  - Queue depth metrics (`rabbitmq_queue_depth`) exposed by the ingestion worker (port 8000).
  - Trade execution latency (`copy_trade_latency_seconds`) exposed by the copy worker (port 8001).

### Resilience Testing
- **Chaos Testing**: Toxiproxy (`tests/test_chaos.py`) simulates RabbitMQ/PostgreSQL network failures, verifying that asynchronous workers gracefully retry or requeue failed executions.
- **Load Testing**: Locust (`locustfile.py`) simulates 1000+ concurrent webhook ingests to ensure sub-200ms API latency SLAs.

---

## Frontend & E2E Testing (Phase 12+)

- **Framework**: Playwright is used for End-to-End (E2E) testing.
- **Viewport**: Tests execute via a simulated mobile viewport (`320px x 600px`) natively mimicking Telegram Mini App runtime resolution constraints.
- **Auth Mocking**: TMA environments are stubbed directly in `/frontend/src/utils/mockTelegram.ts` permitting auth tests to proceed completely offline without an active Telegram client session.
- **CI/CD Integration**: Playwright test suites act as gatekeepers for pull requests, executed automatically via GitHub Actions `.github/workflows/e2e-tests.yml`.
