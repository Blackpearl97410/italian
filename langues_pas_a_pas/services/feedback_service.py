from __future__ import annotations

import re
import unicodedata

from domain.models import Exercise
from domain.schemas import Feedback


def normalize_answer(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[.?!,;:'\"`]", "", normalized)
    return re.sub(r"\s+", " ", normalized)


class FeedbackService:
    def evaluate(self, exercise: Exercise, user_answer: str) -> Feedback:
        expected = normalize_answer(exercise.correct_answer)
        actual = normalize_answer(user_answer)
        is_correct = actual == expected
        if is_correct:
            message = f"Correct. {exercise.explanation_correct}"
        else:
            message = (
                f"Pas exactement. Reponse attendue : {exercise.correct_answer}.\n\n"
                f"{exercise.explanation_wrong}"
            )
        return Feedback(is_correct=is_correct, message=message)

