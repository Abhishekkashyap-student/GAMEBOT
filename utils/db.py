import sqlite3
import threading
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "axlbot.db"
_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            is_dead INTEGER DEFAULT 0,
            protect_until INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0
        )
        """
        )
        # Ensure `is_premium` column exists for older DBs
        cur.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cur.fetchall()]
        if "is_premium" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
        conn.commit()
        conn.close()


def ensure_user(user_id: int, username: str | None = None):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users(user_id, username, balance, is_premium) VALUES(?,?,?,?)",
                (user_id, username or "", 0, 0),
            )
            conn.commit()
        else:
            if username and row["username"] != username:
                cur.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?", (username, user_id)
                )
                conn.commit()
        conn.close()


def set_premium(user_id: int, premium: bool):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (1 if premium else 0, user_id))
        conn.commit()
        conn.close()


def is_premium(user_id: int) -> bool:
    row = get_user(user_id)
    if not row:
        return False
    return bool(row["is_premium"])


def get_user(user_id: int):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row


def change_balance(user_id: int, delta: int):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        if delta < 0:
            # Safe subtract: ensure balance remains >= 0
            want = -delta
            cur.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
                (want, user_id, want),
            )
            if cur.rowcount == 0:
                conn.commit()
                conn.close()
                return None
        else:
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta, user_id))
        conn.commit()
        cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = cur.fetchone()[0]
        conn.close()
        return bal


def transfer(sender_id: int, recipient_id: int, amount: int) -> bool:
    """Atomically transfer amount from sender to recipient. Returns True on success."""
    if amount <= 0:
        return False
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        try:
            # ensure both users exist
            cur.execute("SELECT 1 FROM users WHERE user_id = ?", (recipient_id,))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO users(user_id, username, balance, is_premium) VALUES(?,?,?,?)", (recipient_id, "", 0, 0))
            cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?", (amount, sender_id, amount))
            if cur.rowcount == 0:
                conn.commit()
                conn.close()
                return False
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
            conn.commit()
            return True
        finally:
            conn.close()


def claim_daily(user_id: int, amount: int, now_ts: int) -> bool:
    """Claim daily amount if 24h passed. Returns True if claimed."""
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        last = row[0] if row else 0
        if now_ts - (last or 0) < 24 * 3600:
            conn.close()
            return False
        # perform update: set last_daily and add balance
        cur.execute("UPDATE users SET last_daily = ?, balance = balance + ? WHERE user_id = ?", (now_ts, amount, user_id))
        conn.commit()
        conn.close()
        return True


def set_dead(user_id: int, dead: bool):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_dead = ? WHERE user_id = ?", (1 if dead else 0, user_id))
        conn.commit()
        conn.close()


def set_protect(user_id: int, until_ts: int):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET protect_until = ? WHERE user_id = ?", (int(until_ts), user_id))
        conn.commit()
        conn.close()


def set_last_daily(user_id: int, ts: int):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (int(ts), user_id))
        conn.commit()
        conn.close()


def top_users(limit: int = 15):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return rows
