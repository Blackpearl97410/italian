from __future__ import annotations

from sqlalchemy.orm import Session

from domain.models import Exercise


class ExerciseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_situation(self, situation_id: int) -> list[Exercise]:
        return (
            self.session.query(Exercise)
            .filter(Exercise.situation_id == situation_id)
            .order_by(Exercise.id)
            .all()
        )

    def get(self, exercise_id: int) -> Exercise | None:
        return self.session.query(Exercise).filter(Exercise.id == exercise_id).first()

