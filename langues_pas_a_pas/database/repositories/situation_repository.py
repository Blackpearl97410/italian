from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from domain.models import Situation


class SituationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Situation]:
        return (
            self.session.query(Situation)
            .order_by(Situation.order_index, Situation.title)
            .all()
        )

    def get(self, situation_id: int) -> Situation | None:
        return (
            self.session.query(Situation)
            .options(joinedload(Situation.phrases), joinedload(Situation.grammar_points))
            .filter(Situation.id == situation_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Situation | None:
        return self.session.query(Situation).filter(Situation.slug == slug).first()

