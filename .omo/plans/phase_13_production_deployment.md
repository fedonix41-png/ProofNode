# Phase 13: Production Deployment

## TL;DR
This plan details Phase 13 of the ProofNode project: taking the full stack (Frontend, Backend, Bot, and Workers) to production.

**Objective:** Create a secure, scalable, and resilient production deployment architecture using Docker Compose, Nginx (or Traefik), and proper secrets management.
**Non-goals:** Setting up Kubernetes or multi-region auto-scaling at this stage. We are sticking to a robust single-node/multi-container Docker deployment.

## Decision Summary
- **Infrastructure:** Docker Compose (combining Postgres/TimescaleDB, Redis, RabbitMQ, Backend API, Bot, Workers, and Frontend).
- **Web Server / Reverse Proxy:** Nginx (serving built frontend static files and proxying `/api` to the backend).
- **Security:** Cloudflare Tunnel or Let's Encrypt for SSL/TLS. Secrets managed via a strict production `.env` securely injected into containers.
- **Frontend Serving:** Multi-stage Docker build for the frontend (build with Node, serve with Nginx alpine).

## Files to Edit / Create
- `docker-compose.prod.yml` (new - production specific configuration)
- `frontend/Dockerfile` (new - multi-stage build)
- `backend/Dockerfile` (update to run via `uvicorn` production workers, removing `--reload`)
- `nginx/nginx.conf` (new - reverse proxy and static serving)
- `scripts/deploy.sh` (new - convenience deployment script)
- `docs/deployment.md` (new - SSOT for deployment instructions)

## TODOs

- [ ] **1. Create Frontend Dockerfile**
  - Implement a multi-stage Docker build: Stage 1 (`npm run build`), Stage 2 (Nginx to serve `dist/`).
- [ ] **2. Configure Nginx Reverse Proxy**
  - Create `nginx.conf` to serve frontend static files on `/`.
  - Proxy requests starting with `/api/` to the backend container (port 8000).
- [ ] **3. Create Production Docker Compose**
  - Create `docker-compose.prod.yml`.
  - Define services: `db` (TimescaleDB), `redis`, `rabbitmq`, `backend`, `worker`, `bot`, `frontend` (Nginx).
  - Ensure networks are isolated appropriately (only Nginx exposed to host).
  - Setup persistent named volumes for DB, Redis, and RabbitMQ data.
- [ ] **4. Optimize Backend and Bot for Production**
  - Update backend command to run with multiple worker processes (e.g., `uvicorn main:app --workers 4`).
  - Disable debug modes and `--reload` flags.
- [ ] **5. Deployment Scripts & Documentation**
  - Write `scripts/deploy.sh` to automate pulling changes, building images, and running `docker compose -f docker-compose.prod.yml up -d`.
  - Document the required `.env` variables and deployment steps in `docs/deployment.md`.
- [ ] **6. Backup Strategy Configuration**
  - Document or script a cron-based `pg_dump` strategy for PostgreSQL backups.

## QA Scenarios
1. **Production Build Test:**
   - Command: `docker compose -f docker-compose.prod.yml build`
   - Expected Evidence: All images build successfully without development dependencies.
2. **Container Spin-up:**
   - Command: `docker compose -f docker-compose.prod.yml up -d`
   - Expected Evidence: All containers reach `healthy` or `running` state. No crash loops.
3. **End-to-End Routing Test:**
   - Action: Access the host IP or domain on port 80/443.
   - Expected Evidence: The React frontend loads. API requests to `/api/*` successfully reach the backend and return data without CORS errors.
4. **Data Persistence:**
   - Action: Create a user/signal, restart the `db` container, check if data persists.
   - Expected Evidence: Data is retained across container restarts due to volume mapping.

## Next Steps
Next: `start-work .omo/plans/phase_13_production_deployment.md`
