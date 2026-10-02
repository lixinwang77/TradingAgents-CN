#!/bin/bash
# TradingAgents-CN Service Startup Script
# This script starts all required services for running the application on a cloud VM

set -e

echo "=========================================="
echo "TradingAgents-CN Service Startup"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MongoDB is running
echo -n "Checking MongoDB... "
if pgrep -x "mongod" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}✗ Not running, starting...${NC}"
    mongod --dbpath /tmp/mongodb/data --logpath /tmp/mongodb/logs/mongodb.log --port 27017 --bind_ip 127.0.0.1 --fork
    sleep 2
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${GREEN}✓ MongoDB started${NC}"
    else
        echo -e "${RED}✗ Failed to start MongoDB${NC}"
        exit 1
    fi
fi

# Check if Redis is running
echo -n "Checking Redis... "
if pgrep -x "redis-server" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}✗ Not running, starting...${NC}"
    redis-server --bind 127.0.0.1 --port 6379 --daemonize yes
    sleep 1
    if pgrep -x "redis-server" > /dev/null; then
        echo -e "${GREEN}✓ Redis started${NC}"
    else
        echo -e "${RED}✗ Failed to start Redis${NC}"
        exit 1
    fi
fi

# Check if backend is running
echo -n "Checking Backend... "
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}✗ Not running, starting...${NC}"
    cd "$(dirname "$0")"
    tmux -f /exec-daemon/tmux.portal.conf has-session -t backend-server 2>/dev/null || \
        tmux -f /exec-daemon/tmux.portal.conf new-session -d -s backend-server -c "$(pwd)"
    tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 \
        "source env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000" C-m
    sleep 5
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "${GREEN}✓ Backend started${NC}"
    else
        echo -e "${RED}✗ Failed to start backend${NC}"
        exit 1
    fi
fi

# Check if frontend is running
echo -n "Checking Frontend... "
if pgrep -f "vite" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}✗ Not running, starting...${NC}"
    cd "$(dirname "$0")/frontend"
    tmux -f /exec-daemon/tmux.portal.conf has-session -t frontend-server 2>/dev/null || \
        tmux -f /exec-daemon/tmux.portal.conf new-session -d -s frontend-server -c "$(pwd)"
    tmux -f /exec-daemon/tmux.portal.conf send-keys -t frontend-server:0.0 \
        "npm run dev" C-m
    sleep 3
    if pgrep -f "vite" > /dev/null; then
        echo -e "${GREEN}✓ Frontend started${NC}"
    else
        echo -e "${RED}✗ Failed to start frontend${NC}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ All services are running!${NC}"
echo "=========================================="
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "View logs:"
echo "  Backend:  tmux attach-session -t backend-server"
echo "  Frontend: tmux attach-session -t frontend-server"
echo "  (Press Ctrl+B then D to detach)"
echo ""
echo "Stop services:"
echo "  Run: ./stop_services.sh"
echo ""
