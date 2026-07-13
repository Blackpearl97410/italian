from __future__ import annotations

from sqlalchemy.orm import Session

from domain.models import Phrase


class PhraseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_situation(self, situation_id: int) -> list[Phrase]:
        return (
            self.session.query(Phrase)
            .filter(Phrase.situation_id == situation_id)
            .order_by(Phrase.id)
            .all()
        )

