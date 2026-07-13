from __future__ import annotations

from dataclasses import dataclass

from app.paths import DB_PATH


@dataclass(frozen=True)
class Settings:
    app_name: str = "Langues Pas a Pas"
    database_url: str = f"sqlite:///{DB_PATH}"


settings = Settings()

