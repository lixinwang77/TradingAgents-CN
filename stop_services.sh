#!/bin/bash
# TradingAgents-CN Service Stop Script
# This script stops all running services

echo "=========================================="
echo "TradingAgents-CN Service Shutdown"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop Frontend
echo -n "Stopping Frontend... "
if pgrep -f "vite" > /dev/null; then
    tmux -f /exec-daemon/tmux.portal.conf kill-session -t frontend-server 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    sleep 1
    if pgrep -f "vite" > /dev/null; then
        echo -e "${RED}✗ Failed to stop${NC}"
    else
        echo -e "${GREEN}✓ Stopped${NC}"
    fi
else
    echo -e "${YELLOW}✗ Not running${NC}"
fi

# Stop Backend
echo -n "Stopping Backend... "
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    tmux -f /exec-daemon/tmux.portal.conf kill-session -t backend-server 2>/dev/null || true
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 1
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "${RED}✗ Failed to stop${NC}"
    else
        echo -e "${GREEN}✓ Stopped${NC}"
    fi
else
    echo -e "${YELLOW}✗ Not running${NC}"
fi

# Stop Redis
echo -n "Stopping Redis... "
if pgrep -x "redis-server" > /dev/null; then
    redis-cli shutdown 2>/dev/null || pkill redis-server 2>/dev/null || true
    sleep 1
    if pgrep -x "redis-server" > /dev/null; then
        echo -e "${RED}✗ Failed to stop${NC}"
    else
        echo -e "${GREEN}✓ Stopped${NC}"
    fi
else
    echo -e "${YELLOW}✗ Not running${NC}"
fi

# Stop MongoDB
echo -n "Stopping MongoDB... "
if pgrep -x "mongod" > /dev/null; then
    pkill mongod 2>/dev/null || true
    sleep 2
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${RED}✗ Failed to stop${NC}"
    else
        echo -e "${GREEN}✓ Stopped${NC}"
    fi
else
    echo -e "${YELLOW}✗ Not running${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ All services stopped${NC}"
echo "=========================================="
echo ""
echo "To start services again, run: ./start_services.sh"
echo ""
