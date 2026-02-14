import os

from utils import db
import economy


def setup_function():
    try:
        if db.DB_PATH.exists():
            db.DB_PATH.unlink()
    except Exception:
        pass
    # set owner env and init
    os.environ["OWNER_ID"] = "99999"
    db.init_db()


def test_owner_marked_premium_on_setup():
    economy.setup()
    assert db.is_premium(99999)
