# ASW Plan: ProofNode Phase 1 - Core Infrastructure & Webhook Ingestion Pipeline

## TL;DR
Establish the foundational backend, database, and messaging infrastructure for **ProofNode** (decentralized on-chain social trading and secure copy-trading protocol). This phase sets up the local Docker environment, TimescaleDB/PostgreSQL schemas, a stateless FastAPI Webhook Ingestion Gateway, a message parser worker, and an integration test suite using Testcontainers. All Python work will be executed within a virtual environment managed by `uv`.

---

## Objective
To build a highly robust, secure, event-driven backend shell that:
1. Receives webhooks from blockchain indexers (TON, Solana, Base) with payload signature checking.
2. Enqueues raw payloads into RabbitMQ.
3. Spawns an event parser worker to decode swaps and record transactions to TimescaleDB hypertables.
4. Validates database, cache, and queue states using automated integration testing (Testcontainers).
5. Ensures total isolation by running all services in Docker and managing local Python modules inside a `uv` virtual environment.

---

## Non-Goals
- Building the frontend user interface (UI) or visual charts (reserved for Phase 4).
- Implementing copy-trading execution (signing transactions, proxy wallet creation) or KMS key encryption (reserved for Phase 3).
- Setting up final cloud deployment pipelines or production DNS records.
- Creating the production Telegram Bot with full user conversational flows (reserved for Phase 2).

---

## Decision Summary
- **Project Name**: **ProofNode**
- **Language**: Python 3.13 + FastAPI + Pydantic v2.
- **Databases**: PostgreSQL 15 + TimescaleDB for relational structures and optimized timeseries tables; Redis for caching, state, and webhook deduplication.
- **Message Broker**: RabbitMQ for reliable event ingestion.
- **Frontend Tech (Phase 4 preview)**: React 19 + Vite + TailwindCSS v4 + Telegram Mini App SDK.
- **Environment Isolation**: Virtualenv managed via `uv` inside Docker. No packages will be installed on the host OS.
- **Key Security Model**: 
  - 1-Click Copy-Trading: Client-side Shamir's Secret Sharing (SSS) 2-of-3 reconstruction in user's browser/TMA RAM.
  - Automated Cloud Copy-Trading: Dedicated, budget-limited proxy wallets with encrypted keys.
- **Testing**: Pytest + Testcontainers (Docker-in-Docker friendly) to spin up ephemeral containers for Postgres/Timescale, Redis, and RabbitMQ.

---

## Files to Edit & Create

### [NEW] Configuration & Infrastructure
- `docker-compose.yml` - Sets up Postgres/TimescaleDB, RabbitMQ, and Redis for local development.
- `backend/requirements.txt` - Dependency file for FastAPI, RabbitMQ clients, database drivers, and testing tools.
- `database/init_db.sql` - Table definitions, TimescaleDB hypertables, compression, and retention configurations.

### [NEW] FastAPI Webhook Gateway
- `backend/app/config.py` - Environment variable loading via Pydantic settings.
- `backend/app/db.py` - Database connection pool management (asyncpg).
- `backend/app/main.py` - FastAPI entrypoint, router for Webhook endpoints (`/gateway/ton`, `/gateway/sol`, `/gateway/evm`).
- `backend/app/schemas.py` - JSON schema validation for webhooks.

### [NEW] Event Parser Worker
- `backend/app/worker.py` - RabbitMQ queue consumer initialization and event loop.
- `backend/app/parser.py` - Mock/skeleton decoders for TonAPI, Helius, and Alchemy webhook payloads.

### [NEW] Testing Suite
- `tests/conftest.py` - Pytest fixtures utilizing `testcontainers-python` to spin up PostgreSQL, Redis, and RabbitMQ.
- `tests/test_gateway.py` - Integration tests verifying webhook submission, signature validation, and RabbitMQ queuing.
- `tests/test_worker.py` - Integration tests verifying message ingestion, token parse decoding, and TimescaleDB insertion.

---

## TODOs

- [ ] **Infrastructure Setup**
    - Create `docker-compose.yml` with `timescale/timescaledb:latest-pg15`, `rabbitmq:3-management`, and `redis:alpine`.
    - Create `database/init_db.sql` with user/trader schemas and TimescaleDB hypertables under the **ProofNode** name.
    - Validate that docker-compose starts correctly.
    - *Commit guidance*: "infra: set up local docker-compose environment and db schema"

- [ ] **Python Dependency Definition (via uv)**
    - Initialize virtual environment:
      ```bash
      uv venv
      ```
    - Create `backend/requirements.txt` containing `fastapi`, `uvicorn`, `pydantic-settings`, `asyncpg`, `aio-pika`, `redis`, `pytest`, `pytest-asyncio`, `testcontainers[postgres,rabbitmq,redis]`.
    - *Commit guidance*: "infra: define backend python dependencies"

- [ ] **FastAPI Webhook Gateway Development**
    - Create `backend/app/config.py` to manage settings.
    - Create `backend/app/db.py` for connection pooling.
    - Create `backend/app/schemas.py` with payload models.
    - Create `backend/app/main.py` with `/health` and webhook endpoints.
    - Implement webhook signature validation skeleton.
    - *Commit guidance*: "feat: implement fastapi webhook ingestion gateway"

- [ ] **RabbitMQ Ingestion Logic**
    - In `backend/app/main.py`, add RabbitMQ publisher integration that pushes payloads to `raw_blockchain_events` queue.
    - *Commit guidance*: "feat: add rabbitmq producer integration to gateway"

- [ ] **Event Parser Worker Development**
    - Create `backend/app/parser.py` to parse transaction inputs and output structured DEX swaps (token in, token out, volume, etc.).
    - Create `backend/app/worker.py` to consume messages from RabbitMQ, trigger the parser, and write results to the database.
    - *Commit guidance*: "feat: implement blockchain event parser and database writer worker"

- [ ] **Integration Testing Suite**
    - Create `tests/conftest.py` with Testcontainers.
    - Write `tests/test_gateway.py` to verify API endpoint behavior.
    - Write `tests/test_worker.py` to verify worker parsing and DB insertion logic.
    - Run the test suite under the virtual environment:
      ```bash
      uv run pytest -v
      ```
    - *Commit guidance*: "test: add integration tests with testcontainers"

---

## QA Scenarios

### Scenario 1: Local Docker Cluster Bootup
- **Command**:
  ```bash
  docker compose up -d
  ```
- **Expected Evidence**:
  - `docker compose ps` shows all 3 services (`timescaledb`, `rabbitmq`, `redis`) as "Up (healthy)" or running.
  - Access to RabbitMQ management portal at `http://localhost:15672` is responsive.

### Scenario 2: Webhook Endpoint Health & Processing
- **Command**:
  - Spin up FastAPI gateway using `uv`:
    ```bash
    uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
    GATEWAY_PID=$!
    sleep 2
    ```
  - Send dummy transaction payload to TON gateway:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -H "X-Tonapi-Signature: test_sig" \
         -d '{"tx_hash": "ton_tx_123", "wallet_address": "EQC...", "logical_time": 98765, "time": "2026-06-10T22:00:00Z", "payload": "raw_hex_data"}' \
         http://127.0.0.1:8000/gateway/ton
    ```
  - Shut down gateway:
    ```bash
    kill $GATEWAY_PID
    ```
- **Expected Evidence**:
  - Curl returns HTTP code `202 Accepted` with JSON `{"status": "queued", "tx_hash": "ton_tx_123"}`.
  - Gateway logs confirm message successfully published to RabbitMQ exchange.

### Scenario 3: Complete Integration Test Suite Execution
- **Command**:
  ```bash
  uv run pytest -v
  ```
- **Expected Evidence**:
  - Output displays all tests passed: `tests/test_gateway.py::... PASSED` and `tests/test_worker.py::... PASSED`.

### Cleanup Receipt
- **Command**:
  ```bash
  docker compose down -v
  ```
- **Expected Evidence**:
  - All local containers are stopped and deleted.
  - Volumes are removed, leaving a clean environment.

---

## Privacy & Package Safeguards
- Verify that credentials (usernames, passwords) in `docker-compose.yml` and `init_db.sql` are standard development defaults (e.g. `postgres/postgres`).
- Do not check in active API keys or private keys.
- Ensure all test artifacts and databases created during test execution are isolated inside Docker volumes or clean schemas and destroyed on test tear-down.

Next: `start-work proofnode_phase1`
