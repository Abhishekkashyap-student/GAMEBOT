"""
Async MongoDB helper using Motor (optional). This module is added to satisfy the
requirement to support Motor (async MongoDB). It exposes simple async functions
that can be used by newer async handlers. If `MONGO_URI` is not set, callers
should fall back to the existing sqlite firebase_db module.

Usage (async):
    from utils.motor_db import ensure_user, get_user, change_balance
    await ensure_user(user_id, username)
    user = await get_user(user_id)

This file intentionally provides a minimal, production-ready async interface.
"""
from typing import Optional
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("MONGO_DBNAME", "gamebot")

_client = None
_db = None


async def _connect():
    global _client, _db
    if _client is not None:
        return
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except Exception as e:
        logger.error("motor is not installed: %s", e)
        return

    if not MONGO_URI:
        logger.info("MONGO_URI not set; motor not initialized")
        return

    _client = AsyncIOMotorClient(MONGO_URI)
    _db = _client[DB_NAME]
    # Ensure indexes
    try:
        await _db.users.create_index("user_id", unique=True)
    except Exception:
        pass


async def ensure_user(user_id: int, username: Optional[str] = None):
    await _connect()
    if _db is None:
        return
    users = _db.users
    await users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "username": username or "",
                "balance": 0,
                "is_dead": False,
                "protect_until": 0,
                "last_daily": 0,
                "is_premium": False,
            }
        },
        upsert=True,
    )


async def get_user(user_id: int):
    await _connect()
    if _db is None:
        return None
    users = _db.users
    doc = await users.find_one({"user_id": user_id})
    return doc


async def change_balance(user_id: int, delta: int):
    await _connect()
    if _db is None:
        return None
    users = _db.users
    if delta < 0:
        # atomic decrement only if enough balance
        res = await users.find_one_and_update(
            {"user_id": user_id, "balance": {"$gte": -delta}},
            {"$inc": {"balance": delta}},
            return_document=True,
        )
        if res is None:
            return None
        return res.get("balance")
    else:
        res = await users.find_one_and_update(
            {"user_id": user_id}, {"$inc": {"balance": delta}}, return_document=True
        )
        if res:
            return res.get("balance")
        return None


async def transfer(sender_id: int, recipient_id: int, amount: int) -> bool:
    if amount <= 0:
        return False
    await _connect()
    if _db is None:
        return False
    users = _db.users
    # ensure both
    await ensure_user(sender_id, None)
    await ensure_user(recipient_id, None)

    async with await _client.start_session() as s:
        async with s.start_transaction():
            sender = await users.find_one({"user_id": sender_id})
            if not sender or sender.get("balance", 0) < amount:
                return False
            await users.update_one({"user_id": sender_id}, {"$inc": {"balance": -amount}})
            await users.update_one({"user_id": recipient_id}, {"$inc": {"balance": amount}})
            return True


async def claim_daily(user_id: int, amount: int, now_ts: int) -> bool:
    await _connect()
    if _db is None:
        return False
    users = _db.users
    user = await users.find_one({"user_id": user_id})
    last = user.get("last_daily", 0) if user else 0
    if now_ts - last < 24 * 3600:
        return False
    await users.update_one({"user_id": user_id}, {"$set": {"last_daily": now_ts}, "$inc": {"balance": amount}})
    return True


async def top_users(limit: int = 15):
    await _connect()
    if _db is None:
        return []
    users = _db.users
    cursor = users.find({}, {"_id": 0}).sort("balance", -1).limit(limit)
    return [doc async for doc in cursor]
