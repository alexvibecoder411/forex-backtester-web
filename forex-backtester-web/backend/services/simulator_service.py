"""
backend/services/simulator_service.py
Trade simulation against yfinance OHLC data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
from config import TICKER_MAP, PIP_SIZE_MAP, PIP_VALUE_MAP, SPREAD_PIPS
import database as db


_price_cache: dict[str, pd.DataFrame] = {}


def _pip_size(pair: str) -> float:
    return PIP_SIZE_MAP.get(pair, PIP_SIZE_MAP["default"])


def _pip_value(pair: str, lot: float) -> float:
    return PIP_VALUE_MAP.get(pair, PIP_VALUE_MAP["default"]) * lot


def _spread_price(pair: str) -> float:
    return SPREAD_PIPS.get(pair, SPREAD_PIPS["default"]) * _pip_size(pair)


def _fetch_ohlc(pair: str, start: datetime, end: datetime) -> pd.DataFrame | None:
    ticker = TICKER_MAP.get(pair, f"{pair}=X")
    key    = f"{ticker}_{start.date()}_{end.date()}"
    if key in _price_cache:
        return _price_cache[key]
    try:
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=(end + timedelta(days=2)).strftime("%Y-%m-%d"),
            interval="1h", progress=False, auto_adjust=True,
        )
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index, utc=True)
        df.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in df.columns]
        df = df[["open", "high", "low", "close"]]
        _price_cache[key] = df
        return df
    except Exception as e:
        print(f"[Simulator] Price fetch error for {pair}: {e}")
        return None


def _simulate_one(signal: dict, lot_size: float, be_after_tp1: bool,
                   tp_split: str, custom_ratios: list) -> list[dict]:
    pair      = signal["pair"]
    direction = signal["direction"]
    entry     = signal["entry"]
    sl        = signal["sl"]
    tps       = [t for t in [signal.get("tp1"), signal.get("tp2"), signal.get("tp3")] if t]

    if not tps:
        return []

    # Ratios
    n = len(tps)
    if tp_split == "custom" and custom_ratios:
        ratios = (custom_ratios[:n] + [1/n]*n)[:n]
        s = sum(ratios); ratios = [r/s for r in ratios]
    else:
        ratios = [1/n]*n

    try:
        sig_time = datetime.fromisoformat(signal["timestamp"])
        if sig_time.tzinfo is None:
            sig_time = sig_time.replace(tzinfo=timezone.utc)
    except Exception:
        return []

    df = _fetch_ohlc(pair, sig_time, sig_time + timedelta(days=60))
    if df is None or df.empty:
        return []

    candles = df[df.index >= pd.Timestamp(sig_time, tz="UTC")].head(720)
    if candles.empty:
        return []

    spread = _spread_price(pair)
    eff_entry = entry + spread if direction == "BUY" else entry - spread

    results   = []
    active_sl = sl
    tp1_hit   = False

    for tp_idx, (tp_price, ratio) in enumerate(zip(tps, ratios), 1):
        outcome    = "PENDING"
        exit_price = None
        exit_i     = None
        cur_sl     = active_sl

        for i, (_, c) in enumerate(candles.iterrows()):
            if direction == "BUY":
                if c["low"]  <= cur_sl:  outcome="LOSS"; exit_price=cur_sl; exit_i=i; break
                if c["high"] >= tp_price: outcome="WIN";  exit_price=tp_price; exit_i=i; break
            else:
                if c["high"] >= cur_sl:  outcome="LOSS"; exit_price=cur_sl; exit_i=i; break
                if c["low"]  <= tp_price: outcome="WIN";  exit_price=tp_price; exit_i=i; break

        if outcome == "WIN" and tp_idx == 1 and be_after_tp1 and n > 1:
            active_sl = eff_entry
            tp1_hit   = True

        if tp1_hit and outcome == "LOSS":
            outcome = "BREAKEVEN"
            exit_price = eff_entry

        if exit_price is not None:
            diff = (exit_price - eff_entry) if direction == "BUY" else (eff_entry - exit_price)
            pips    = round((diff / _pip_size(pair)) * ratio, 1)
            usd_pnl = round(_pip_value(pair, lot_size) * pips, 2)
            dur     = exit_i if exit_i is not None else len(candles)
        else:
            pips = usd_pnl = 0
            dur  = len(candles)

        results.append({
            "signal_id":    signal["id"],
            "user_id":      signal["user_id"],
            "outcome":      outcome,
            "entry_price":  eff_entry,
            "exit_price":   exit_price,
            "pips":         pips,
            "usd_pnl":      usd_pnl,
            "tp_hit":       tp_idx if outcome == "WIN" else None,
            "duration_mins": dur,
        })

        if outcome == "LOSS":
            break

    return results


async def run_backtest(
    user_id: int,
    job_id: int,
    lot_size: float = 0.1,
    be_after_tp1: bool = True,
    tp_split: str = "equal",
    custom_ratios: list = None,
    provider: str = None,
    pair: str = None,
    history_days: int = 180,
) -> dict:
    """Run full backtest for a user. Updates job progress in DB."""

    await db.clear_trades(user_id)
    signals = await db.get_signals(user_id, provider=provider, pair=pair)
    total   = len(signals)

    await db.update_job(job_id, "running", 0, total, "Starting simulation...")

    all_trades = []
    for i, signal in enumerate(signals):
        trades = _simulate_one(signal, lot_size, be_after_tp1, tp_split, custom_ratios or [])
        for t in trades:
            await db.insert_trade(t)
        all_trades.extend(trades)

        if (i + 1) % 5 == 0 or (i + 1) == total:
            await db.update_job(
                job_id, "running", i + 1, total,
                f"Simulating {i+1}/{total}: {signal.get('pair')} {signal.get('direction')}"
            )

    await db.update_job(job_id, "done", total, total,
                        f"Complete. {len(all_trades)} trade legs simulated.")
    return {"trades": len(all_trades), "signals": total}
