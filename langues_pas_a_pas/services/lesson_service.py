from __future__ import annotations

from sqlalchemy.orm import Session

from database.repositories.situation_repository import SituationRepository
from domain.models import Situation


class LessonService:
    def __init__(self, session: Session) -> None:
        self.situations = SituationRepository(session)

    def list_situations(self) -> list[Situation]:
        return self.situations.list_all()

    def get_situation(self, situation_id: int) -> Situation | None:
        return self.situations.get(situation_id)

