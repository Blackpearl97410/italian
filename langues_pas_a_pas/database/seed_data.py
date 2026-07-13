from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from services.import_service import ImportService


def seed_database(session: Session, seed_path: Path) -> None:
    service = ImportService(session)
    service.import_file(seed_path)

