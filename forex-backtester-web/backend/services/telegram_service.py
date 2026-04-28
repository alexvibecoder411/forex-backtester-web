"""
backend/services/telegram_service.py
Manages Telethon clients per user session.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import Message
from config import SESSION_DIR
import database as db
from services.parser_service import parse_message

# Active clients keyed by session_name
_clients: dict[str, TelegramClient] = {}

# WebSocket broadcast callbacks keyed by session_name
_live_callbacks: dict[str, list] = {}


def _session_path(session_name: str) -> str:
    return str(SESSION_DIR / session_name)


async def create_client(session_name: str, api_id: str, api_hash: str) -> TelegramClient:
    if session_name in _clients:
        return _clients[session_name]
    client = TelegramClient(_session_path(session_name), int(api_id), api_hash)
    _clients[session_name] = client
    return client


async def connect_client(session_name: str, phone: str, api_id: str, api_hash: str) -> dict:
    """
    Start client and send auth code if not yet authorised.
    Returns {"status": "connected"} or {"status": "code_required"}
    """
    client = await create_client(session_name, api_id, api_hash)
    await client.connect()

    if await client.is_user_authorized():
        await db.set_user_connected(session_name, True)
        me = await client.get_me()
        return {"status": "connected", "name": me.first_name, "username": me.username}

    await client.send_code_request(phone)
    return {"status": "code_required"}


async def verify_code(session_name: str, phone: str, code: str, password: str = None) -> dict:
    """Complete sign-in with the received code (and optional 2FA password)."""
    client = _clients.get(session_name)
    if not client:
        return {"status": "error", "message": "Session not found. Start auth first."}

    try:
        await client.sign_in(phone, code)
    except Exception as e:
        if "password" in str(e).lower() and password:
            await client.sign_in(password=password)
        elif "password" in str(e).lower():
            return {"status": "2fa_required"}
        else:
            return {"status": "error", "message": str(e)}

    await db.set_user_connected(session_name, True)
    me = await client.get_me()
    return {"status": "connected", "name": me.first_name, "username": me.username}


async def disconnect_client(session_name: str):
    client = _clients.pop(session_name, None)
    if client:
        await client.disconnect()
    await db.set_user_connected(session_name, False)


async def get_status(session_name: str, api_id: str = None, api_hash: str = None) -> dict:
    client = _clients.get(session_name)
    if not client:
        if api_id and api_hash:
            client = await create_client(session_name, api_id, api_hash)
            await client.connect()
        else:
            return {"connected": False}

    if await client.is_user_authorized():
        me = await client.get_me()
        return {"connected": True, "name": me.first_name, "username": me.username}
    return {"connected": False}


# ── Historical Fetch ──────────────────────────────────────────────────────────

async def fetch_historical(session_name: str, user_id: int, history_days: int,
                            progress_callback=None) -> int:
    client = _clients.get(session_name)
    if not client or not await client.is_user_authorized():
        raise RuntimeError("Not connected to Telegram")

    channels = await db.get_channels(user_id)
    if not channels:
        return 0

    cutoff     = datetime.now(timezone.utc) - timedelta(days=history_days)
    total_saved = 0
    total_channels = len(channels)

    for ch_idx, channel in enumerate(channels):
        try:
            entity = await client.get_entity(int(channel["channel_id"]))
        except Exception as e:
            if progress_callback:
                await progress_callback(ch_idx, total_channels, f"Could not access {channel['name']}: {e}")
            continue

        saved = 0
        async for message in client.iter_messages(entity, reverse=False):
            if message.date < cutoff:
                break
            if not isinstance(message, Message) or not message.text:
                continue

            signal = parse_message(
                text       = message.text,
                provider   = channel["name"],
                channel_id = channel["channel_id"],
                message_id = message.id,
                timestamp  = message.date.replace(tzinfo=timezone.utc).isoformat(),
                user_id    = user_id,
            )
            if signal:
                row_id = await db.insert_signal(signal)
                if row_id:
                    saved += 1

        total_saved += saved
        if progress_callback:
            await progress_callback(
                ch_idx + 1, total_channels,
                f"Fetched {channel['name']}: {saved} signals saved"
            )

    return total_saved


# ── Live Listener ─────────────────────────────────────────────────────────────

def register_live_callback(session_name: str, callback):
    _live_callbacks.setdefault(session_name, []).append(callback)


def unregister_live_callback(session_name: str, callback):
    if session_name in _live_callbacks:
        _live_callbacks[session_name] = [
            cb for cb in _live_callbacks[session_name] if cb != callback
        ]


async def start_live_listener(session_name: str, user_id: int):
    client = _clients.get(session_name)
    if not client:
        return

    channels = await db.get_channels(user_id)
    channel_ids = [int(ch["channel_id"]) for ch in channels]
    channel_map = {str(ch["channel_id"]): ch for ch in channels}

    @client.on(events.NewMessage(chats=channel_ids))
    async def handler(event):
        message = event.message
        if not isinstance(message, Message) or not message.text:
            return

        chat_id = str(event.chat_id)
        cfg     = channel_map.get(chat_id, {})

        signal = parse_message(
            text       = message.text,
            provider   = cfg.get("name", chat_id),
            channel_id = chat_id,
            message_id = message.id,
            timestamp  = message.date.replace(tzinfo=timezone.utc).isoformat(),
            user_id    = user_id,
        )

        if signal:
            signal_id = await db.insert_signal(signal)
            if signal_id:
                signal["id"] = signal_id
                # Broadcast to all registered WebSocket callbacks
                for cb in _live_callbacks.get(session_name, []):
                    try:
                        await cb(signal)
                    except Exception:
                        pass
