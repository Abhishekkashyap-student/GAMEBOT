import os
import time
import asyncio

from utils import db


def setup_function():
    try:
        if db.DB_PATH.exists():
            db.DB_PATH.unlink()
    except Exception:
        pass
    db.init_db()


def test_daily_and_leaderboard_basic():
    db.ensure_user(10, "dave")
    db.change_balance(10, 50)
    # simulate daily claim by setting last_daily far in past
    db.set_last_daily(10, 0)
    # give daily manually (economy.cmd_daily is async and needs Update), test db-level change
    db.change_balance(10, 500)
    row = db.get_user(10)
    assert row["balance"] >= 550
    top = db.top_users(10)
    assert any(r["user_id"] == 10 for r in top)
