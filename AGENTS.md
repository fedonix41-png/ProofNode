# ProofNode Agent Context

Use this file as the Single Source of Truth (SSOT) for understanding the ProofNode project architecture and agent guidelines.

## Project Overview
ProofNode (formerly AlphaHub) is a decentralized on-chain social trading and secure copy-trading protocol implemented as a Telegram Mini App (TMA). It verifies trades on-chain (Proof-of-Trade) and allows 1-Click / Automated Copy-Trading for retail investors following VIP signal channels.

## Tech Stack
- **Backend:** Python 3.13, FastAPI, Pydantic v2
- **Database:** PostgreSQL 15 + TimescaleDB (for transactions/ROI time series)
- **Cache & Broker:** Redis, RabbitMQ
- **Bot:** Telegram Bot API via `aiogram` v3
- **Frontend (Phase 4):** React 19, Vite, TailwindCSS v4, Telegram Mini App SDK
- **Environment:** `uv` for Python dependency management, Docker for isolated local development

## Core Architecture
- **Stateless Webhook Gateway:** Ingests webhooks from TonAPI, Helius (Solana), Alchemy (Base) and pushes to RabbitMQ `raw_blockchain_events`.
- **Event Parser Worker:** Decodes DEX swaps (Ston.fi, DeDust, Jupiter, 1inch) and writes to TimescaleDB.
- **Copy-Trade Execution Worker:** Consumes `copy_trade_execution` jobs, decrypts proxy wallet keys via KMS, quotes DEX routes, and simulates execution.
- **Bot Manager:** Manages B2B subscriptions (Telegram Stars/TON), automatically generates invite links, and kicks expired members from channels.

## Security Model (Hybrid Copy-Trading)
1. **1-Click Copy-Trading (Non-Custodial):** Uses Shamir's Secret Sharing (SSS) 2-of-3. Client holds Share 1, Server DB holds Share 2. Reconstructed in-memory (WASM) on the client.
2. **Automated Cloud Copy-Trading:** Custodial proxy wallets with strictly limited budgets. Private keys are encrypted via KMS (`cryptography.fernet` stub in dev) and decrypted in-memory by the Execution Worker.

## Technical References
- **[docs/technical.md](file:///home/ozzy/Документы/ProofNode/docs/technical.md)**: Contains critical low-level implementation details including Environment Variables, Webhook JSON payloads, RabbitMQ message schemas, and exact PostgreSQL/TimescaleDB table structures. Agents should read this file before implementing database models or message consumers.

## Coding Guidelines (ASW)
- Follow `asw-comment-check`: Keep comments explaining *why*, constraints, non-obvious algorithms, and operational hazards. Remove redundant comments. Do not add AI-generated section banners.
- Follow `asw-programming`: Strict implementation discipline.
- Use `uv` for all Python dependency management.
- All backend code must be compatible with async execution where applicable.
