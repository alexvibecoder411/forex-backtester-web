"""
backend/routers/backtest.py
Backtest trigger, status polling, and historical fetch endpoints.
"""

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import database as db
import services.telegram_service as tg
import services.simulator_service as sim

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


class FetchRequest(BaseModel):
    session_name: str = "default"
    history_days: int = 180


class RunRequest(BaseModel):
    session_name:  str   = "default"
    lot_size:      float = 0.1
    be_after_tp1:  bool  = True
    tp_split:      str   = "equal"
    custom_ratios: list  = []
    provider:      str   = None
    pair:          str   = None
    history_days:  int   = 180


@router.post("/fetch")
async def fetch_history(req: FetchRequest, background_tasks: BackgroundTasks):
    """Fetch historical signals from Telegram in the background."""
    user = await db.get_user(req.session_name)
    if not user:
        raise HTTPException(404, "User session not found.")

    job_id = await db.create_job(user["id"])

    async def _run():
        async def progress(done, total, msg):
            await db.update_job(job_id, "running", done, total, msg)

        try:
            saved = await tg.fetch_historical(
                req.session_name, user["id"], req.history_days, progress
            )
            await db.update_job(job_id, "done", saved, saved,
                                f"Fetch complete. {saved} signals saved.")
        except Exception as e:
            await db.update_job(job_id, "error", 0, 0, str(e))

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "started"}


@router.post("/run")
async def run_backtest(req: RunRequest, background_tasks: BackgroundTasks):
    """Run simulation on stored signals in the background."""
    user = await db.get_user(req.session_name)
    if not user:
        raise HTTPException(404, "User session not found.")

    signal_count = await db.count_signals(user["id"])
    if signal_count == 0:
        raise HTTPException(400, "No signals found. Fetch historical data first.")

    job_id = await db.create_job(user["id"])

    async def _run():
        try:
            await sim.run_backtest(
                user_id      = user["id"],
                job_id       = job_id,
                lot_size     = req.lot_size,
                be_after_tp1 = req.be_after_tp1,
                tp_split     = req.tp_split,
                custom_ratios = req.custom_ratios,
                provider     = req.provider,
                pair         = req.pair,
                history_days = req.history_days,
            )
        except Exception as e:
            await db.update_job(job_id, "error", 0, 0, str(e))

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "started"}


@router.get("/status/{job_id}")
async def job_status(job_id: int):
    """Poll background job progress."""
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    return job
