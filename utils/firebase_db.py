import os
import logging

logger = logging.getLogger(__name__)

# Try to import Firebase admin SDK. If not available, fall back to local sqlite utils.db
FIREBASE_AVAILABLE = True
try:
    import firebase_admin
    from firebase_admin import credentials, db
except Exception:  # pragma: no cover - fallback path used in tests/environments without firebase
    FIREBASE_AVAILABLE = False
    logger.warning("firebase_admin not available; falling back to local sqlite DB via utils.db")
    from . import db as local_db  # type: ignore


# Firebase configuration from environment variables
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
}

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "")


if FIREBASE_AVAILABLE:
    # Initialize Firebase only if credentials are available
    if FIREBASE_CONFIG["project_id"] and FIREBASE_CONFIG["private_key"] and FIREBASE_DB_URL:
        try:
            cred = credentials.Certificate(FIREBASE_CONFIG)
            firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    else:
        logger.warning("Firebase credentials not fully configured. Set all environment variables.")


def ensure_user(user_id: int, username: str | None = None):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            user_data = user_ref.get()

            if user_data is None:
                user_ref.set({
                    "user_id": user_id,
                    "username": username or "",
                    "balance": 0,
                    "is_dead": 0,
                    "protect_until": 0,
                    "last_daily": 0,
                    "is_premium": 0,
                })
            elif username and user_data.get("username") != username:
                user_ref.update({"username": username})
        except Exception as e:
            logger.error(f"Error in ensure_user (firebase): {e}")
    else:
        local_db.ensure_user(user_id, username)


def get_user(user_id: int):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            data = user_ref.get()
            if data:
                return {**data, "user_id": user_id}
            return None
        except Exception as e:
            logger.error(f"Error in get_user (firebase): {e}")
            return None
    else:
        row = local_db.get_user(user_id)
        if not row:
            return None
        # convert sqlite Row to dict-like
        return {k: row[k] for k in row.keys()}


def change_balance(user_id: int, delta: int):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            user_data = user_ref.get()

            if user_data is None:
                ensure_user(user_id)
                user_data = user_ref.get()

            current_balance = user_data.get("balance", 0)

            if delta < 0 and current_balance < -delta:
                return None

            new_balance = current_balance + delta
            user_ref.update({"balance": new_balance})
            return new_balance
        except Exception as e:
            logger.error(f"Error in change_balance (firebase): {e}")
            return None
    else:
        return local_db.change_balance(user_id, delta)


def transfer(sender_id: int, recipient_id: int, amount: int) -> bool:
    if FIREBASE_AVAILABLE:
        if amount <= 0:
            return False
        try:
            sender_ref = db.reference(f"users/{sender_id}")
            recipient_ref = db.reference(f"users/{recipient_id}")

            ensure_user(sender_id)
            ensure_user(recipient_id)

            sender_data = sender_ref.get()
            sender_balance = sender_data.get("balance", 0) if sender_data else 0

            if sender_balance < amount:
                return False

            sender_ref.update({"balance": sender_balance - amount})

            recipient_data = recipient_ref.get()
            recipient_balance = recipient_data.get("balance", 0) if recipient_data else 0
            recipient_ref.update({"balance": recipient_balance + amount})

            return True
        except Exception as e:
            logger.error(f"Error in transfer (firebase): {e}")
            return False
    else:
        return local_db.transfer(sender_id, recipient_id, amount)


def claim_daily(user_id: int, amount: int, now_ts: int) -> bool:
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            user_data = user_ref.get()

            if user_data is None:
                ensure_user(user_id)
                user_data = user_ref.get()

            last_daily = user_data.get("last_daily", 0)

            if now_ts - last_daily < 24 * 3600:
                return False

            current_balance = user_data.get("balance", 0)
            user_ref.update({"last_daily": now_ts, "balance": current_balance + amount})
            return True
        except Exception as e:
            logger.error(f"Error in claim_daily (firebase): {e}")
            return False
    else:
        return local_db.claim_daily(user_id, amount, now_ts)


def set_premium(user_id: int, premium: bool):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            ensure_user(user_id)
            user_ref.update({"is_premium": 1 if premium else 0})
        except Exception as e:
            logger.error(f"Error in set_premium (firebase): {e}")
    else:
        local_db.set_premium(user_id, premium)


def is_premium(user_id: int) -> bool:
    if FIREBASE_AVAILABLE:
        try:
            user_data = get_user(user_id)
            if not user_data:
                return False
            return bool(user_data.get("is_premium", 0))
        except Exception as e:
            logger.error(f"Error in is_premium (firebase): {e}")
            return False
    else:
        return local_db.is_premium(user_id)


def set_dead(user_id: int, dead: bool):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            ensure_user(user_id)
            user_ref.update({"is_dead": 1 if dead else 0})
        except Exception as e:
            logger.error(f"Error in set_dead (firebase): {e}")
    else:
        local_db.set_dead(user_id, dead)


def set_protect(user_id: int, until_ts: int):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            ensure_user(user_id)
            user_ref.update({"protect_until": int(until_ts)})
        except Exception as e:
            logger.error(f"Error in set_protect (firebase): {e}")
    else:
        local_db.set_protect(user_id, until_ts)


def set_last_daily(user_id: int, ts: int):
    if FIREBASE_AVAILABLE:
        try:
            user_ref = db.reference(f"users/{user_id}")
            ensure_user(user_id)
            user_ref.update({"last_daily": int(ts)})
        except Exception as e:
            logger.error(f"Error in set_last_daily (firebase): {e}")
    else:
        local_db.set_last_daily(user_id, ts)


def top_users(limit: int = 15):
    if FIREBASE_AVAILABLE:
        try:
            users_ref = db.reference("users")
            all_users = users_ref.get()

            if not all_users:
                return []

            user_list = [
                {
                    "user_id": uid,
                    "username": user.get("username", ""),
                    "balance": user.get("balance", 0),
                    "is_dead": user.get("is_dead", 0),
                    "is_premium": user.get("is_premium", 0),
                }
                for uid, user in all_users.items()
            ]

            user_list.sort(key=lambda x: x["balance"], reverse=True)

            return user_list[:limit]
        except Exception as e:
            logger.error(f"Error in top_users (firebase): {e}")
            return []
    else:
        rows = local_db.top_users(limit)
        # convert sqlite rows to list of dicts
        return [ {"user_id": r[0], "username": r[1], "balance": r[2], "is_dead": r[3], "is_premium": r[4]} for r in rows ]


def init_db():
    if FIREBASE_AVAILABLE:
        logger.info("Firebase database initialized")
    else:
        local_db.init_db()
