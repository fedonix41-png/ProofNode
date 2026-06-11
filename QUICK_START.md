# ProofNode (AlphaHub)

ProofNode is a decentralized on-chain social trading and secure copy-trading protocol implemented as a Telegram Mini App (TMA). It provides zero-fraud verification of VIP signal channels and enables 1-Click & Automated Copy-Trading for retail investors.

## Documentation
- [Agent Context & Root Docs](AGENTS.md)
- [Architecture & Overview](docs/README.md)
- [Security Model (KMS/SSS)](docs/security.md)
- [Technical Specifications](docs/technical.md)

## Development Setup

The project uses `uv` for Python dependency management and Docker for infrastructure.

### 1. Start Infrastructure
Spin up PostgreSQL (TimescaleDB), RabbitMQ, and Redis:
```bash
docker compose up -d
```

### 2. Backend & Worker Setup
Install dependencies and activate virtual environment:
```bash
uv venv
uv pip install -r backend/requirements.txt
```

Run tests to verify the core systems (Gateway, Event Parser, Copy Worker, SSS crypto, Bot Paywall):
```bash
PYTHONPATH=. uv run pytest -v
```

### 3. Frontend Development
Run the React 19 Telegram Mini App locally:
```bash
cd frontend
npm install
npm run dev
```

## Current Status
- **Phases 1-5 (Backend, Crypto, Queues, Bot)** are fully implemented and verified with 100% test coverage.
- **Phase 6** (Mainnet DEX integrations) is pending.
