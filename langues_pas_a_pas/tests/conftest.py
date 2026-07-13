from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.init_db import ensure_languages, init_db


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    init_db(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    db = TestingSession()
    ensure_languages(db)
    try:
        yield db
    finally:
        db.close()

