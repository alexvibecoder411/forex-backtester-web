"""
backend/services/parser_service.py
Parses raw Telegram messages into normalised signal dicts.
"""

import re
from config import KNOWN_PAIRS


def _clean_price(val: str) -> float | None:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _find_pair(text: str) -> str | None:
    upper = text.upper()
    for pair in KNOWN_PAIRS:
        if pair in upper:
            return pair
    return None


def _find_direction(text: str) -> str | None:
    upper = text.upper()
    for kw in ["BUY", "LONG"]:
        if kw in upper:
            return "BUY"
    for kw in ["SELL", "SHORT"]:
        if kw in upper:
            return "SELL"
    return None


PRICE_RE = r"[\d,]+\.?\d*"


def _find_price_after(text: str, *labels: str) -> float | None:
    for label in labels:
        m = re.search(
            rf"{re.escape(label)}\s*[:\-]?\s*({PRICE_RE})",
            text, re.IGNORECASE
        )
        if m:
            return _clean_price(m.group(1))
    return None


def _find_entry(text: str) -> float | None:
    price = _find_price_after(text, "entry", "enter", "price", "@")
    if price:
        return price
    m = re.search(r"(?:^|\s)(\d{1,6}\.?\d{2,})", text)
    return _clean_price(m.group(1)) if m else None


def _find_tps(text: str):
    tp1 = _find_price_after(text, "TP1", "TP 1", "Target 1", "T1", "Take Profit 1")
    tp2 = _find_price_after(text, "TP2", "TP 2", "Target 2", "T2", "Take Profit 2")
    tp3 = _find_price_after(text, "TP3", "TP 3", "Target 3", "T3", "Take Profit 3")
    if not tp1:
        tp1 = _find_price_after(text, "TP", "Take Profit", "Target", "T/P")
    return tp1, tp2, tp3


def parse_message(text: str, provider: str, channel_id: str,
                  message_id: int, timestamp: str, user_id: int) -> dict | None:
    """Parse a raw message. Returns normalised signal dict or None."""
    pair      = _find_pair(text)
    direction = _find_direction(text)
    if not pair or not direction:
        return None

    entry       = _find_entry(text)
    sl          = _find_price_after(text, "SL", "Stop Loss", "Stop", "S/L", "Stoploss")
    tp1, tp2, tp3 = _find_tps(text)

    if not entry or not sl or not tp1:
        return None

    return {
        "user_id":     user_id,
        "provider":    provider,
        "pair":        pair,
        "direction":   direction,
        "entry":       entry,
        "sl":          sl,
        "tp1":         tp1,
        "tp2":         tp2,
        "tp3":         tp3,
        "timestamp":   timestamp,
        "raw_message": text,
        "channel_id":  str(channel_id),
        "message_id":  message_id,
    }
