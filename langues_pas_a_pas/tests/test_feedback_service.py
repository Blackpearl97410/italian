from __future__ import annotations

from domain.models import Exercise
from services.feedback_service import FeedbackService, normalize_answer


def test_normalize_answer_ignores_case_spaces_and_punctuation() -> None:
    assert normalize_answer(" My name is Alexandre! ") == "my name is alexandre"


def test_feedback_service_explains_wrong_answer() -> None:
    exercise = Exercise(
        situation_id=1,
        type="multiple_choice",
        question="Comment dit-on Je m'appelle ?",
        correct_answer="My name is Alexandre",
        explanation_correct="Formule naturelle.",
        explanation_wrong="On ne dit pas I call myself dans ce contexte.",
        difficulty=1,
        source_id=1,
    )
    feedback = FeedbackService().evaluate(exercise, "I call myself Alexandre")
    assert not feedback.is_correct
    assert "Pas exactement" in feedback.message
    assert "My name is Alexandre" in feedback.message

