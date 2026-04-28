"""
backend/routers/live.py
WebSocket endpoint for real-time signal feed.
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import database as db
import services.telegram_service as tg

router = APIRouter(tags=["live"])


@router.websocket("/ws/live")
async def live_feed(websocket: WebSocket, session_name: str = "default"):
    await websocket.accept()

    user = await db.get_user(session_name)
    if not user:
        await websocket.send_json({"type": "error", "message": "User not found"})
        await websocket.close()
        return

    await websocket.send_json({"type": "connected", "message": "Live feed active"})

    # Start Telegram listener if not already running
    await tg.start_live_listener(session_name, user["id"])

    async def broadcast(signal: dict):
        try:
            await websocket.send_json({"type": "signal", "data": signal})
        except Exception:
            pass

    tg.register_live_callback(session_name, broadcast)

    try:
        # Keep connection alive, send heartbeat every 30s
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        tg.unregister_live_callback(session_name, broadcast)
