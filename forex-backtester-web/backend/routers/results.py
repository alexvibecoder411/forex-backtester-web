"""
backend/routers/results.py
Trade results, stats, signals list, and CSV export.
"""

import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import database as db
from services.analytics_service import compute_stats

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/stats")
async def get_stats(session_name: str = "default", provider: str = None, pair: str = None):
    user = await db.get_user(session_name)
    if not user:
        raise HTTPException(404, "User session not found.")
    trades = await db.get_trades(user["id"], provider=provider, pair=pair)
    return compute_stats(trades)


@router.get("/trades")
async def get_trades(session_name: str = "default", provider: str = None,
                     pair: str = None, limit: int = 500):
    user = await db.get_user(session_name)
    if not user:
        raise HTTPException(404, "User session not found.")
    trades = await db.get_trades(user["id"], provider=provider, pair=pair)
    return trades[:limit]


@router.get("/signals")
async def get_signals(session_name: str = "default", provider: str = None,
                      pair: str = None, limit: int = 500):
    user = await db.get_user(session_name)
    if not user:
        raise HTTPException(404, "User session not found.")
    signals = await db.get_signals(user["id"], provider=provider, pair=pair)
    return signals[:limit]


@router.get("/export/csv")
async def export_csv(session_name: str = "default"):
    user = await db.get_user(session_name)
    if not user:
        raise HTTPException(404, "User session not found.")
    trades = await db.get_trades(user["id"])
    if not trades:
        raise HTTPException(404, "No trades to export.")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(trades[0].keys()))
    writer.writeheader()
    writer.writerows(trades)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trades.csv"}
    )
