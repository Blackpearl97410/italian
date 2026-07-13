from __future__ import annotations

from sqlalchemy.orm import Session

from domain.models import Base, Language


def init_db(engine) -> None:
    Base.metadata.create_all(bind=engine)


def ensure_languages(session: Session) -> None:
    languages = [("fr", "Francais"), ("en", "Anglais"), ("it", "Italien")]
    for code, name in languages:
        exists = session.query(Language).filter(Language.code == code).first()
        if not exists:
            session.add(Language(code=code, name=name))
    session.commit()

