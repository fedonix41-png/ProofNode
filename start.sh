#!/bin/bash

# ==============================================================================
# ProofNode Development Startup Script
# ==============================================================================

# Цвета для вывода в консоль
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting ProofNode local development stack...${NC}"

# Создаем папки для логов и PID
mkdir -p logs
mkdir -p .pids

# 1. Запуск Docker инфраструктуры (PostgreSQL, Redis, RabbitMQ, Cloudflared)
echo -e "${BLUE}🐳 Spinning up Docker containers (DB, Redis, RabbitMQ, Cloudflared)...${NC}"
docker compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start Docker containers. Check your docker installation.${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Waiting 5 seconds for databases and RabbitMQ to initialize...${NC}"
sleep 5

# 2. Запуск Backend (FastAPI)
echo -e "${BLUE}🐍 Starting FastAPI Backend on http://localhost:8000...${NC}"
PYTHONUNBUFFERED=1 PYTHONPATH=. nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 < /dev/null &
BACKEND_PID=$!
echo $BACKEND_PID > .pids/backend.pid
echo -e "${GREEN}✔ Backend started (PID: $BACKEND_PID, logs -> logs/backend.log)${NC}"

# 3. Запуск Telegram Bot
echo -e "${BLUE}🤖 Starting Telegram Bot...${NC}"
PYTHONUNBUFFERED=1 PYTHONPATH=. nohup .venv/bin/python bot/main.py > logs/bot.log 2>&1 < /dev/null &
BOT_PID=$!
echo $BOT_PID > .pids/bot.pid
echo -e "${GREEN}✔ Telegram Bot started (PID: $BOT_PID, logs -> logs/bot.log)${NC}"

# 4. Запуск Frontend (Vite)
echo -e "${BLUE}⚛ Starting Frontend (Vite) on http://localhost:5173...${NC}"
cd frontend
nohup ./node_modules/.bin/vite > ../logs/frontend.log 2>&1 < /dev/null &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.pids/frontend.pid
cd ..
echo -e "${GREEN}✔ Frontend started (PID: $FRONTEND_PID, logs -> logs/frontend.log)${NC}"

# Отвязываем фоновые процессы, чтобы они не завершались при выходе скрипта
disown -a

echo -e "\n${GREEN}🎉 All services are up and running!${NC}"
echo -e "💡 Use ${YELLOW}./stop.sh${NC} to stop all services."
echo -e "📝 To view logs, run: ${BLUE}tail -f logs/backend.log logs/bot.log logs/frontend.log${NC}\n"
