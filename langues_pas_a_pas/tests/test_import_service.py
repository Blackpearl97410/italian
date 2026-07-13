from __future__ import annotations

from services.import_service import ImportService


def valid_payload() -> dict:
    return {
        "source": {
            "name": "Manual",
            "url": "manual://test",
            "source_type": "manual",
            "license": "manual",
            "retrieved_at": "2026-07-07",
            "reliability_score": 4,
            "notes": "Test.",
        },
        "situations": [
            {
                "slug": "test",
                "title": "Test",
                "level": "A1",
                "objective": "Tester.",
                "phrases": [
                    {
                        "fr_text": "Bonjour.",
                        "en_text": "Hello.",
                        "it_text": "Buongiorno.",
                        "explanation": "Equivalent simple.",
                        "common_trap": "Ciao est plus familier.",
                    }
                ],
                "exercises": [
                    {
                        "type": "multiple_choice",
                        "question": "Question",
                        "correct_answer": "Hello",
                        "options": ["Hello", "Bye"],
                        "explanation_correct": "Oui.",
                        "explanation_wrong": "Non.",
                        "difficulty": 1,
                    }
                ],
            }
        ],
    }


def test_validate_import_payload(session) -> None:
    result = ImportService(session).validate_payload(valid_payload())
    assert result.valid
    assert result.errors == []


def test_import_skips_duplicate_slug(session) -> None:
    service = ImportService(session)
    first = service.import_payload(valid_payload())
    second = service.import_payload(valid_payload())
    assert first.imported_situations == 1
    assert second.imported_situations == 0


def test_invalid_import_reports_missing_fields(session) -> None:
    payload = valid_payload()
    del payload["source"]["url"]
    result = ImportService(session).validate_payload(payload)
    assert not result.valid
    assert "source.url est obligatoire." in result.errors

