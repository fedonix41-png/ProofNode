#!/bin/bash

# ==============================================================================
# ProofNode Development Shutdown Script
# ==============================================================================

# Цвета для вывода в консоль
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping ProofNode local development services...${NC}"

# 1. Останавливаем процессы по сохраненным PID
if [ -d .pids ]; then
    for service in backend bot frontend; do
        if [ -f .pids/$service.pid ]; then
            PID=$(cat .pids/$service.pid)
            if ps -p $PID > /dev/null; then
                echo -e "${YELLOW}Stopping $service (PID: $PID)...${NC}"
                kill $PID
                sleep 0.5
                # Если процесс не умер, убиваем принудительно
                if ps -p $PID > /dev/null; then
                    kill -9 $PID
                fi
            fi
            rm .pids/$service.pid
        fi
    done
fi

# 2. Запасной вариант: убиваем зависшие процессы по именам/портам
echo -e "${YELLOW}Cleaning up any orphaned backend/frontend processes...${NC}"
pkill -f "uvicorn backend.app.main:app" 2>/dev/null
pkill -f "python bot/main.py" 2>/dev/null
pkill -f "node_modules/.bin/vite" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Освобождаем порты, если они остались заняты
fuser -k 8000/tcp 2>/dev/null
fuser -k 5173/tcp 2>/dev/null

echo -e "${GREEN}✔ Local processes stopped.${NC}"

# 3. Останавливаем Docker-контейнеры
echo -e "${BLUE}🐳 Stopping Docker containers...${NC}"
docker compose down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✔ Docker containers stopped.${NC}"
else
    echo -e "${RED}⚠ Failed to stop some Docker containers automatically. Try running 'docker compose down' manually.${NC}"
fi

# Удаляем временную папку PID
rm -rf .pids

echo -e "\n${GREEN}✨ Shutdown complete! All ProofNode services have been stopped.${NC}\n"
