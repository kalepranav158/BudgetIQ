from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

import joblib
import django
from django.conf import settings as django_settings
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.svm import LinearSVC

from ml.artifacts import build_manifest_path, build_versioned_path, generate_artifact_version, write_manifest
from ml.features import build_features
from ml.utils import normalize_text


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


def _split_train_validation(texts: list[str], labels: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    if len(texts) < 4 or len(set(labels)) < 2:
        return texts, [], labels, []

    counts = Counter(labels)
    if min(counts.values()) < 2:
        return texts, [], labels, []

    class_count = len(set(labels))
    test_size = max(class_count, int(round(len(texts) * 0.25)))
    if len(texts) - test_size < class_count:
        test_size = len(texts) - class_count

    if test_size < class_count or test_size <= 0:
        return texts, [], labels, []

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
    train_idx, val_idx = next(splitter.split(texts, labels))
    train_texts = [texts[i] for i in train_idx]
    validation_texts = [texts[i] for i in val_idx]
    train_labels = [labels[i] for i in train_idx]
    validation_labels = [labels[i] for i in val_idx]
    return train_texts, validation_texts, train_labels, validation_labels


def _load_trainable_classes(class_audit_path: Path) -> list[str] | None:
    if not class_audit_path.exists():
        return None
    try:
        payload = json.loads(class_audit_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(payload, dict):
        return None

    trainable: list[str] = []
    for category, meta in payload.items():
        if not isinstance(meta, dict):
            continue
        if bool(meta.get("trainable", False)):
            trainable.append(normalize_text(category))

    return sorted({category for category in trainable if category}) or None


def train_model(
    dataset_path: Path,
    model_path: Path,
    vectorizer_path: Path,
    class_audit_path: Path | None = None,
) -> int:
    rows: list[dict[str, str]] = []
    labels: list[str] = []

    with dataset_path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    trainable_classes = _load_trainable_classes(class_audit_path or Path("ml/data/class_audit.json"))

    feature_rows = build_features(rows)
    texts: list[str] = []
    for feature_row in feature_rows:
        text = normalize_text(feature_row.get("combined_text", ""))
        category = normalize_text(feature_row.get("category", ""))
        if trainable_classes and category not in trainable_classes:
            continue
        if text and category:
            texts.append(text)
            labels.append(category)

    if not texts:
        raise ValueError('Training dataset is empty. Run ml/preprocessing/build_dataset.py after importing transactions.')

    train_texts, validation_texts, train_labels, validation_labels = _split_train_validation(texts, labels)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, strip_accents='unicode', sublinear_tf=True)
    train_features = vectorizer.fit_transform(train_texts)

    candidate_models = {
        "logreg_balanced": LogisticRegression(
            class_weight="balanced",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            multi_class="multinomial",
        ),
        "linearsvc_balanced": CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", C=0.5, max_iter=2000),
            cv=3,
        ),
    }

    fitted_models: dict[str, object] = {}
    for name, candidate in candidate_models.items():
        candidate.fit(train_features, train_labels)
        fitted_models[name] = candidate

    winner_name = "logreg_balanced"
    model = fitted_models[winner_name]

    metrics = {
        "training_samples": len(train_texts),
        "validation_samples": len(validation_texts),
        "classes": sorted(set(labels)),
        "trainable_classes": trainable_classes or sorted(set(labels)),
    }

    if validation_texts:
        validation_features = vectorizer.transform(validation_texts)

        candidate_scores: dict[str, dict[str, float]] = {}
        winner_macro_f1 = -1.0
        winner_preds = None
        for name, fitted_model in fitted_models.items():
            preds = fitted_model.predict(validation_features)
            macro_f1 = f1_score(validation_labels, preds, average="macro", zero_division=0)
            weighted_f1 = f1_score(validation_labels, preds, average="weighted", zero_division=0)
            accuracy = accuracy_score(validation_labels, preds)
            candidate_scores[name] = {
                "validation_accuracy": float(accuracy),
                "validation_macro_f1": float(macro_f1),
                "validation_weighted_f1": float(weighted_f1),
            }
            if macro_f1 >= winner_macro_f1:
                winner_macro_f1 = float(macro_f1)
                winner_name = name
                model = fitted_model
                winner_preds = preds

        predictions = winner_preds if winner_preds is not None else model.predict(validation_features)
        report = classification_report(validation_labels, predictions, output_dict=True, zero_division=0)

        metrics.update(
            {
                "winner": winner_name,
                "candidate_scores": candidate_scores,
                "validation_accuracy": accuracy_score(validation_labels, predictions),
                "validation_macro_f1": f1_score(validation_labels, predictions, average="macro", zero_division=0),
                "validation_weighted_f1": f1_score(validation_labels, predictions, average="weighted", zero_division=0),
                "per_class_report": report,
            }
        )
    else:
        metrics.update(
            {
                "winner": winner_name,
                "candidate_scores": {},
                "validation_accuracy": None,
                "validation_macro_f1": None,
                "validation_weighted_f1": None,
                "per_class_report": {},
            }
        )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    vectorizer_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_version = generate_artifact_version()
    versioned_model_path = build_versioned_path(model_path, artifact_version)
    versioned_vectorizer_path = build_versioned_path(vectorizer_path, artifact_version)
    versioned_metrics_path = model_path.with_name(f"{model_path.stem}.{artifact_version}.metrics.json")

    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(model, versioned_model_path)
    joblib.dump(vectorizer, versioned_vectorizer_path)

    metrics_path = model_path.with_suffix('.metrics.json')
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    versioned_metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')

    manifest_payload = {
        "version": artifact_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "training_samples": len(train_texts),
        "validation_samples": len(validation_texts),
        "classes": sorted(set(labels)),
        "winner": winner_name,
        "model_path": str(versioned_model_path),
        "vectorizer_path": str(versioned_vectorizer_path),
        "metrics_path": str(versioned_metrics_path),
        "latest_model_path": str(model_path),
        "latest_vectorizer_path": str(vectorizer_path),
    }
    manifest_payload.update(metrics)
    write_manifest(build_manifest_path(model_path), manifest_payload)

    return len(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description='Train a TF-IDF + Logistic Regression transaction classifier.')
    parser.add_argument('--dataset', default='ml/data/training_dataset.csv', help='CSV dataset path')
    parser.add_argument(
        '--model-path',
        default=str(getattr(django_settings, 'ML_MODEL_PATH', 'ml/models/transaction_classifier.joblib')),
        help='Joblib output for the classifier',
    )
    parser.add_argument(
        '--vectorizer-path',
        default=str(getattr(django_settings, 'ML_VECTORIZER_PATH', 'ml/models/transaction_vectorizer.joblib')),
        help='Joblib output for the vectorizer',
    )
    parser.add_argument(
        '--class-audit',
        default='ml/data/class_audit.json',
        help='Optional class-audit JSON path to filter non-trainable categories',
    )
    args = parser.parse_args()

    rows = train_model(
        dataset_path=Path(args.dataset),
        model_path=Path(args.model_path),
        vectorizer_path=Path(args.vectorizer_path),
        class_audit_path=Path(args.class_audit),
    )
    print(f'Trained classifier on {rows} labeled transactions')


if __name__ == '__main__':
    main()
