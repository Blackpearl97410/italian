from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportResult:
    valid: bool
    errors: list[str]
    imported_situations: int = 0


@dataclass(frozen=True)
class Feedback:
    is_correct: bool
    message: str

