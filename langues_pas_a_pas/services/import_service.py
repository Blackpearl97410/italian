from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from database.repositories.situation_repository import SituationRepository
from domain.models import Exercise, GrammarPoint, Phrase, Situation, Source
from domain.schemas import ImportResult


REQUIRED_SOURCE_FIELDS = {
    "name",
    "url",
    "source_type",
    "license",
    "retrieved_at",
    "reliability_score",
    "notes",
}
REQUIRED_SITUATION_FIELDS = {"slug", "title", "level", "objective", "phrases", "exercises"}
REQUIRED_PHRASE_FIELDS = {"fr_text", "en_text", "it_text", "explanation", "common_trap"}
REQUIRED_EXERCISE_FIELDS = {
    "type",
    "question",
    "correct_answer",
    "explanation_correct",
    "explanation_wrong",
    "difficulty",
}


class ImportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.situations = SituationRepository(session)

    def validate_file(self, path: Path) -> ImportResult:
        try:
            payload = self._read_payload(path)
        except Exception as exc:
            return ImportResult(valid=False, errors=[f"Lecture impossible : {exc}"])
        return self.validate_payload(payload)

    def import_file(self, path: Path) -> ImportResult:
        try:
            payload = self._read_payload(path)
        except Exception as exc:
            return ImportResult(valid=False, errors=[f"Lecture impossible : {exc}"])
        return self.import_payload(payload)

    def validate_payload(self, payload: dict[str, Any]) -> ImportResult:
        errors: list[str] = []
        source = payload.get("source")
        if not isinstance(source, dict):
            errors.append("Le bloc source est obligatoire.")
        else:
            errors.extend(self._missing_errors(source, REQUIRED_SOURCE_FIELDS, "source"))
            if "retrieved_at" in source:
                self._parse_date(source["retrieved_at"], errors, "source.retrieved_at")
        situations = payload.get("situations")
        if not isinstance(situations, list) or not situations:
            errors.append("Le tableau situations doit contenir au moins une situation.")
        else:
            for index, situation in enumerate(situations):
                prefix = f"situations[{index}]"
                if not isinstance(situation, dict):
                    errors.append(f"{prefix} doit etre un objet.")
                    continue
                errors.extend(self._missing_errors(situation, REQUIRED_SITUATION_FIELDS, prefix))
                if situation.get("level") not in {"A1", "A2", "B1"}:
                    errors.append(f"{prefix}.level doit etre A1, A2 ou B1.")
                phrases = situation.get("phrases", [])
                if not isinstance(phrases, list) or not phrases:
                    errors.append(f"{prefix}.phrases doit contenir au moins une phrase.")
                else:
                    for phrase_index, phrase in enumerate(phrases):
                        errors.extend(
                            self._missing_errors(
                                phrase,
                                REQUIRED_PHRASE_FIELDS,
                                f"{prefix}.phrases[{phrase_index}]",
                            )
                        )
                exercises = situation.get("exercises", [])
                if not isinstance(exercises, list) or not exercises:
                    errors.append(f"{prefix}.exercises doit contenir au moins un exercice.")
                else:
                    for exercise_index, exercise in enumerate(exercises):
                        errors.extend(
                            self._missing_errors(
                                exercise,
                                REQUIRED_EXERCISE_FIELDS,
                                f"{prefix}.exercises[{exercise_index}]",
                            )
                        )
        return ImportResult(valid=not errors, errors=errors)

    def import_payload(self, payload: dict[str, Any]) -> ImportResult:
        validation = self.validate_payload(payload)
        if not validation.valid:
            return validation
        source = self._get_or_create_source(payload["source"])
        imported = 0
        for index, item in enumerate(payload["situations"], start=1):
            if self.situations.get_by_slug(item["slug"]):
                continue
            situation = Situation(
                slug=item["slug"],
                title=item["title"],
                level=item["level"],
                objective=item["objective"],
                order_index=item.get("order_index", index),
            )
            self.session.add(situation)
            self.session.flush()
            phrases = self._create_phrases(item, situation.id, source.id)
            self.session.flush()
            phrase_by_fr = {phrase.fr_text: phrase for phrase in phrases}
            for grammar in item.get("grammar_points", []):
                self.session.add(
                    GrammarPoint(
                        situation_id=situation.id,
                        title=grammar.get("title", "Point grammatical"),
                        explanation=grammar.get("explanation", ""),
                        example_fr=grammar.get("example_fr", ""),
                        example_en=grammar.get("example_en", ""),
                        example_it=grammar.get("example_it", ""),
                        source_id=source.id,
                    )
                )
            for exercise in item["exercises"]:
                linked_phrase = phrase_by_fr.get(exercise.get("phrase_fr", ""))
                self.session.add(
                    Exercise(
                        situation_id=situation.id,
                        phrase_id=linked_phrase.id if linked_phrase else None,
                        type=exercise["type"],
                        question=exercise["question"],
                        correct_answer=exercise["correct_answer"],
                        options_json=json.dumps(exercise.get("options", []), ensure_ascii=False),
                        explanation_correct=exercise["explanation_correct"],
                        explanation_wrong=exercise["explanation_wrong"],
                        difficulty=int(exercise["difficulty"]),
                        source_id=source.id,
                    )
                )
            imported += 1
        self.session.commit()
        return ImportResult(valid=True, errors=[], imported_situations=imported)

    def _create_phrases(self, item: dict[str, Any], situation_id: int, source_id: int) -> list[Phrase]:
        phrases: list[Phrase] = []
        for phrase in item["phrases"]:
            row = Phrase(
                situation_id=situation_id,
                fr_text=phrase["fr_text"],
                en_text=phrase["en_text"],
                it_text=phrase["it_text"],
                pronunciation_en=phrase.get("pronunciation_en"),
                pronunciation_it=phrase.get("pronunciation_it"),
                explanation=phrase["explanation"],
                common_trap=phrase["common_trap"],
                source_id=source_id,
            )
            self.session.add(row)
            phrases.append(row)
        return phrases

    def _get_or_create_source(self, source_payload: dict[str, Any]) -> Source:
        source = self.session.query(Source).filter(Source.url == source_payload["url"]).first()
        if source:
            return source
        source = Source(
            name=source_payload["name"],
            url=source_payload["url"],
            source_type=source_payload["source_type"],
            license=source_payload["license"],
            retrieved_at=date.fromisoformat(source_payload["retrieved_at"]),
            reliability_score=int(source_payload["reliability_score"]),
            notes=source_payload["notes"],
        )
        self.session.add(source)
        self.session.flush()
        return source

    def _read_payload(self, path: Path) -> dict[str, Any]:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix.lower() == ".csv":
            return self._read_csv_payload(path)
        raise ValueError("Format non supporte. Utilisez JSON ou CSV.")

    def _read_csv_payload(self, path: Path) -> dict[str, Any]:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        if not rows:
            raise ValueError("CSV vide.")
        first = rows[0]
        source = {
            "name": first.get("source_name", "Import CSV manuel"),
            "url": first.get("source_url", "manual://csv-import"),
            "source_type": first.get("source_type", "manual"),
            "license": first.get("license", "manual"),
            "retrieved_at": first.get("retrieved_at", date.today().isoformat()),
            "reliability_score": int(first.get("reliability_score", 3)),
            "notes": first.get("source_notes", "Import CSV valide manuellement."),
        }
        situations: dict[str, dict[str, Any]] = {}
        for row in rows:
            slug = row["slug"]
            situation = situations.setdefault(
                slug,
                {
                    "slug": slug,
                    "title": row["title"],
                    "level": row["level"],
                    "objective": row["objective"],
                    "phrases": [],
                    "exercises": [],
                },
            )
            situation["phrases"].append(
                {
                    "fr_text": row["fr_text"],
                    "en_text": row["en_text"],
                    "it_text": row["it_text"],
                    "explanation": row["explanation"],
                    "common_trap": row["common_trap"],
                }
            )
            if row.get("question"):
                situation["exercises"].append(
                    {
                        "type": row.get("exercise_type", "fill_blank"),
                        "question": row["question"],
                        "correct_answer": row["correct_answer"],
                        "options": [value for value in row.get("options", "").split("|") if value],
                        "explanation_correct": row.get("explanation_correct", "Bien joue."),
                        "explanation_wrong": row.get("explanation_wrong", "Relisez la comparaison."),
                        "difficulty": int(row.get("difficulty", 1)),
                    }
                )
        return {"source": source, "situations": list(situations.values())}

    def _missing_errors(self, payload: Any, fields: set[str], prefix: str) -> list[str]:
        if not isinstance(payload, dict):
            return [f"{prefix} doit etre un objet."]
        return [f"{prefix}.{field} est obligatoire." for field in sorted(fields) if not payload.get(field)]

    def _parse_date(self, value: str, errors: list[str], field: str) -> None:
        try:
            date.fromisoformat(value)
        except ValueError:
            errors.append(f"{field} doit etre une date ISO YYYY-MM-DD.")

