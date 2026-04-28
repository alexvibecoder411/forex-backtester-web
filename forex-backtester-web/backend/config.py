"""
backend/config.py
Central configuration — reads from environment variables with sane defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", str(BASE_DIR / "data")))
SESSION_DIR = DATA_DIR / "sessions"
DB_PATH     = DATA_DIR / "signals.db"
OUTPUT_DIR  = DATA_DIR / "output"

for d in [DATA_DIR, SESSION_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Server ────────────────────────────────────────────────────────────────────
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = int(os.getenv("PORT", 8000))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# ── Instruments ───────────────────────────────────────────────────────────────
TICKER_MAP = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "GBPJPY": "GBPJPY=X",
    "USDCAD": "USDCAD=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "USDCHF": "USDCHF=X",
    "EURJPY": "EURJPY=X",
    "EURGBP": "EURGBP=X",
    "US30":   "YM=F",
    "NAS100": "NQ=F",
    "SP500":  "ES=F",
    "UK100":  "Z=F",
    "GER40":  "FDAX=F",
}

PIP_SIZE_MAP = {
    "XAUUSD": 0.01,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "EURJPY": 0.01,
    "US30":   1.0,
    "NAS100": 1.0,
    "SP500":  1.0,
    "UK100":  1.0,
    "GER40":  1.0,
    "default": 0.0001,
}

PIP_VALUE_MAP = {
    "XAUUSD": 1.0,
    "EURUSD": 10.0,
    "GBPUSD": 10.0,
    "USDJPY": 9.0,
    "GBPJPY": 9.0,
    "USDCAD": 7.5,
    "AUDUSD": 10.0,
    "NZDUSD": 10.0,
    "USDCHF": 10.0,
    "EURJPY": 9.0,
    "EURGBP": 10.0,
    "US30":   5.0,
    "NAS100": 5.0,
    "SP500":  5.0,
    "UK100":  5.0,
    "GER40":  5.0,
    "default": 10.0,
}

SPREAD_PIPS = {
    "XAUUSD": 3.0,
    "EURUSD": 1.2,
    "GBPUSD": 1.5,
    "USDJPY": 1.5,
    "GBPJPY": 2.0,
    "US30":   5.0,
    "NAS100": 5.0,
    "default": 2.0,
}

KNOWN_PAIRS = list(TICKER_MAP.keys())
