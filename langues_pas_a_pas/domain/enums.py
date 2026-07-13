from __future__ import annotations

from enum import StrEnum


class Level(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"


class ExerciseType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ERROR_CORRECTION = "error_correction"

