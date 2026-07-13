from __future__ import annotations

from sqlalchemy.orm import Session

from domain.models import UserAnswer, UserProgress


class ProgressRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, situation_id: int) -> UserProgress:
        progress = (
            self.session.query(UserProgress)
            .filter(UserProgress.situation_id == situation_id)
            .first()
        )
        if progress is None:
            progress = UserProgress(situation_id=situation_id)
            self.session.add(progress)
            self.session.flush()
        return progress

    def add_answer(self, answer: UserAnswer) -> None:
        self.session.add(answer)

    def list_answers(self) -> list[UserAnswer]:
        return self.session.query(UserAnswer).order_by(UserAnswer.created_at.desc()).all()

    def list_progress(self) -> list[UserProgress]:
        return self.session.query(UserProgress).all()

