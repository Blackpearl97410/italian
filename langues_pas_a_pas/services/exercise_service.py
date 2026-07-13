from __future__ import annotations

from sqlalchemy.orm import Session

from database.repositories.exercise_repository import ExerciseRepository
from domain.models import Exercise
from domain.schemas import Feedback
from services.feedback_service import FeedbackService
from services.progress_service import ProgressService
from services.review_service import ReviewService


class ExerciseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.exercises = ExerciseRepository(session)
        self.feedback = FeedbackService()
        self.progress = ProgressService(session)
        self.review = ReviewService(session)

    def list_for_situation(self, situation_id: int) -> list[Exercise]:
        return self.exercises.list_for_situation(situation_id)

    def answer(self, exercise: Exercise, user_answer: str) -> Feedback:
        feedback = self.feedback.evaluate(exercise, user_answer)
        self.progress.save_answer(exercise.id, user_answer, feedback.is_correct, feedback.message)
        self.review.record_exercise_result(exercise.phrase_id, feedback.is_correct)
        self.session.commit()
        return feedback

