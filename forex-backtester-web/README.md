# Forex Signal Backtester — Web App

A full-stack web application for backtesting forex signals pulled live from Telegram.

---

## Stack
- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python
- **Database**: SQLite (via aiosqlite)
- **Telegram**: Telethon (user account API)
- **Price Data**: yfinance (auto-fetched OHLC)

---

## Quick Start (Local Dev)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# API running at http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

---

## Quick Start (Docker)

```bash
docker-compose up --build
# App at http://localhost:5173
# API at http://localhost:8000
```

---

## How to Use

### Step 1 — Setup
1. Go to **Setup** page
2. Get your API credentials from [my.telegram.org/apps](https://my.telegram.org/apps)
3. Enter `api_id`, `api_hash`, and your phone number
4. Enter the OTP code sent to your Telegram app

### Step 2 — Channels
1. Go to **Channels** page
2. Add each signal provider's channel
3. Get Channel IDs by forwarding a message to `@userinfobot` on Telegram

### Step 3 — Backtest
1. Go to **Backtest** page
2. Click **Fetch from Telegram** — pulls historical signals
3. Configure lot size, TP split, breakeven settings
4. Click **Run Simulation**

### Step 4 — Reports
- View win rate, equity curve, drawdown, per-pair stats
- Switch between Overview / Trades / Pairs / Providers tabs
- Export results as CSV

### Step 5 — Live Monitor
- Click **Start Listening** to watch channels in real time
- New signals appear instantly as they're posted

---

## Hosting on Railway (Free Tier)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project → Deploy from GitHub
4. Set environment variables: `HOST`, `PORT`, `CORS_ORIGINS`
5. Railway auto-builds and deploys

---

## Project Structure

```
forex-backtester-web/
├── backend/
│   ├── main.py                   # FastAPI app
│   ├── config.py                 # Settings + instrument maps
│   ├── database.py               # Async SQLite
│   ├── routers/
│   │   ├── auth.py               # Telegram auth
│   │   ├── channels.py           # Channel management
│   │   ├── backtest.py           # Fetch + simulate
│   │   ├── results.py            # Stats + CSV export
│   │   └── live.py               # WebSocket feed
│   └── services/
│       ├── telegram_service.py   # Telethon wrapper
│       ├── parser_service.py     # Signal parsing
│       ├── simulator_service.py  # Trade simulation
│       └── analytics_service.py  # Stats calculation
└── frontend/
    └── src/
        ├── pages/
        │   ├── Setup.jsx
        │   ├── Channels.jsx
        │   ├── Backtest.jsx
        │   ├── LiveMonitor.jsx
        │   └── Reports.jsx
        ├── components/
        │   ├── Sidebar.jsx
        │   └── UI.jsx
        ├── hooks/useSession.jsx
        └── utils/api.js
```
