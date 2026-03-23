from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def _env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in {None, ''} else default


@dataclass(frozen=True)
class Settings:
    root_dir: Path = Path(__file__).resolve().parents[2]
    app_name: str = _env_or_default("APP_NAME", "Smart Budget ML System")
    environment: str = _env_or_default("APP_ENV", "development")
    enable_ml_categorization: bool = _env_or_default("ENABLE_ML_CATEGORIZATION", "0") == "1"
    default_pdf_password: str = os.getenv("BANK_PDF_PASSWORD", "")
    category_rules_path: Path = root_dir / "backend" / "config" / "category_rules.json"
    model_path: Path = root_dir / "ml" / "models" / "transaction_classifier.joblib"
    vectorizer_path: Path = root_dir / "ml" / "models" / "transaction_vectorizer.joblib"
    database_file: Path = root_dir / "database" / "connection" / "smart_budget.db"
    database_url: str = _env_or_default(
        "DATABASE_URL",
        f"sqlite:///{(root_dir / 'database' / 'connection' / 'smart_budget.db').as_posix()}",
    )


settings = Settings()
