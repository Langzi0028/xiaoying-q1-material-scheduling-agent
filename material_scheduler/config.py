from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database_path: Path
    llm_base_url: str | None
    llm_api_key: str | None
    llm_model: str | None

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "Settings":
        root = project_root or PROJECT_ROOT
        dotenv = dotenv_values(root / ".env")

        def configured_value(name: str) -> str | None:
            return os.environ[name] if name in os.environ else dotenv.get(name)

        default_database = root / "data" / "material_scheduler.db"
        return cls(
            database_path=Path(configured_value("MATERIAL_SCHEDULER_DB_PATH") or default_database),
            llm_base_url=configured_value("LLM_BASE_URL"),
            llm_api_key=configured_value("LLM_API_KEY"),
            llm_model=configured_value("LLM_MODEL"),
        )
