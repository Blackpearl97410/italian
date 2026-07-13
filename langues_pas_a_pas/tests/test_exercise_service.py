from __future__ import annotations

from datetime import date

from domain.models import Exercise, Phrase, Situation, Source
from services.exercise_service import ExerciseService


def test_exercise_answer_saves_feedback_and_review(session) -> None:
    source = Source(
        name="Manual",
        url="manual://exercise",
        source_type="manual",
        license="manual",
        retrieved_at=date(2026, 7, 7),
        reliability_score=4,
        notes="Test",
    )
    situation = Situation(slug="hungry", title="Faim", level="A1", objective="Tester", order_index=1)
    session.add_all([source, situation])
    session.flush()
    phrase = Phrase(
        situation_id=situation.id,
        fr_text="J'ai faim.",
        en_text="I am hungry.",
        it_text="Ho fame.",
        explanation="Avoir en FR/IT, etre en EN.",
        common_trap="I have hungry.",
        source_id=source.id,
    )
    session.add(phrase)
    session.flush()
    exercise = Exercise(
        situation_id=situation.id,
        phrase_id=phrase.id,
        type="error_correction",
        question="Corrigez: I have hungry.",
        correct_answer="I am hungry",
        explanation_correct="Hungry utilise etre.",
        explanation_wrong="En anglais, on dit I am hungry.",
        difficulty=2,
        source_id=source.id,
    )
    session.add(exercise)
    session.commit()
    feedback = ExerciseService(session).answer(exercise, "I have hungry")
    assert not feedback.is_correct
    assert phrase.review_item is not None
    assert phrase.review_item.mistake_count == 1

