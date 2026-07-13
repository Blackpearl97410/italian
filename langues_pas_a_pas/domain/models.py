from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    license: Mapped[str] = mapped_column(String(120), nullable=False)
    retrieved_at: Mapped[date] = mapped_column(Date, nullable=False)
    reliability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    notes: Mapped[str] = mapped_column(Text, default="")


class Situation(Base):
    __tablename__ = "situations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    level: Mapped[str] = mapped_column(String(8), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    phrases: Mapped[list["Phrase"]] = relationship(back_populates="situation", cascade="all, delete-orphan")
    grammar_points: Mapped[list["GrammarPoint"]] = relationship(back_populates="situation", cascade="all, delete-orphan")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="situation", cascade="all, delete-orphan")


class Phrase(Base):
    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    situation_id: Mapped[int] = mapped_column(ForeignKey("situations.id"), nullable=False)
    fr_text: Mapped[str] = mapped_column(Text, nullable=False)
    en_text: Mapped[str] = mapped_column(Text, nullable=False)
    it_text: Mapped[str] = mapped_column(Text, nullable=False)
    pronunciation_en: Mapped[str | None] = mapped_column(String(240))
    pronunciation_it: Mapped[str | None] = mapped_column(String(240))
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    common_trap: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    situation: Mapped[Situation] = relationship(back_populates="phrases")
    source: Mapped[Source] = relationship()
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="phrase")
    review_item: Mapped["ReviewItem | None"] = relationship(back_populates="phrase")


class GrammarPoint(Base):
    __tablename__ = "grammar_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    situation_id: Mapped[int] = mapped_column(ForeignKey("situations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    example_fr: Mapped[str] = mapped_column(Text, nullable=False)
    example_en: Mapped[str] = mapped_column(Text, nullable=False)
    example_it: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    situation: Mapped[Situation] = relationship(back_populates="grammar_points")
    source: Mapped[Source] = relationship()


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    situation_id: Mapped[int] = mapped_column(ForeignKey("situations.id"), nullable=False)
    phrase_id: Mapped[int | None] = mapped_column(ForeignKey("phrases.id"))
    type: Mapped[str] = mapped_column(String(60), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    explanation_correct: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_wrong: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    situation: Mapped[Situation] = relationship(back_populates="exercises")
    phrase: Mapped[Phrase | None] = relationship(back_populates="exercises")
    source: Mapped[Source] = relationship()
    answers: Mapped[list["UserAnswer"]] = relationship(back_populates="exercise")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    situation_id: Mapped[int] = mapped_column(ForeignKey("situations.id"), unique=True, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    situation: Mapped[Situation] = relationship()


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    exercise: Mapped[Exercise] = relationship(back_populates="answers")


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id"), unique=True, nullable=False)
    strength: Mapped[int] = mapped_column(Integer, default=1)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)

    phrase: Mapped[Phrase] = relationship(back_populates="review_item")

