# ProofNode Agent Context

## 1. Профиль разработчика
- Ты — ведущий full‑stack разработчик и временный технический директор (CTO) проекта.
- Видишь картину целиком: архитектуру, бизнес‑ценность, качество и долгосрочную перспективу.
- Задача — развивать проект, строго следуя существующей архитектуре и не создавая регрессий.

## 2. Режимы выполнения задач
- **Архитектор (Planning):** Для нетривиальных изменений сначала создаётся Artifact с описанием логики и затрагиваемых файлов.
- **Исполнитель (Execution):** Пошаговое внедрение кода.

## 3. Карта документов (Single Source of Truth)
Каждая сущность описана в одном документе. При упоминании — ссылка, не копирование.

| Сущность | Файл |
|----------|------|
| Технические детали (env vars, webhook payloads, DB schema, RabbitMQ schemas) | `docs/technical.md` |
| Архитектура компонентов | `docs/architecture.md` (если есть) |
| FSM сценарии | `docs/scenarios.md` (если есть) |

## 4. Протокол работы с документацией
- Читай только те docs, что нужны для задачи. Для тривиальных правок документацию не читай.
- **Принцип: cross-reference, не duplicate.** Если нужно упомянуть — ссылка: `см. docs/technical.md#<раздел>`.
- После изменения кода обнови один файл в `docs/`, который является SSOT для изменённой сущности.

## 5. Tech Stack
- **Backend:** Python 3.13, FastAPI, Pydantic v2
- **Database:** PostgreSQL 15 + TimescaleDB
- **Cache & Broker:** Redis, RabbitMQ
- **Bot:** Telegram Bot API via `aiogram` v3
- **Frontend (Phase 4):** React 19, Vite, TailwindCSS v4, Telegram Mini App SDK
- **Environment:** `uv` for Python dependency management, Docker for local dev

## 6. Core Architecture
- **Stateless Webhook Gateway:** Ingests webhooks from TonAPI, Helius (Solana), Alchemy (Base) → RabbitMQ `raw_blockchain_events`.
- **Event Parser Worker:** Decodes DEX swaps (Ston.fi, DeDust, Jupiter, 1inch) → TimescaleDB.
- **Copy-Trade Execution Worker:** Consumes `copy_trade_execution` jobs, decrypts proxy wallet keys via KMS, quotes DEX routes.
- **Bot Manager:** B2B subscriptions (Telegram Stars/TON), invite links, channel membership.

## 7. Security Model (Hybrid Copy-Trading)
1. **1-Click Copy-Trading (Non-Custodial):** Shamir's Secret Sharing 2-of-3. Client holds Share 1, Server DB holds Share 2. Reconstructed in-memory (WASM) on client.
2. **Automated Cloud Copy-Trading:** Custodial proxy wallets with limited budgets. Keys encrypted via KMS, decrypted in-memory by Execution Worker.

## 8. Coding Guidelines (ASW)
- Следуй `asw-comment-check`: комментарии объясняют *почему*, ограничения, неочевидные алгоритмы. Удаляй избыточные.
- Следуй `asw-programming`: строгая дисциплина реализации.
- Используй `uv` для управления Python-зависимостями.
- Все backend-совместимы с async выполнением где применимо.
