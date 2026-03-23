from __future__ import annotations

from pathlib import Path
from typing import Iterable

from backend.config.settings import settings

try:
    import joblib
except ImportError:  # pragma: no cover - optional during first install
    joblib = None


class TransactionClassifier:
    def __init__(
        self,
        model_path: Path | None = None,
        vectorizer_path: Path | None = None,
    ) -> None:
        self.model_path = model_path or settings.model_path
        self.vectorizer_path = vectorizer_path or settings.vectorizer_path
        self.model = None
        self.vectorizer = None
        self._load_artifacts()

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.vectorizer is not None

    def _load_artifacts(self) -> None:
        if joblib is None:
            return
        if not self.model_path.exists() or not self.vectorizer_path.exists():
            return
        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)

    def predict(self, texts: Iterable[str]) -> list[str]:
        if not self.is_ready:
            return []
        features = self.vectorizer.transform(list(texts))
        predictions = self.model.predict(features)
        return [str(item) for item in predictions]
