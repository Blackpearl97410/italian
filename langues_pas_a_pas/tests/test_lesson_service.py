from __future__ import annotations

from pathlib import Path

from services.import_service import ImportService
from services.lesson_service import LessonService


def test_retrieves_seed_situations(session) -> None:
    seed_path = Path(__file__).resolve().parents[1] / "data" / "seed" / "situations_seed.json"
    ImportService(session).import_file(seed_path)
    situations = LessonService(session).list_situations()
    assert len(situations) == 5
    assert situations[0].slug == "se-presenter"

