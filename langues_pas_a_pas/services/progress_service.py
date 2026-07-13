from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.repositories.progress_repository import ProgressRepository
from domain.models import UserAnswer


class ProgressService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.progress = ProgressRepository(session)

    def mark_opened(self, situation_id: int) -> None:
        progress = self.progress.get_or_create(situation_id)
        progress.last_opened_at = datetime.now(timezone.utc)
        self.session.commit()

    def save_answer(self, exercise_id: int, user_answer: str, is_correct: bool, feedback: str) -> None:
        self.progress.add_answer(
            UserAnswer(
                exercise_id=exercise_id,
                user_answer=user_answer,
                is_correct=is_correct,
                feedback=feedback,
            )
        )

    def update_situation_score(self, situation_id: int, correct_count: int, total_count: int) -> None:
        progress = self.progress.get_or_create(situation_id)
        progress.score = 0.0 if total_count == 0 else round((correct_count / total_count) * 100, 1)
        progress.completed = total_count > 0 and correct_count == total_count
        progress.last_opened_at = datetime.now(timezone.utc)
        progress.completed_at = datetime.now(timezone.utc) if progress.completed else None
        self.session.commit()

    def dashboard_stats(self) -> dict[str, float | int]:
        rows = self.progress.list_progress()
        started = sum(1 for row in rows if row.last_opened_at is not None)
        completed = sum(1 for row in rows if row.completed)
        average = round(sum(row.score for row in rows) / len(rows), 1) if rows else 0.0
        return {"started": started, "completed": completed, "average_score": average}

