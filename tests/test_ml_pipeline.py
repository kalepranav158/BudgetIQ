from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from uuid import uuid4

import django
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction
from ml.features import build_feature_row, build_features
from ml.inference.predict import HybridTransactionCategorizer
from ml.preprocessing.build_dataset import build_dataset
from ml.training.train_classifier import train_model


def test_build_dataset_exports_transaction_rows(tmp_path: Path) -> None:
    unique_description = f"ML EXPORT {uuid4().hex[:10].upper()}"
    Transaction.objects.create(
        date="2099-04-13",
        description=unique_description,
        amount="123.45",
        type="debit",
        subtype="expense",
        category="lunch",
        source_file="ml-test.pdf",
    )

    output_path = tmp_path / "training_dataset.csv"
    rows_written = build_dataset(output_path)

    assert rows_written >= 1
    assert output_path.exists()

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows
    assert any(row["text"] == unique_description.lower() and row["category"] == "lunch" for row in rows)


def test_train_model_writes_artifacts(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    dataset_path.write_text(
        "text,counterparty,category\n"
        "paid to mess,,lunch\n"
        "paid to tea stall,,lunch\n"
        "atm withdrawal,,cash_withdrawal\n"
        "cash withdrawal atm,,cash_withdrawal\n",
        encoding="utf-8",
    )

    model_path = tmp_path / "transaction_classifier.joblib"
    vectorizer_path = tmp_path / "transaction_vectorizer.joblib"

    rows = train_model(dataset_path, model_path, vectorizer_path)

    assert rows == 4
    assert model_path.exists()
    assert vectorizer_path.exists()

    metrics_path = model_path.with_suffix(".metrics.json")
    assert metrics_path.exists()

    manifest_path = model_path.with_name(f"{model_path.stem}.manifest.json")
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_model_path = Path(manifest["model_path"])
    versioned_vectorizer_path = Path(manifest["vectorizer_path"])
    versioned_metrics_path = Path(manifest["metrics_path"])

    assert manifest["version"].startswith("v")
    assert versioned_model_path.exists()
    assert versioned_vectorizer_path.exists()
    assert versioned_metrics_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["training_samples"] >= 2
    assert metrics["validation_samples"] >= 1
    assert metrics["validation_accuracy"] is not None
    assert metrics["validation_macro_f1"] is not None


def test_build_features_creates_structured_text() -> None:
    rows = build_features(
        [
            {
                "date": "2026-04-13",
                "description": "TRANSFER TO 4897694162092 UPI/DR/510791183658/MAYURESH/YESB/Q731754728/UPI",
                "amount": "249.00",
                "type": "debit",
                "subtype": "transfer_out",
                "category": "lunch",
            }
        ]
    )

    assert len(rows) == 1
    feature_row = rows[0]
    assert feature_row["amount_bucket"] in {"micro", "small"}
    assert feature_row["weekday"] == "mon"
    assert feature_row["month"] == "apr"
    assert "counterparty mayuresh" in feature_row["combined_text"]
    assert "subtype transfer_out" in feature_row["combined_text"]


def test_predict_category_returns_none_when_artifacts_missing(tmp_path: Path) -> None:
    categorizer = HybridTransactionCategorizer(
        model_path=str(tmp_path / "missing-model.joblib"),
        vectorizer_path=str(tmp_path / "missing-vectorizer.joblib"),
    )

    assert categorizer.predict_category("paid to mess") is None


def test_predict_category_uses_loaded_artifacts(tmp_path: Path) -> None:
    texts = ["paid to mess debit", "atm withdrawal debit"]
    labels = ["lunch", "cash_withdrawal"]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    features = vectorizer.fit_transform(texts)
    model = LogisticRegression(max_iter=200, class_weight="balanced")
    model.fit(features, labels)

    model_path = tmp_path / "transaction_classifier.joblib"
    vectorizer_path = tmp_path / "transaction_vectorizer.joblib"
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    categorizer = HybridTransactionCategorizer(model_path=str(model_path), vectorizer_path=str(vectorizer_path))

    assert categorizer.predict_category("paid to mess", counterparty="mess", direction="debit") == "lunch"
    assert categorizer.predict_category("atm withdrawal", counterparty="atm", direction="debit") == "cash_withdrawal"


def test_predict_category_resolves_versioned_artifacts_from_manifest(tmp_path: Path) -> None:
    texts = ["paid to mess debit", "atm withdrawal debit"]
    labels = ["lunch", "cash_withdrawal"]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    features = vectorizer.fit_transform(texts)
    model = LogisticRegression(max_iter=200, class_weight="balanced")
    model.fit(features, labels)

    legacy_model_path = tmp_path / "transaction_classifier.joblib"
    legacy_vectorizer_path = tmp_path / "transaction_vectorizer.joblib"
    version = "v20990101T000000Z-abcd1234"
    versioned_model_path = tmp_path / f"transaction_classifier.{version}.joblib"
    versioned_vectorizer_path = tmp_path / f"transaction_vectorizer.{version}.joblib"
    versioned_metrics_path = tmp_path / f"transaction_classifier.{version}.metrics.json"

    joblib.dump(model, versioned_model_path)
    joblib.dump(vectorizer, versioned_vectorizer_path)
    versioned_metrics_path.write_text(json.dumps({"version": version}), encoding="utf-8")

    manifest_path = tmp_path / "transaction_classifier.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": version,
                "model_path": str(versioned_model_path),
                "vectorizer_path": str(versioned_vectorizer_path),
                "metrics_path": str(versioned_metrics_path),
            }
        ),
        encoding="utf-8",
    )

    categorizer = HybridTransactionCategorizer(model_path=str(legacy_model_path), vectorizer_path=str(legacy_vectorizer_path))

    assert categorizer.predict_category("paid to mess", counterparty="mess", direction="debit") == "lunch"
