from __future__ import annotations

import json
from dataclasses import dataclass

from backend.config.settings import settings
from backend.models.classifier import TransactionClassifier
from backend.utils.preprocessing import normalize_text


@dataclass(frozen=True)
class CategoryDecision:
    category: str
    source: str
    predicted_category: str | None = None


class HybridTransactionCategorizer:
    def __init__(self, classifier: TransactionClassifier | None = None) -> None:
        self.enable_ml = settings.enable_ml_categorization
        self.classifier = None
        if self.enable_ml:
            self.classifier = classifier or TransactionClassifier()
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, dict[str, str] | dict[str, list[str]]]:
        if not settings.category_rules_path.exists():
            return {"counterparty_rules": {}, "keyword_rules": {}}
        with settings.category_rules_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def categorize(
        self,
        description: str,
        counterparty: str | None,
        direction: str,
        stored_mappings: dict[str, str] | None = None,
    ) -> CategoryDecision:
        normalized_description = normalize_text(description).lower()
        normalized_counterparty = normalize_text(counterparty).lower()
        known_mappings = stored_mappings or {}

        if normalized_counterparty and normalized_counterparty in known_mappings:
            return CategoryDecision(category=known_mappings[normalized_counterparty], source="mapping")

        for alias, category in self.rules.get("counterparty_rules", {}).items():
            if alias in normalized_counterparty:
                return CategoryDecision(category=category, source="rule")

        combined_text = f"{normalized_counterparty} {normalized_description}".strip()
        for category, keywords in self.rules.get("keyword_rules", {}).items():
            if any(keyword in combined_text for keyword in keywords):
                return CategoryDecision(category=category, source="rule")

        if direction == "credit":
            return CategoryDecision(category="income", source="rule")

        if self.enable_ml and self.classifier is not None:
            predictions = self.classifier.predict([combined_text])
            if predictions:
                prediction = predictions[0]
                return CategoryDecision(category=prediction, source="ml", predicted_category=prediction)

        return CategoryDecision(category="other", source="fallback")
