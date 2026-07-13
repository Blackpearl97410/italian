from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.paths import SEED_DIR
from database.db import engine, create_session
from database.init_db import ensure_languages, init_db
from database.seed_data import seed_database


def main() -> None:
    init_db(engine)
    session = create_session()
    try:
        ensure_languages(session)
        seed_database(session, SEED_DIR / "situations_seed.json")
    finally:
        session.close()
    print("Base SQLite initialisee.")


if __name__ == "__main__":
    main()
