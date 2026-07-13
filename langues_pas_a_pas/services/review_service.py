from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from domain.models import ReviewItem


class ReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_exercise_result(self, phrase_id: int | None, is_correct: bool) -> None:
        if phrase_id is None:
            return
        item = self.session.query(ReviewItem).filter(ReviewItem.phrase_id == phrase_id).first()
        if item is None:
            item = ReviewItem(phrase_id=phrase_id, strength=1)
            self.session.add(item)
            self.session.flush()
        if is_correct:
            item.strength = min(item.strength + 1, 5)
            item.next_review_at = datetime.now(timezone.utc) + timedelta(days=item.strength * 2)
        else:
            item.strength = max(item.strength - 1, 1)
            item.mistake_count += 1
            item.next_review_at = datetime.now(timezone.utc) + timedelta(hours=12)

    def due_items_count(self) -> int:
        return (
            self.session.query(ReviewItem)
            .filter(ReviewItem.next_review_at <= datetime.now(timezone.utc))
            .count()
        )

    def frequent_mistakes(self, limit: int = 5) -> list[ReviewItem]:
        return (
            self.session.query(ReviewItem)
            .filter(ReviewItem.mistake_count > 0)
            .order_by(ReviewItem.mistake_count.desc())
            .limit(limit)
            .all()
        )

