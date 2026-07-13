from __future__ import annotations

from sqlalchemy.orm import Session

from domain.models import Source


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_url(self, url: str) -> Source | None:
        return self.session.query(Source).filter(Source.url == url).first()

