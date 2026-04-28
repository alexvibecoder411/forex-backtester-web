"""
backend/database.py
Async SQLite database using aiosqlite.
"""

import aiosqlite
import json
from datetime import datetime
from config import DB_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(str(DB_PATH))
        _db.row_factory = aiosqlite.Row
        await _create_tables(_db)
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


async def _create_tables(db: aiosqlite.Connection):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name  TEXT UNIQUE NOT NULL,
            phone         TEXT,
            api_id        TEXT,
            api_hash      TEXT,
            connected     INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS channels (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            name        TEXT NOT NULL,
            channel_id  TEXT NOT NULL,
            parser      TEXT DEFAULT 'generic',
            active      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, channel_id)
        );

        CREATE TABLE IF NOT EXISTS signals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            provider    TEXT NOT NULL,
            pair        TEXT,
            direction   TEXT,
            entry       REAL,
            sl          REAL,
            tp1         REAL,
            tp2         REAL,
            tp3         REAL,
            timestamp   TEXT,
            raw_message TEXT,
            channel_id  TEXT,
            message_id  INTEGER,
            parsed_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, channel_id, message_id)
        );

        CREATE TABLE IF NOT EXISTS trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id       INTEGER REFERENCES signals(id),
            user_id         INTEGER REFERENCES users(id),
            outcome         TEXT,
            entry_price     REAL,
            exit_price      REAL,
            pips            REAL,
            usd_pnl         REAL,
            tp_hit          INTEGER,
            duration_mins   INTEGER,
            simulated_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS backtest_jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            status      TEXT DEFAULT 'pending',
            progress    INTEGER DEFAULT 0,
            total       INTEGER DEFAULT 0,
            message     TEXT,
            started_at  TEXT DEFAULT (datetime('now')),
            finished_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_signals_user     ON signals(user_id);
        CREATE INDEX IF NOT EXISTS idx_signals_pair     ON signals(pair);
        CREATE INDEX IF NOT EXISTS idx_trades_user      ON trades(user_id);
        CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id);
    """)
    await db.commit()


# ── Users ─────────────────────────────────────────────────────────────────────

async def upsert_user(session_name: str, phone: str, api_id: str, api_hash: str) -> int:
    db = await get_db()
    await db.execute("""
        INSERT INTO users (session_name, phone, api_id, api_hash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_name) DO UPDATE SET
            phone=excluded.phone, api_id=excluded.api_id, api_hash=excluded.api_hash
    """, (session_name, phone, api_id, api_hash))
    await db.commit()
    row = await (await db.execute(
        "SELECT id FROM users WHERE session_name=?", (session_name,)
    )).fetchone()
    return row["id"]


async def set_user_connected(session_name: str, connected: bool):
    db = await get_db()
    await db.execute(
        "UPDATE users SET connected=? WHERE session_name=?",
        (1 if connected else 0, session_name)
    )
    await db.commit()


async def get_user(session_name: str) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM users WHERE session_name=?", (session_name,)
    )).fetchone()
    return dict(row) if row else None


# ── Channels ──────────────────────────────────────────────────────────────────

async def add_channel(user_id: int, name: str, channel_id: str, parser: str = "generic") -> int | None:
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO channels (user_id, name, channel_id, parser)
            VALUES (?, ?, ?, ?)
        """, (user_id, name, channel_id, parser))
        await db.commit()
        return cur.lastrowid
    except Exception:
        return None


async def get_channels(user_id: int) -> list[dict]:
    db = await get_db()
    rows = await (await db.execute(
        "SELECT * FROM channels WHERE user_id=? AND active=1", (user_id,)
    )).fetchall()
    return [dict(r) for r in rows]


async def delete_channel(channel_db_id: int, user_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE channels SET active=0 WHERE id=? AND user_id=?",
        (channel_db_id, user_id)
    )
    await db.commit()


# ── Signals ───────────────────────────────────────────────────────────────────

async def insert_signal(signal: dict) -> int | None:
    db = await get_db()
    try:
        cur = await db.execute("""
            INSERT INTO signals
                (user_id, provider, pair, direction, entry, sl, tp1, tp2, tp3,
                 timestamp, raw_message, channel_id, message_id)
            VALUES
                (:user_id, :provider, :pair, :direction, :entry, :sl, :tp1, :tp2, :tp3,
                 :timestamp, :raw_message, :channel_id, :message_id)
        """, signal)
        await db.commit()
        return cur.lastrowid
    except Exception:
        return None


async def get_signals(user_id: int, provider: str = None, pair: str = None,
                      start: str = None, end: str = None) -> list[dict]:
    db   = await get_db()
    q    = "SELECT * FROM signals WHERE user_id=?"
    args = [user_id]
    if provider: q += " AND provider=?";   args.append(provider)
    if pair:     q += " AND pair=?";       args.append(pair)
    if start:    q += " AND timestamp>=?"; args.append(start)
    if end:      q += " AND timestamp<=?"; args.append(end)
    q += " ORDER BY timestamp ASC"
    rows = await (await db.execute(q, args)).fetchall()
    return [dict(r) for r in rows]


async def count_signals(user_id: int) -> int:
    db = await get_db()
    row = await (await db.execute(
        "SELECT COUNT(*) as c FROM signals WHERE user_id=?", (user_id,)
    )).fetchone()
    return row["c"]


# ── Trades ────────────────────────────────────────────────────────────────────

async def insert_trade(trade: dict) -> int:
    db = await get_db()
    cur = await db.execute("""
        INSERT INTO trades
            (signal_id, user_id, outcome, entry_price, exit_price, pips,
             usd_pnl, tp_hit, duration_mins)
        VALUES
            (:signal_id, :user_id, :outcome, :entry_price, :exit_price, :pips,
             :usd_pnl, :tp_hit, :duration_mins)
    """, trade)
    await db.commit()
    return cur.lastrowid


async def get_trades(user_id: int, provider: str = None, pair: str = None) -> list[dict]:
    db = await get_db()
    q = """
        SELECT t.*, s.provider, s.pair, s.direction, s.timestamp, s.entry as signal_entry
        FROM trades t JOIN signals s ON s.id = t.signal_id
        WHERE t.user_id=?
    """
    args = [user_id]
    if provider: q += " AND s.provider=?"; args.append(provider)
    if pair:     q += " AND s.pair=?";     args.append(pair)
    q += " ORDER BY s.timestamp ASC"
    rows = await (await db.execute(q, args)).fetchall()
    return [dict(r) for r in rows]


async def clear_trades(user_id: int):
    db = await get_db()
    await db.execute("DELETE FROM trades WHERE user_id=?", (user_id,))
    await db.commit()


# ── Backtest Jobs ─────────────────────────────────────────────────────────────

async def create_job(user_id: int) -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO backtest_jobs (user_id) VALUES (?)", (user_id,)
    )
    await db.commit()
    return cur.lastrowid


async def update_job(job_id: int, status: str, progress: int = 0,
                     total: int = 0, message: str = ""):
    db = await get_db()
    finished = "datetime('now')" if status in ("done", "error") else "NULL"
    await db.execute(f"""
        UPDATE backtest_jobs
        SET status=?, progress=?, total=?, message=?,
            finished_at={"datetime('now')" if status in ('done','error') else 'finished_at'}
        WHERE id=?
    """, (status, progress, total, message, job_id))
    await db.commit()


async def get_job(job_id: int) -> dict | None:
    db = await get_db()
    row = await (await db.execute(
        "SELECT * FROM backtest_jobs WHERE id=?", (job_id,)
    )).fetchone()
    return dict(row) if row else None
