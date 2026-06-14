from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import joblib

from ml.artifacts import resolve_artifact_paths
from ml.utils import normalize_text


ALLOWED_CATEGORIES = {
    "cash_withdrawal",
    "extra",
    "lunch",
    "other",
    "recharge",
    "tea",
    "credit",
}


class HybridTransactionCategorizer:
    """Optional ML predictor for transaction categorization.

    The predictor loads a joblib classifier and vectorizer lazily. If either
    artifact is unavailable or invalid, prediction returns None instead of
    raising.
    """

    def __init__(self, model_path: str | None = None, vectorizer_path: str | None = None) -> None:
        self.model_path = Path(model_path or os.getenv("ML_MODEL_PATH", "ml/models/transaction_classifier.joblib"))
        self.vectorizer_path = Path(
            vectorizer_path or os.getenv("ML_VECTORIZER_PATH", "ml/models/transaction_vectorizer.joblib")
        )
        self._model: Any = None
        self._vectorizer: Any = None
        self._loaded = False

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return True

        model_path, vectorizer_path = resolve_artifact_paths(self.model_path, self.vectorizer_path)
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path

        if not self.model_path.exists() or not self.vectorizer_path.exists():
            return False

        try:
            self._model = joblib.load(self.model_path)
            self._vectorizer = joblib.load(self.vectorizer_path)
        except Exception:
            self._model = None
            self._vectorizer = None
            return False

        self._loaded = True
        return True

    def predict_category(self, description: str, counterparty: str = "", direction: str = "debit") -> str | None:
        if not self._ensure_loaded():
            return None

        text = normalize_text(f"{counterparty} {description} {direction}")
        if not text:
            return None

        try:
            features = self._vectorizer.transform([text])
            prediction = self._model.predict(features)[0]
        except Exception:
            return None

        category = normalize_text(prediction)
        return category if category in ALLOWED_CATEGORIES else None


def main() -> None:
    parser = argparse.ArgumentParser(description='Predict a transaction category using the hybrid rule and ML pipeline.')
    parser.add_argument('text', help='Transaction text, for example: Paid to mess')
    parser.add_argument('--counterparty', default='', help='Optional extracted merchant or counterparty text')
    parser.add_argument('--direction', default='debit', choices=['debit', 'credit'], help='Transaction direction')
    parser.add_argument('--model-path', default=None, help='Optional path to the classifier artifact')
    parser.add_argument('--vectorizer-path', default=None, help='Optional path to the vectorizer artifact')
    args = parser.parse_args()

    categorizer = HybridTransactionCategorizer(model_path=args.model_path, vectorizer_path=args.vectorizer_path)
    category = categorizer.predict_category(
        description=args.text,
        counterparty=args.counterparty,
        direction=args.direction,
    )
    print(f"category={category or 'none'} source={'ml' if category else 'none'}")


if __name__ == '__main__':
    main()
