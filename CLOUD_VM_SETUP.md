# TradingAgents-CN Cloud VM Setup Guide

This document describes how to run TradingAgents-CN on a cloud VM (like Cursor Cloud Agents) without Docker.

## Quick Start Summary

✅ **Backend**: Running on http://localhost:8000  
✅ **Frontend**: Running on http://localhost:3000  
✅ **MongoDB**: Running on localhost:27017 (no authentication in dev mode)  
✅ **Redis**: Running on localhost:6379 (no password in dev mode)

## System Information

- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.12.3 (required: 3.11+)
- **Node.js**: 22.14.0 (required: 18+)
- **MongoDB**: 8.0.32
- **Redis**: 7.0.15

## Installed Services

All services are running in the background:

1. **MongoDB** - Database for storing stock data, analysis results, and user information
   - Port: 27017
   - Data directory: /tmp/mongodb/data
   - Log file: /tmp/mongodb/logs/mongodb.log
   - Running without authentication for development

2. **Redis** - Cache and session storage
   - Port: 6379
   - Running without password for development

3. **Backend (FastAPI)** - API server
   - Port: 8000
   - Virtual environment: /workspace/TradingAgents-CN/env
   - Running in tmux session: `backend-server`

4. **Frontend (Vue 3 + Vite)** - Web interface
   - Port: 3000
   - Running in tmux session: `frontend-server`

## Start/Stop Commands

### Check Service Status

```bash
# Check all running services
ps aux | grep -E "(mongod|redis-server|uvicorn|vite)" | grep -v grep

# Check MongoDB
mongosh --eval "db.adminCommand('ping')"

# Check Redis
redis-cli ping

# Check backend API
curl http://localhost:8000/

# Check frontend
curl -I http://localhost:3000/
```

### Start Services

```bash
cd /workspace/TradingAgents-CN

# Start MongoDB
mongod --dbpath /tmp/mongodb/data --logpath /tmp/mongodb/logs/mongodb.log --port 27017 --bind_ip 127.0.0.1 --fork

# Start Redis
redis-server --bind 127.0.0.1 --port 6379 --daemonize yes

# Start Backend (in tmux session)
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s backend-server -c /workspace/TradingAgents-CN
tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 'source env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000' C-m

# Start Frontend (in tmux session)
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s frontend-server -c /workspace/TradingAgents-CN/frontend
tmux -f /exec-daemon/tmux.portal.conf send-keys -t frontend-server:0.0 'npm run dev' C-m
```

### Stop Services

```bash
# Stop MongoDB
pkill mongod

# Stop Redis
redis-cli shutdown
# or
pkill redis-server

# Stop Backend
tmux -f /exec-daemon/tmux.portal.conf kill-session -t backend-server
# or
pkill -f "uvicorn app.main:app"

# Stop Frontend
tmux -f /exec-daemon/tmux.portal.conf kill-session -t frontend-server
# or
pkill -f "vite"
```

### View Logs

```bash
# Backend logs (tmux session)
tmux -f /exec-daemon/tmux.portal.conf attach-session -t backend-server

# Frontend logs (tmux session)
tmux -f /exec-daemon/tmux.portal.conf attach-session -t frontend-server

# MongoDB logs
tail -f /tmp/mongodb/logs/mongodb.log

# Detach from tmux: Press Ctrl+B, then D
```

## Environment Configuration

The `.env` file has been created with safe defaults for local development:

- **MongoDB**: No authentication (for dev only)
- **Redis**: No password (for dev only)
- **JWT & CSRF secrets**: Auto-generated secure random values
- **Admin password**: `admin123` (change after first login)
- **Debug mode**: Enabled
- **Data source**: AKShare (free, no API key required)

### Required Secrets (User Must Provide)

The following API keys are **NOT included** in the `.env` file and must be provided by the user for full functionality:

1. **AI Model API Keys** (at least one required for AI analysis features):
   - `DEEPSEEK_API_KEY` - DeepSeek V3 (recommended, cost-effective)
     - Get from: https://platform.deepseek.com/
   - `DASHSCOPE_API_KEY` - Alibaba Tongyi Qianwen (Chinese, stable)
     - Get from: https://dashscope.aliyun.com/
   - `OPENAI_API_KEY` - OpenAI GPT models
     - Get from: https://platform.openai.com/

2. **Stock Data API Keys** (optional, for advanced features):
   - `TUSHARE_TOKEN` - Professional Chinese stock market data
     - Get from: https://tushare.pro/weborder/#/login?reg=tacn
     - Note: Free tier has rate limits; 2000+ points recommended

### How to Add API Keys

Edit the `.env` file and add your keys:

```bash
cd /workspace/TradingAgents-CN
nano .env  # or use any text editor

# Add your keys:
DEEPSEEK_API_KEY=sk-your-actual-key-here
DEEPSEEK_ENABLED=true

TUSHARE_TOKEN=your-tushare-token-here
TUSHARE_ENABLED=true
```

After adding keys, restart the backend:

```bash
tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 C-c
sleep 2
tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 'source env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000' C-m
```

## First Login

1. Open the frontend: http://localhost:3000
2. Login credentials:
   - **Username**: `admin`
   - **Password**: `admin123` (as set in `.env` -> `ADMIN_DEFAULT_PASSWORD`)

3. After first login, go to **Settings** to:
   - Change admin password
   - Configure AI model API keys
   - Set up data source preferences

## Features Available

### Working (Free, No API Keys Required)

- ✅ User authentication and management
- ✅ Stock data retrieval via AKShare (free)
- ✅ Stock screening and filtering
- ✅ Basic portfolio tracking
- ✅ Learning center (free courses)
- ✅ Paper trading simulation

### Requires API Keys

- ⚠️ **AI Analysis Features** (requires AI model API key):
  - Single stock research (multi-agent debate)
  - General research (natural language queries)
  - Smart assistant with web search
  - Memory and fact accumulation

- ⚠️ **Advanced Stock Data** (requires Tushare token):
  - Real-time quotes
  - Financial statements
  - Historical data synchronization
  - Professional indicators

## Blockers and Limitations

### Current Blockers

1. **MongoDB Authentication**: Running without authentication for development simplicity
   - **Impact**: Lower security, acceptable for local dev VM
   - **Fix for production**: Enable MongoDB auth and update `.env` with credentials

2. **Missing API Keys**: AI features won't work without API keys
   - **Impact**: Core analysis features disabled
   - **Required**: User must provide at least one AI model API key
   - **Cost**: DeepSeek is recommended (~$0.14 per 1M input tokens)

### Known Limitations

1. **No Docker**: MongoDB and Redis installed directly on VM
   - **Impact**: Manual service management required
   - **Benefit**: Simpler setup, no Docker daemon overhead

2. **Development Mode**: `DEBUG=true` in `.env`
   - **Impact**: Verbose logging, security checks relaxed
   - **For production**: Set `DEBUG=false` and enable proper authentication

3. **No HTTPS**: Services run on HTTP
   - **Impact**: Not secure for production
   - **For production**: Set up nginx with SSL/TLS certificates

## Troubleshooting

### Backend won't start

```bash
# Check backend logs
tmux -f /exec-daemon/tmux.portal.conf attach-session -t backend-server

# Common issues:
# 1. MongoDB not running
mongosh --eval "db.adminCommand('ping')"

# 2. Redis not running
redis-cli ping

# 3. Port 8000 already in use
lsof -i :8000
```

### Frontend won't start

```bash
# Check frontend logs
tmux -f /exec-daemon/tmux.portal.conf attach-session -t frontend-server

# Common issues:
# 1. Node modules not installed
cd /workspace/TradingAgents-CN/frontend && npm install

# 2. Port 3000 already in use
lsof -i :3000
```

### MongoDB issues

```bash
# Check if MongoDB is running
ps aux | grep mongod

# Check MongoDB logs
tail -50 /tmp/mongodb/logs/mongodb.log

# Restart MongoDB
pkill mongod
sleep 2
mongod --dbpath /tmp/mongodb/data --logpath /tmp/mongodb/logs/mongodb.log --port 27017 --bind_ip 127.0.0.1 --fork
```

### Redis issues

```bash
# Check if Redis is running
ps aux | grep redis-server

# Test Redis
redis-cli ping

# Restart Redis
pkill redis-server
sleep 1
redis-server --bind 127.0.0.1 --port 6379 --daemonize yes
```

## Development Workflow

### Making Code Changes

1. **Backend changes**:
   ```bash
   # Edit code in /workspace/TradingAgents-CN/app/
   # Restart backend
   tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 C-c
   sleep 1
   tmux -f /exec-daemon/tmux.portal.conf send-keys -t backend-server:0.0 'source env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' C-m
   ```

2. **Frontend changes**:
   ```bash
   # Edit code in /workspace/TradingAgents-CN/frontend/src/
   # Vite has hot module reloading, changes auto-apply
   ```

### Adding New Dependencies

```bash
# Backend (Python)
cd /workspace/TradingAgents-CN
source env/bin/activate
pip install <package-name>
pip freeze > requirements.txt

# Frontend (Node.js)
cd /workspace/TradingAgents-CN/frontend
npm install <package-name>
```

## Security Notes

⚠️ **This setup is for development/learning purposes only!**

For production deployment, you MUST:

1. Enable MongoDB authentication
2. Set Redis password
3. Use strong, unique values for `JWT_SECRET`, `CSRF_SECRET`, and `ADMIN_DEFAULT_PASSWORD`
4. Set `DEBUG=false`
5. Configure proper CORS origins (not `["*"]`)
6. Use HTTPS (nginx with SSL/TLS)
7. Never commit `.env` to version control
8. Never expose admin credentials

## Useful Links

- Backend API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Project README: [README.md](README.md)
- User Manual: [docs/02-user-guide/user-manual-v3.0.md](docs/02-user-guide/user-manual-v3.0.md)
- Original project: https://github.com/hsliuping/TradingAgents-CN

## Support

This is a community edition research/learning project. For questions:

1. Check the official documentation in `/docs`
2. Review the README.md
3. Check GitHub issues on the original repo
4. Contact project maintainer: hsliup@163.com

---

**Last Updated**: 2026-10-02  
**Setup by**: Cursor Cloud Agent  
**Repository**: https://github.com/lixinwang77/TradingAgents-CN (fork)
