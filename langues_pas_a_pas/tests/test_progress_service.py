from __future__ import annotations

from domain.models import Situation
from services.progress_service import ProgressService


def test_progress_score_calculation(session) -> None:
    situation = Situation(slug="score", title="Score", level="A1", objective="Tester", order_index=1)
    session.add(situation)
    session.commit()
    service = ProgressService(session)
    service.update_situation_score(situation.id, correct_count=1, total_count=2)
    stats = service.dashboard_stats()
    assert stats["started"] == 1
    assert stats["average_score"] == 50.0

