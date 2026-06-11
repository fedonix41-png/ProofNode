# ASW Plan: ProofNode Phase 9 - Production Hardening & Observability

## TL;DR
Harden ProofNode for production deployment. Replace local Fernet encryption with AWS KMS or HashiCorp Vault using envelope encryption. Integrate Sentry for exception tracking and Prometheus for metrics. Add load testing with Locust and chaos resilience testing with Toxiproxy. Prepare production Docker orchestration.

---

## Objective
To secure wallet credentials and guarantee production readiness:
1. Implement production-grade KMS provider wrapper supporting AWS KMS (`boto3`) or HashiCorp Vault (`hvac`) with envelope encryption.
2. Integrate Sentry for exception capturing across gateway, workers, and bot.
3. Configure Prometheus metrics instrumentation for request rates, queue depths, and trade latency.
4. Build chaos resilience tests verifying database and message broker reconnection.
5. Create Locust load test validating 1000 req/sec under 200ms latency SLA.
6. Assemble production Docker Compose with TLS, log rotation, and database read replicas.

---

## Non-Goals
- Penetration testing or smart contract audits.
- Cloud VPC network configuration or DNS zone delegation.
- CI/CD pipeline setup (separate task).

---

## Decision Summary
- **Envelope Encryption Model**:
  - Master Key stored in AWS KMS or Vault.
  - Data Encryption Key (DEK) encrypted and stored in environment/config.
  - At startup, server requests KMS to decrypt DEK.
  - Decrypted DEK kept only in RAM, used for AES-256-GCM encryption/decryption of proxy wallet private keys.
- **Monitoring Stack**:
  - Sentry: `sentry-sdk[fastapi]` for gateway, manual init for workers/bot.
  - Prometheus: `prometheus-fastapi-instrumentator` for `/metrics` endpoint.
  - Custom metrics: queue size gauges, trade latency histograms.
- **Resilience Testing**:
  - Toxiproxy sits between services and Postgres/RabbitMQ during tests.
  - Tests introduce latency, connection drops, and verify graceful recovery.
- **Load Testing**:
  - Locust simulates concurrent webhook ingestion with valid signatures.
  - Target: 1000 users, 0% failure rate, P99 < 200ms.

---

## Files to Edit & Create

### [MODIFY] Configuration & Dependencies
- [requirements.txt](file:///home/ozzy/Документы/ProofNode/backend/requirements.txt) - Add `boto3`, `hvac`, `sentry-sdk[fastapi]`, `prometheus-fastapi-instrumentator`, `locust`, `toxiproxy-python`.
- [config.py](file:///home/ozzy/Документы/ProofNode/backend/app/config.py) - Add `KMS_PROVIDER` (`aws`/`vault`/`local`), `AWS_KMS_KEY_ID`, `VAULT_URL`, `VAULT_TOKEN`, `SENTRY_DSN`, `PROMETHEUS_ENABLED`.

### [MODIFY] Services
- [kms.py](file:///home/ozzy/Документы/ProofNode/backend/app/services/kms.py) - Implement abstract `KMSProvider` class with `LocalKMSProvider`, `AWSKMSProvider`, `VaultKMSProvider` implementations.

### [MODIFY] Entrypoints
- [main.py](file:///home/ozzy/Документы/ProofNode/backend/app/main.py) - Initialize Sentry, mount Prometheus `/metrics` endpoint.
- [worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/worker.py) - Initialize Sentry, expose metrics on separate port.
- [copy_worker.py](file:///home/ozzy/Документы/ProofNode/backend/app/copy_worker.py) - Initialize Sentry, add trade latency histogram metric.
- [bot/main.py](file:///home/ozzy/Документы/ProofNode/bot/main.py) - Initialize Sentry.

### [NEW] Testing
- [test_chaos.py](file:///home/ozzy/Документы/ProofNode/tests/test_chaos.py) - Chaos tests using Toxiproxy for connection failure scenarios.
- [locustfile.py](file:///home/ozzy/Документы/ProofNode/locustfile.py) - Load test configuration for webhook endpoint.

### [NEW] Infrastructure
- [docker-compose.prod.yml](file:///home/ozzy/Документы/ProofNode/docker-compose.prod.yml) - Production orchestration with Caddy/Traefik, Prometheus, Grafana, TimescaleDB replica.
- [prometheus.yml](file:///home/ozzy/Документы/ProofNode/prometheus.yml) - Prometheus scrape configuration.
- [grafana/dashboards/proofnode.json](file:///home/ozzy/Документы/ProofNode/grafana/dashboards/proofnode.json) - Grafana dashboard JSON.

---

## TODOs

- [ ] **Dependencies Expansion**
  - Add to `requirements.txt`:
    ```
    boto3>=1.28.0
    hvac>=2.0.0
    sentry-sdk[fastapi]>=1.40.0
    prometheus-fastapi-instrumentator>=7.0.0
    locust>=2.20.0
    toxiproxy-python>=0.6.0
    ```
  - Install: `uv pip install -r backend/requirements.txt`.
  - *Commit guidance*: "infra: add production security and observability dependencies"

- [ ] **KMS Provider Implementation**
  - Update `backend/app/services/kms.py`:
    - Define `KMSProvider` abstract base class with `encrypt(plaintext)` and `decrypt(ciphertext)`.
    - Implement `LocalKMSProvider` (current Fernet implementation for dev).
    - Implement `AWSKMSProvider`:
      - Use `boto3.client('kms')` to decrypt DEK at startup.
      - Store decrypted DEK in memory.
      - Use `cryptography.fernet` or AES-GCM for data encryption.
    - Implement `VaultKMSProvider`:
      - Use `hvac.Client` with transit secrets engine.
  - Add factory function `get_kms_provider()` based on `KMS_PROVIDER` setting.
  - *Commit guidance*: "feat: implement envelope encryption with AWS KMS and Vault"

- [ ] **Sentry Integration**
  - Add to `backend/app/main.py`:
    ```python
    import sentry_sdk
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[FastAPIIntegration()])
    ```
  - Add to `worker.py`, `copy_worker.py`, `bot/main.py`:
    ```python
    import sentry_sdk
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn)
    ```
  - *Commit guidance*: "feat: integrate Sentry exception tracking"

- [ ] **Prometheus Metrics**
  - Add to `backend/app/main.py`:
    ```python
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    ```
  - Add custom metrics to `copy_worker.py`:
    ```python
    from prometheus_client import Histogram
    TRADE_LATENCY = Histogram('copy_trade_latency_seconds', 'Time to execute copy trade')
    ```
  - Add queue depth gauge in `worker.py`:
    ```python
    from prometheus_client import Gauge
    QUEUE_DEPTH = Gauge('rabbitmq_queue_depth', 'Messages in queue', ['queue'])
    ```
  - *Commit guidance*: "feat: add Prometheus metrics instrumentation"

- [ ] **Chaos Resilience Tests**
  - Create `tests/test_chaos.py`:
    - Spin up Toxiproxy containers via Docker.
    - Route Postgres/RabbitMQ connections through proxy.
    - Introduce 500ms latency during message processing.
    - Cut connection mid-processing.
    - Assert workers retry and complete after connection restore.
  - *Commit guidance*: "test: add chaos resilience tests with Toxiproxy"

- [ ] **Load Test Configuration**
  - Create `locustfile.py`:
    ```python
    from locust import HttpUser, task, between
    import hmac
    import hashlib
    
    class WebhookUser(HttpUser):
        wait_time = between(0.01, 0.05)
        
        @task
        def send_webhook(self):
            payload = '{"tx_hash": "test", "wallet_address": "test", "time": "2024-01-01T00:00:00Z", "payload": ""}'
            sig = hmac.new(b'test_secret', payload.encode(), hashlib.sha256).hexdigest()
            self.client.post("/gateway/ton", payload, headers={"X-Tonapi-Signature": sig})
    ```
  - *Commit guidance*: "test: add Locust load testing configuration"

- [ ] **Production Docker Compose**
  - Create `docker-compose.prod.yml`:
    - Caddy/Traefik reverse proxy with auto-HTTPS.
    - Prometheus container with scrape config.
    - Grafana with preconfigured dashboard.
    - TimescaleDB primary + read replica.
    - RabbitMQ with durable queues.
    - Log rotation and resource limits.
  - *Commit guidance*: "infra: create production docker-compose configuration"

- [ ] **Grafana Dashboard**
  - Create `grafana/dashboards/proofnode.json`:
    - Request rate panel.
    - Error rate panel.
    - Queue depth panel.
    - Trade latency histogram.
    - Database connection pool usage.
  - *Commit guidance*: "infra: add Grafana dashboard for ProofNode"

---

## QA Scenarios

### Scenario 1: Load Test SLA Verification
- **Command**:
  ```bash
  docker compose -f docker-compose.prod.yml up -d
  sleep 10
  uv run locust -f locustfile.py --headless -u 1000 -r 50 --run-time 30s --host http://127.0.0.1:8000
  ```
- **Expected Evidence**: Console output shows 0% failure rate and P99 latency < 200ms.

### Scenario 2: Chaos Recovery Test
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_chaos.py -v
  ```
- **Expected Evidence**: All tests pass, showing workers recover from connection loss.

### Scenario 3: Sentry Error Capture
- **Command**:
  - Trigger a deliberate error in the running application.
  - Check Sentry dashboard for error event.
- **Expected Evidence**: Error appears in Sentry with stack trace and context.

### Scenario 4: KMS Decryption Flow
- **Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_kms_provider.py -v
  ```
- **Expected Evidence**: Tests pass for local and mocked AWS/Vault providers.

### Cleanup Receipt
- **Command**: `docker compose -f docker-compose.prod.yml down -v`
- **Expected Evidence**: All containers and volumes stopped and removed.

---

## Privacy & Package Safeguards
- Filter sensitive data from Sentry events: private keys, wallet addresses, transaction payloads.
- Never expose `/metrics` endpoint publicly without authentication.
- Use least-privilege IAM roles for AWS KMS access.
- Store Vault tokens in secure environment variables, never in code.

---

## Summary: Revised Phase Order

| Phase | Focus | Status |
|-------|-------|--------|
| 6 | Webhook security, RPC pools, CRM features, public profiles, freemium | Ready |
| 7 | Referral program, B2C premium, commission transfers, growth hooks | Ready |
| 8 | DEX aggregators, transaction signing, copy-trade execution | Ready |
| 9 | KMS/Vault, Sentry, Prometheus, load/chaos testing, production Docker | Ready |

This order follows the original ТЗ priority: core value → monetization → advanced features → production hardening.
