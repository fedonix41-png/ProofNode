# ProofNode Documentation (SSOT)

## Vision
ProofNode is a decentralized Web3 trust protocol and investment co-pilot in Telegram. It substitutes manual signal entry with **Proof-of-Trade** (on-chain trade verification) and replaces manual order entry with **1-Click / Automated Copy-Trading**.

## System Architecture
The backend uses an event-driven architecture designed to handle thousands of transactions per second with minimal latency.

- **Webhook Gateway (FastAPI):** Receives webhooks from blockchain indexers (TonAPI, Helius, Alchemy), validates signatures, and enqueues to RabbitMQ without blocking.
- **Message Broker (RabbitMQ):**
  - `raw_blockchain_events`
  - `processed_swaps`
  - `copy_trade_execution`
  - `tg_bot_notifications`
- **Workers:**
  - **Event Parser:** Decodes DEX contracts (Ston.fi, Jupiter, 1inch) and logs to TimescaleDB.
  - **Copy-Trade Execution:** Executes automated trades via encrypted proxy wallets.
  - **Bot Worker:** Manages Telegram channel access, invite link generation, and billing verifications.

## Data Storage
- **PostgreSQL (Relational):** Users, trader profiles, tariffs, subscriptions, encrypted proxy keys, and SSS shares.
- **TimescaleDB (Time-series):** `wallet_transactions` and `trader_pnl_history`. Utilizes 7-day chunking, compression after 14 days, and 90-day retention policies.

## Key Concepts
- **Proof-of-Trade:** Directly links a signal channel's subscription paywall to the admin's on-chain trading address, providing transparent ROI and win rates.
- **Trace ID & Logical Time (lt):** Used to properly sequence asynchronous TON smart contract messages.

*For security details on wallet encryption and SSS, see [security.md](./security.md).*
*For environment variables, API contracts, and deployment, see [technical.md](./technical.md).*
