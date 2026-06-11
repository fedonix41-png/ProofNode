# ASW Plan: ProofNode Phase 7 - Hardening, Observability & Production Deployment

## TL;DR
Prepare **ProofNode** for a secure production deployment. Replace the local symmetric encryption mock in `kms.py` with AWS KMS (using envelope encryption for database Data Encryption Keys) or HashiCorp Vault. Integrate Sentry exception tracking, Prometheus metrics, and Grafana dashboards. Build load testing suites using Locust and chaos resilience testing using Toxiproxy. Configure production Docker settings.

---

## Objective
To harden the system, guarantee high availability, and secure wallet credentials:
1. Implement a production-grade Key Management Service (KMS) provider wrapper supporting AWS KMS (`boto3`) or HashiCorp Vault (`hvac`) using envelope encryption (master key encrypts/decrypts database data keys).
2. Integrate Sentry for exception capturing and alert aggregation across the gateway, parser worker, copy worker, and Telegram bot.
3. Configure Prometheus metrics instrumentation (request rates, queue sizes, database connections, trade mirroring latency) and draft a Grafana dashboard specification.
4. Setup Chaos resilience tests (Toxiproxy) in pytest to verify database and message broker reconnect strategies.
5. Create a Locust load test configuration to validate the webhook gateway can process 1000 requests/sec under the 200ms latency SLA.
6. Assemble a production Docker orchestration compose file (`docker-compose.prod.yml`) with HTTPS, logs rotation, and database replica support.

---

## Non-Goals
- Performing penetration testing or smart contract audits.
- Configuring cloud network VPC details or DNS zone delegations.

---

## Decision Summary
- **Envelope Encryption Model**:
  - The database contains `user_proxy_wallets.encrypted_private_key`.
  - We store an encrypted Data Encryption Key (DEK) in backend configuration.
  - At startup, the server requests AWS KMS to decrypt the DEK.
  - The decrypted DEK is kept only in server RAM and used with symmetric encryption (AES-256-GBC) to encrypt and decrypt user proxy wallet keys. This minimizes round-trip latency to AWS KMS.
- **Monitoring Tools**:
  - **Sentry**: Python SDK (`sentry-sdk`) with integrations for FastAPI, SQLAlchemy/asyncpg, and Aio-pika.
  - **Prometheus**: `prometheus-fastapi-instrumentator` for FastAPI, and custom gauges for workers.
- **Resilience Testing**:
  - Use Toxiproxy containers to mock flaky networks (TCP lag, socket closing) between database/RabbitMQ and the workers during pytest execution.

---

## Files to Edit & Create

### [MODIFY] Configuration & Dependencies
- [requirements.txt](file:///home/ozzy/Документы/ProofNode/backend/requirements.txt) - Add `boto3`, `hvac`, `sentry-sdk`, `prometheus-fastapi-instrumentator`, `locust`, `toxiproxy`.
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Add settings for `KMS_PROVIDER` (`AWS` / `VAULT` / `LOCAL`), `AWS_KMS_KEY_ID`, `SENTRY_DSN`, `PROMETHEUS_ENABLED`.

### [MODIFY] Core Services & Entrypoints
- [kms.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/kms.py) - Implement the real AWS KMS and Vault providers with envelope encryption fallback logic.
- [main.py](file:///home/ozzy/Документы/ProofNode/backend/app/main.py) - Initialize Sentry and mount the `/metrics` endpoint.
- [worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/worker.py) & [copy_worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/copy_worker.py) - Initialize Sentry and expose background prometheus metric ports.
- [bot/main.py](file:///home/ozzy/Документы/ProofNode/bot/main.py) - Initialize Sentry.

### [NEW] Chaos and Load Testing
- [test_chaos.py](file:///home/ozzy/Документы/ProofNode/tests/test_chaos.py) - pytest suite running tests through Toxiproxy to verify backend/workers gracefully retry on db or queue connection drops.
- [locustfile.py](file:///home/ozzy/Документы/ProofNode/locustfile.py) - Load test file simulating massive webhook ingestion traffic.

### [NEW] Production Infrastructure
- [docker-compose.prod.yml](file:///home/ozzy/Документы/ProofNode/docker-compose.prod.yml) - Production multi-container structure including TLS reverse-proxy (Caddy/Nginx), Prometheus, Grafana, timescaledb-replica, and production-configured RabbitMQ.

---

## TODOs

- [ ] **Dependencies Expansion**
  - Add production packages to `backend/requirements.txt`: `boto3`, `hvac`, `sentry-sdk[fastapi]`, `prometheus-fastapi-instrumentator`, `locust`, `toxiproxy`.
  - Install dependencies: `uv pip install -r backend/requirements.txt`.
  - Configure production variables in `backend/app/config.py`.
  - *Commit guidance*: "infra: define production dependencies for security and observability"

- [ ] **Production Key Management Service (KMS)**
  - Rewrite `backend/app/services/kms.py`:
    - Define an abstract `KMSProvider` class.
    - Implement `LocalKMSProvider` (current Fernet mock).
    - Implement `AWSKMSProvider` using `boto3` client to decrypt the encrypted Data Encryption Key (DEK). Use the decrypted DEK in memory with `cryptography.fernet` or `AES-GBC` to encrypt/decrypt private keys.
    - Implement `VaultKMSProvider` using `hvac` client to read keys from Vault's transit secrets engine.
  - *Commit guidance*: "feat: implement envelope encryption with AWS KMS and HashiCorp Vault"

- [ ] **Exception Tracking & Metrics Instrumentation**
  - Integrate Sentry in `backend/app/main.py`, workers, and `bot/main.py` by calling `sentry_sdk.init()`.
  - Integrate Prometheus metrics inside the FastAPI gateway using `Instrumentator().instrument(app).expose(app)`.
  - Create custom metrics (e.g. `mirrored_trade_latency_seconds`) in `copy_worker.py` and export them.
  - *Commit guidance*: "feat: integrate Sentry exception tracking and Prometheus metrics"

- [ ] **Chaos Resilience Integration Tests**
  - Create `tests/test_chaos.py` using Toxiproxy:
    - Launch Toxiproxy containers for Postgres and RabbitMQ.
    - Route client connections through the proxy ports.
    - Introduce packet delay, jitter, and connection cuts during a mock trade copying sequence.
    - Assert that FastAPI and workers retry and successfully complete the trades when connections restore.
  - *Commit guidance*: "test: add chaos resilience tests with Toxiproxy"

- [ ] **Load Stress Testing**
  - Create `locustfile.py` to:
    - Simulate 1000 users sending webhook HTTP POST requests with mock signatures.
    - Monitor request failure rate and response times.
  - *Commit guidance*: "test: add Locust load testing script for gateway"

- [ ] **Production Docker Orchestration**
  - Create `docker-compose.prod.yml` configuring:
    - Secure postgres volume permissions.
    - RabbitMQ user accounts and partition handling.
    - Reverse-proxy (e.g. Caddy) with automatic Let's Encrypt SSL generation.
    - Prometheus container and Grafana dashboard templates.
  - *Commit guidance*: "infra: create production docker-compose configuration"

---

## QA Scenarios

### Scenario 1: Load Test Ingestion SLA Verification
- **Command**:
  - Start services locally in dev mode:
    ```bash
    docker compose up -d
    ```
  - Run Locust headless stress test for 1 minute:
    ```bash
    uv run locust -f locustfile.py --headless -u 100 -r 20 --run-time 1m --host http://127.0.0.1:8000
    ```
- **Expected Evidence**:
  - The console summary shows 0% failure rate and P99 response time is `< 200ms`.

### Scenario 2: Chaos Recovery Assertion
- **Command**:
  - Run the chaos test suite:
    ```bash
    PYTHONPATH=. uv run pytest tests/test_chaos.py -v
    ```
- **Expected Evidence**:
  - Tests succeed, proving that connection loss to RabbitMQ/TimescaleDB is recovered by the workers.

### Cleanup Receipt
- **Command**:
  ```bash
  docker compose down -v
  ```
- **Expected Evidence**:
  - All temporary testing containers and networks are stopped and purged.

---

## Privacy & Package Safeguards
- Sentry configurations must filter out sensitive user data, decrypted keys, or private payload details.
- Never expose Prometheus metrics `/metrics` routes containing system secrets.

Next: `start-work proofnode_phase7`
