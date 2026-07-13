from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.db import create_session
from services.import_service import ImportService


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_content.py fichier.json")
        return 2
    session = create_session()
    try:
        result = ImportService(session).validate_file(Path(sys.argv[1]))
    finally:
        session.close()
    if result.valid:
        print("Contenu valide.")
        return 0
    print("Contenu invalide:")
    for error in result.errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
