"""
backend/routers/channels.py
Channel management endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database as db

router = APIRouter(prefix="/api/channels", tags=["channels"])


class AddChannelRequest(BaseModel):
    session_name: str = "default"
    name:         str
    channel_id:   str
    parser:       str = "generic"


class DeleteChannelRequest(BaseModel):
    session_name: str = "default"
    channel_db_id: int


@router.get("")
async def list_channels(session_name: str = "default"):
    user = await db.get_user(session_name)
    if not user:
        return []
    return await db.get_channels(user["id"])


@router.post("")
async def add_channel(req: AddChannelRequest):
    user = await db.get_user(req.session_name)
    if not user:
        raise HTTPException(404, "User session not found. Connect to Telegram first.")

    row_id = await db.add_channel(user["id"], req.name, req.channel_id, req.parser)
    if not row_id:
        raise HTTPException(409, "Channel already exists.")
    return {"id": row_id, "name": req.name, "channel_id": req.channel_id}


@router.delete("/{channel_db_id}")
async def delete_channel(channel_db_id: int, session_name: str = "default"):
    user = await db.get_user(session_name)
    if not user:
        raise HTTPException(404, "User session not found.")
    await db.delete_channel(channel_db_id, user["id"])
    return {"status": "deleted"}
