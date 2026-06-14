from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path

import joblib
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

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


def _safe_float(value: str | float | int | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _load_dataset(dataset_path: Path) -> Dataset:
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    features = [[_safe_float(row.get(col)) for col in FEATURE_COLUMNS] for row in rows]
    target = [_safe_float(row.get(TARGET_COLUMN)) for row in rows]
    return Dataset(features=features, target=target)


def _split_time_ordered(dataset: Dataset) -> tuple[Dataset, Dataset]:
    total = len(dataset.target)
    if total < 5:
        return dataset, Dataset(features=[], target=[])

    split_index = max(1, int(total * 0.8))
    if split_index >= total:
        split_index = total - 1

    train = Dataset(features=dataset.features[:split_index], target=dataset.target[:split_index])
    validation = Dataset(features=dataset.features[split_index:], target=dataset.target[split_index:])
    return train, validation


def _compute_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    mae = mean_absolute_error(actual, predicted)
    rmse = sqrt(mean_squared_error(actual, predicted))
    mape_denominator = [max(abs(value), 1.0) for value in actual]
    mape = sum(abs(a - p) / d for a, p, d in zip(actual, predicted, mape_denominator)) / len(actual)
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape),
    }


def train_regressor(dataset_path: Path, model_path: Path) -> int:
    dataset = _load_dataset(dataset_path)
    if not dataset.features:
        raise ValueError("Regression dataset is empty. Build the dataset first.")

    train, validation = _split_time_ordered(dataset)

    candidates = {
        "linear_regression": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
    }

    best_name = ""
    best_model = None
    best_metrics: dict[str, float] | None = None

    candidate_results: dict[str, dict[str, float | None]] = {}

    for name, model in candidates.items():
        model.fit(train.features, train.target)

        train_predictions = model.predict(train.features)
        train_metrics = _compute_metrics(train.target, list(train_predictions))

        if validation.features:
            validation_predictions = model.predict(validation.features)
            validation_metrics = _compute_metrics(validation.target, list(validation_predictions))
            score = validation_metrics["mae"]
        else:
            validation_metrics = {"mae": None, "rmse": None, "mape": None}
            score = train_metrics["mae"]

        candidate_results[name] = {
            "train_mae": train_metrics["mae"],
            "train_rmse": train_metrics["rmse"],
            "train_mape": train_metrics["mape"],
            "validation_mae": validation_metrics["mae"],
            "validation_rmse": validation_metrics["rmse"],
            "validation_mape": validation_metrics["mape"],
        }

        if best_metrics is None or score < (best_metrics.get("validation_mae") or best_metrics["train_mae"]):
            best_name = name
            best_model = model
            best_metrics = candidate_results[name]

    if best_model is None or best_metrics is None:
        raise ValueError("No regression model could be trained.")

    model_path.parent.mkdir(parents=True, exist_ok=True)

    version = generate_artifact_version()
    versioned_model_path = build_versioned_path(model_path, version)

    metrics = {
        "selected_model": best_name,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "rows_total": len(dataset.target),
        "rows_train": len(train.target),
        "rows_validation": len(validation.target),
        "candidates": candidate_results,
    }

    metrics_path = model_path.with_suffix(".metrics.json")
    versioned_metrics_path = model_path.with_name(f"{model_path.stem}.{version}.metrics.json")

    joblib.dump(best_model, model_path)
    joblib.dump(best_model, versioned_model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    versioned_metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    manifest_payload = {
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "model_type": "regression",
        "selected_model": best_name,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "rows_total": len(dataset.target),
        "rows_train": len(train.target),
        "rows_validation": len(validation.target),
        "model_path": str(versioned_model_path),
        "metrics_path": str(versioned_metrics_path),
        "latest_model_path": str(model_path),
    }
    write_manifest(build_manifest_path(model_path), manifest_payload)

    return len(dataset.target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline regression models for daily spend forecasting.")
    parser.add_argument(
        "--dataset",
        default="ml/data/regression_daily_dataset.csv",
        help="Regression dataset CSV path",
    )
    parser.add_argument(
        "--model-path",
        default="ml/models/daily_spend_regressor.joblib",
        help="Output path for best regressor joblib",
    )
    args = parser.parse_args()

    rows = train_regressor(dataset_path=Path(args.dataset), model_path=Path(args.model_path))
    print(f"Trained regression model on {rows} rows")


if __name__ == "__main__":
    main()