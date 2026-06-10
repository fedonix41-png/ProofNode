# Brainstorming Session Results: Test Architecture for Distributed Systems

**Facilitator:** Mary (📊 Analyst BMad Agent)  
**Date:** 2026-06-10  
**Context:** AlphaHub Distributed Backend (FastAPI, RabbitMQ, TimescaleDB, Redis)

---

## Executive Summary

This document captures the results of the brainstorming session for the test architecture of AlphaHub's distributed transaction processing pipeline. The session explored strategies for testing webhook ingestion robustness, RabbitMQ message brokers, and Redis caches under extreme load and simulated outages.

- **Topic:** Test Architecture for Distributed Systems
- **Techniques Used:** Chaos Engineering, Anti-Solution, SCAMPER Method
- **Total Ideas Generated:** 15
- **Key Themes:** Fault-tolerance, database isolation, silent data loss detection, local persistence fallbacks, and test pipeline performance.

---

## Technique Sections

### 1. Chaos Engineering (Fault-Tolerance & Outage Testing)

Focuses on simulating infrastructure failures and testing how the application behaves when RabbitMQ, Redis, or TimescaleDB are partially or completely unreachable.

**[Chaos #1]: In-Memory SQLite Fallback DB**
- _Concept_: When the primary TimescaleDB connection drops or times out, the FastAPI Webhook Gateway transitions to saving raw incoming transaction JSONs into a local SQLite database (or a RocksDB key-value store). A recovery worker reads the SQLite file and replays transactions once the connection to TimescaleDB is restored.
- _Novelty_: Provides a schema-validated relational buffer with transactional guarantees, ensuring zero data loss during DB maintenance or outages.

**[Chaos #2]: Redis Bloom Filter for Webhook Deduplication**
- _Concept_: To handle network-induced duplicate webhooks from providers during lag spikes, the Gateway uses a Redis Bloom Filter for O(1) checks of transaction hashes/signatures. In the test suite, we simulate a storm of duplicate webhook requests and assert that only one write is executed on the database.
- _Novelty_: Deduplicates transactions without querying the primary database, minimizing database connection pool strain.

**[Chaos #3]: Toxiproxy Network Jitter Emulation**
- _Concept_: We run Toxiproxy in our Docker Compose testing environment between FastAPI, Redis, and RabbitMQ. Tests inject network latency, TCP package drops, and unexpected socket closures to verify that our async clients reconnect and retry without dropping messages.
- _Novelty_: Emulates real-world cloud network instability rather than simple "up/down" container states.

**[Chaos #4]: Dynamic Queue Sharding on Peak Load**
- _Concept_: If the main RabbitMQ queue `raw_blockchain_events` reaches a queue-length bottleneck, the system dynamically routes transactions to sharded sub-queues based on a hash of the token address. Tests verify that the message partitioner routes and processes messages concurrently without order corruption.
- _Novelty_: Prevents viral memecoin launches from bottlenecking the processing of other monitored wallets.

**[Chaos #5]: Read-Only Cache-Aside Availability during DB Outage**
- _Concept_: If TimescaleDB is down but Redis is healthy, the FastAPI read APIs serve trader ROI snapshots directly from Redis cache, appending a `X-Stale-Warning` header to the response. Tests assert that read availability remains at 100% during a simulated database crash.
- _Novelty_: Prioritizes read uptime for frontend users during backend storage outages.

---

### 2. Anti-Solution (Sabotaging the Pipeline to Expose Blind Spots)

Focuses on deliberately sabotaging the system silently to find what tests we must implement to catch silent bugs before they reach production.

**[Sabotage #1]: Silent Queue Poisoning**
- _Concept_: Injecting malformed transaction payloads (e.g., negative amounts or invalid decimals) that bypass simple JSON schema validation but cause incorrect calculations in the PnL processor (without crashing the worker).
- _Novelty_: Forces the implementation of strict business-logic validators inside the parser worker before writing metrics to TimescaleDB.

**[Sabotage #2]: DB Connection Pool Exhaustion Attack**
- _Concept_: We block the `wallet_transactions` table with a mock long-running transaction while sending high-concurrency webhooks to the Gateway. We verify if the connection pool crashes or if FastAPI redirects events to fallback storage.
- _Novelty_: Tests API performance under thread-pool blockages, revealing database deadlock risks.

**[Sabotage #3]: Clock Drift Sabotage on Subscriptions**
- _Concept_: Skewing container clock times in our docker environment. We check if subscription chron jobs mistakenly kick out active members or fail to kick expired members due to time desynchronization.
- _Novelty_: Exposes dependencies on server clock time and forces the use of timezone-aware database NTP sync checks.

**[Sabotage #4]: Slippage Front-Run Emulation**
- _Concept_: We mock a swap transaction payload with a high slippage value (e.g. 50%) and send it to the copy-trade execution engine. We test whether the engine rejects the transaction or executes it, making it vulnerable to MEV bots.
- _Novelty_: Validates transaction safety and front-running protection policies in the copy-trading module.

**[Sabotage #5]: Webhook Signature Replay Attack**
- _Concept_: Storing a valid historic webhook payload (including signature) and resending it 24 hours later to check if the gateway re-executes the trade or rejects it as stale.
- _Novelty_: Forces the integration of timestamp-window validation along with standard cryptographic signature checks.

---

### 3. SCAMPER Method (Optimizing the Testing Pipeline)

Systematic lenses to optimize test environments, dependencies, execution speed, and developer experience.

**[SCAMPER - Substitute]: Testcontainers-Python for DB & Broker**
- _Concept_: Substitute local manual docker setup in pytest with programmatically managed `testcontainers-python` to spin up isolated PostgreSQL, Redis, and RabbitMQ containers for each test session, and tear them down automatically.
- _Novelty_: Eliminates manual Docker maintenance and ensures a clean, isolated database/broker state for every test run.

**[SCAMPER - Combine]: Load and Chaos Testing Combined**
- _Concept_: Combine `locust` (or `k6`) for API load testing with a script that randomly stops RabbitMQ and Redis Docker containers during the load test.
- _Novelty_: Measures actual data recovery rate and processing delay during concurrent outages and high load.

**[SCAMPER - Adapt]: Seed Data Generators from Real Blockchain Traces**
- _Concept_: Adapt real TON and EVM transaction traces downloaded from public explorers and save them as JSON fixtures in the test directory, rather than generating random dummy mock transactions.
- _Novelty_: Guarantees the parser code is tested against realistic blockchain structures.

**[SCAMPER - Modify]: Async Mocking using pytest-asyncio and pytest-mock**
- _Concept_: Modify mock objects to support async context managers and async database transactions.
- _Novelty_: Prevents false passes in async tests where awaits are accidentally skipped.

**[SCAMPER - Eliminate]: Parallel Test Execution with pytest-xdist**
- _Concept_: Eliminate test bottlenecks by using `pytest-xdist` to run tests in parallel across multiple CPU cores, using isolated database schemas (schemas under the same Postgres database) for each worker.
- _Novelty_: Reduces test suite execution time from minutes to seconds, improving developer feedback loops.

---

## Idea Categorization

### Immediate Opportunities (Ready to Implement)
- **[SCAMPER - Substitute]: Testcontainers-Python** — Easy to setup in `conftest.py` for automated local and CI testing.
- **[Chaos #2]: Redis Bloom Filter for Webhook Deduplication** — Simple Redis implementation to avoid double-processing.
- **[SCAMPER - Adapt]: Real Blockchain Traces** — Gathering actual transaction traces from block explorers as fixtures.

### Future Innovations (Requires Development)
- **[Chaos #1]: SQLite Fallback DB** — Needs custom fallback middleware inside FastAPI database dependency injectors.
- **[Sabotage #5]: Webhook Signature Replay Protection** — Cryptographic validation requiring timestamp-window checking.

### Moonshots (Ambitious, Transformative)
- **[Chaos #3]: Toxiproxy Network Jitter Integration** — Advanced chaos engineering testing in CI/CD pipeline to verify auto-reconnection robustness.
- **[Sabotage #4]: Slippage Front-Run Emulation** — Dynamic MEV-protection simulation in the copy-trading module.

---

## Action Planning

### Top 3 Priority Ideas
1. **Priority 1:** [SCAMPER - Substitute] Testcontainers-Python integration.
   - _Rationale:_ Provides a reliable, developer-friendly way to run full integration tests (with real Postgres/Redis/RabbitMQ instances) on any developer machine or Github Runner without manual Docker setup.
   - _Next Steps:_ Install `testcontainers` via pip and write a base `conftest.py` file inside the tests folder.
2. **Priority 2:** [Chaos #2] Redis Bloom Filter for Webhook Deduplication.
   - _Rationale:_ In blockchain integrations, duplicate webhooks are common. An early deduplication layer protects the database connection pool from load.
   - _Next Steps:_ Write the bloom filter check logic in FastAPI routes inside `src/gateway.py`.
3. **Priority 3:** [Sabotage #5] Webhook Signature Replay Protection.
   - _Rationale:_ Crucial for payment security and copy-trading trigger authorization.
   - _Next Steps:_ Implement signature parsing and timestamp-window validation (rejections of webhooks older than 5 minutes).

---

## Reflection & Follow-up

- **What worked well:** The Chaos Engineering and Anti-Solution techniques helped identify critical edge-cases in Web3 indexing, such as duplicate transaction processing and network timeouts.
- **Recommended Follow-up:** Transition to the QA Specialist role to design specific test cases in code for the Priority 1 & Priority 2 items.
