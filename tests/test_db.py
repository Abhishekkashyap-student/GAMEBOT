import os
import time
import shutil

import pytest

from utils import db


def setup_function():
    # Remove DB if present to start fresh
    try:
        if db.DB_PATH.exists():
            db.DB_PATH.unlink()
    except Exception:
        pass
    db.init_db()


def test_ensure_user_and_balance():
    db.ensure_user(1, "alice")
    bal = db.change_balance(1, 100)
    row = db.get_user(1)
    assert row["username"] == "alice"
    assert row["balance"] == 100


def test_set_dead_and_protect():
    db.ensure_user(2, "bob")
    db.set_dead(2, True)
    row = db.get_user(2)
    assert row["is_dead"] == 1
    ts = int(time.time()) + 3600
    db.set_protect(2, ts)
    row = db.get_user(2)
    assert row["protect_until"] >= ts


def test_premium_flag_and_top_users():
    db.ensure_user(3, "carol")
    db.change_balance(3, 500)
    db.set_premium(3, True)
    assert db.is_premium(3)
    top = db.top_users(5)
    assert any(r["user_id"] == 3 for r in top)
