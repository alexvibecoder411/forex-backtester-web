"""
backend/routers/auth.py
Telegram authentication endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database as db
import services.telegram_service as tg

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ConnectRequest(BaseModel):
    api_id:       str
    api_hash:     str
    phone:        str
    session_name: str = "default"


class VerifyRequest(BaseModel):
    session_name: str = "default"
    phone:        str
    code:         str
    password:     str = None


class DisconnectRequest(BaseModel):
    session_name: str = "default"


@router.post("/connect")
async def connect(req: ConnectRequest):
    """Step 1: Initiate Telegram connection."""
    user_id = await db.upsert_user(req.session_name, req.phone, req.api_id, req.api_hash)
    result  = await tg.connect_client(req.session_name, req.phone, req.api_id, req.api_hash)
    result["user_id"] = user_id
    return result


@router.post("/verify")
async def verify(req: VerifyRequest):
    """Step 2: Submit the OTP code received on Telegram."""
    result = await tg.verify_code(req.session_name, req.phone, req.code, req.password)
    if result["status"] == "error":
        raise HTTPException(400, result["message"])
    return result


@router.get("/status")
async def status(session_name: str = "default"):
    """Check current connection status."""
    user = await db.get_user(session_name)
    if not user:
        return {"connected": False}
    return await tg.get_status(session_name, user.get("api_id"), user.get("api_hash"))


@router.post("/disconnect")
async def disconnect(req: DisconnectRequest):
    await tg.disconnect_client(req.session_name)
    return {"status": "disconnected"}
