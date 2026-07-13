from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
IMPORTS_DIR = DATA_DIR / "imports"
APP_DATA_DIR = Path.home() / ".langues_pas_a_pas"
DB_PATH = APP_DATA_DIR / "langues_pas_a_pas.sqlite3"


def ensure_app_dirs() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)

