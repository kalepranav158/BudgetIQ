"""Two-stage hurdle model for daily spend forecasting.

Stage 1: Binary classifier (spend vs zero day).
Stage 2: Quantile regressor on non-zero spend days.

This architecture addresses zero-inflated forecasting and provides prediction intervals.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error
from math import sqrt

from ml.artifacts import build_manifest_path, build_versioned_path, generate_artifact_version, write_manifest


FEATURE_COLUMNS = [
    "lag_1",
    "lag_3_mean",
    "lag_7_mean",
    "lag_14_mean",
    "weekday",
    "month",
    "is_weekend",
]
TARGET_COLUMN = "target_total_debit"


@dataclass
class Dataset:
    features: list[list[float]]
    target: list[float]
    has_spend: list[int]  # 1 if target > 0, else 0


def _safe_float(value: str | float | int | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _load_dataset(dataset_path: Path) -> Dataset:
    """Load dataset and create binary spend labels (0 = zero day, 1 = spend day)."""
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    features = [[_safe_float(row.get(col)) for col in FEATURE_COLUMNS] for row in rows]
    target = [_safe_float(row.get(TARGET_COLUMN)) for row in rows]
    has_spend = [1 if t > 0 else 0 for t in target]

    return Dataset(features=features, target=target, has_spend=has_spend)


def _split_time_ordered(dataset: Dataset) -> tuple[Dataset, Dataset]:
    """80-20 stratified split (ensuring both classes in train & validation)."""
    total = len(dataset.target)
    if total < 5:
        return dataset, Dataset(features=[], target=[], has_spend=[])

    # Use stratified split to ensure both classes are represented
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(splitter.split(dataset.features, dataset.has_spend))

    train = Dataset(
        features=[dataset.features[i] for i in train_idx],
        target=[dataset.target[i] for i in train_idx],
        has_spend=[dataset.has_spend[i] for i in train_idx],
    )
    validation = Dataset(
        features=[dataset.features[i] for i in val_idx],
        target=[dataset.target[i] for i in val_idx],
        has_spend=[dataset.has_spend[i] for i in val_idx],
    )
    return train, validation


def _compute_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    """Compute MAE, RMSE, MAPE for point estimates."""
    mae = mean_absolute_error(actual, predicted)
    rmse = sqrt(mean_squared_error(actual, predicted))
    mape_denominator = [max(abs(value), 1.0) for value in actual]
    mape = sum(abs(a - p) / d for a, p, d in zip(actual, predicted, mape_denominator)) / len(actual)
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
    }


def train_hurdle_model(dataset_path: Path, stage1_path: Path, stage2_path: Path) -> dict:
    """Train two-stage hurdle model.
    
    Returns:
        dict with metrics and model info for reporting.
    """
    dataset = _load_dataset(dataset_path)
    if not dataset.features:
        raise ValueError("Hurdle dataset is empty. Build the dataset first.")

    train, validation = _split_time_ordered(dataset)

    # Stage 1: Binary classifier (spend vs zero day)
    print("Training Stage 1: Binary classifier (spend vs zero)...")
    stage1_model = LogisticRegression(
        class_weight="balanced",
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        random_state=42,
    )
    stage1_model.fit(train.features, train.has_spend)

    stage1_metrics = {}
    if validation.has_spend:
        val_preds_stage1 = stage1_model.predict(validation.features)
        stage1_metrics = {
            "validation_accuracy": float(accuracy_score(validation.has_spend, val_preds_stage1)),
            "validation_f1": float(f1_score(validation.has_spend, val_preds_stage1, average="binary", zero_division=0)),
        }
    else:
        stage1_metrics = {"validation_accuracy": None, "validation_f1": None}

    # Stage 2: Quantile regressor on non-zero days
    print("Training Stage 2: Quantile regressor (non-zero spend)...")
    nonzero_train_features = [f for f, s in zip(train.features, train.has_spend) if s == 1]
    nonzero_train_targets = [t for t, s in zip(train.target, train.has_spend) if s == 1]

    stage2_model = GradientBoostingRegressor(
        loss="quantile",
        alpha=0.5,  # Median quantile
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    if nonzero_train_features:
        stage2_model.fit(nonzero_train_features, nonzero_train_targets)
    else:
        # Fallback: train on all if no zero days
        stage2_model.fit(train.features, train.target)

    stage2_metrics = {}
    if validation.has_spend:
        nonzero_val_features = [f for f, s in zip(validation.features, validation.has_spend) if s == 1]
        nonzero_val_targets = [t for t, s in zip(validation.target, validation.has_spend) if s == 1]
        if nonzero_val_features:
            val_preds_stage2 = stage2_model.predict(nonzero_val_features)
            stage2_metrics = _compute_metrics(nonzero_val_targets, list(val_preds_stage2))
            stage2_metrics["validation_samples"] = len(nonzero_val_targets)
        else:
            stage2_metrics = {"mae": None, "rmse": None, "mape": None, "validation_samples": 0}
    else:
        stage2_metrics = {"mae": None, "rmse": None, "mape": None, "validation_samples": 0}

    # Save models
    stage1_path.parent.mkdir(parents=True, exist_ok=True)
    stage2_path.parent.mkdir(parents=True, exist_ok=True)

    version = generate_artifact_version()
    versioned_stage1_path = build_versioned_path(stage1_path, version)
    versioned_stage2_path = build_versioned_path(stage2_path, version)

    joblib.dump(stage1_model, stage1_path)
    joblib.dump(stage1_model, versioned_stage1_path)
    joblib.dump(stage2_model, stage2_path)
    joblib.dump(stage2_model, versioned_stage2_path)

    # Metrics
    metrics = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "rows_total": len(dataset.target),
        "rows_train": len(train.target),
        "rows_validation": len(validation.target),
        "zero_days_train": sum(1 for s in train.has_spend if s == 0),
        "zero_days_validation": sum(1 for s in validation.has_spend if s == 0),
        "spend_days_train": sum(train.has_spend),
        "spend_days_validation": sum(validation.has_spend),
        "stage1_metrics": stage1_metrics,
        "stage2_metrics": stage2_metrics,
    }

    # Write metrics files
    metrics_stage1_path = stage1_path.with_suffix(".metrics.json")
    metrics_stage2_path = stage2_path.with_suffix(".metrics.json")
    metrics_stage1_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics_stage2_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Write manifests
    manifest_stage1 = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": 1,
        "model_type": "binary_classifier",
        "model_path": str(versioned_stage1_path),
        "metrics_path": str(metrics_stage1_path),
        "latest_model_path": str(stage1_path),
    }
    manifest_stage1.update(metrics)

    manifest_stage2 = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": 2,
        "model_type": "quantile_regressor",
        "model_path": str(versioned_stage2_path),
        "metrics_path": str(metrics_stage2_path),
        "latest_model_path": str(stage2_path),
    }
    manifest_stage2.update(metrics)

    write_manifest(build_manifest_path(stage1_path), manifest_stage1)
    write_manifest(build_manifest_path(stage2_path), manifest_stage2)

    print(f"✓ Two-stage hurdle model trained: {len(train.target)} train rows, {len(validation.target)} validation rows")
    print(f"  Stage 1 (binary): {stage1_metrics.get('validation_accuracy', 'N/A')} accuracy")
    if stage2_metrics.get("mae"):
        print(f"  Stage 2 (quantile): {stage2_metrics.get('mae', 'N/A'):.2f} MAE on {stage2_metrics.get('validation_samples', 0)} non-zero days")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train two-stage hurdle model for daily spend forecasting.")
    parser.add_argument(
        "--dataset",
        default="ml/data/regression_daily_dataset.csv",
        help="Regression dataset CSV path",
    )
    parser.add_argument(
        "--stage1-path",
        default="ml/models/hurdle_stage1_classifier.joblib",
        help="Output path for stage 1 (binary classifier)",
    )
    parser.add_argument(
        "--stage2-path",
        default="ml/models/hurdle_stage2_quantile_regressor.joblib",
        help="Output path for stage 2 (quantile regressor)",
    )
    args = parser.parse_args()

    metrics = train_hurdle_model(
        dataset_path=Path(args.dataset),
        stage1_path=Path(args.stage1_path),
        stage2_path=Path(args.stage2_path),
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
