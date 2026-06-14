from __future__ import annotations

import csv
import json
import os
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction
from ml.preprocessing.build_regression_dataset import build_regression_dataset
from ml.training.train_regressor import train_regressor


def test_build_regression_dataset_exports_rows(tmp_path: Path) -> None:
    prefix = f"REG_{uuid4().hex[:8]}"
    start = date(2099, 1, 1)
    for offset in range(20):
        tx_day = start + timedelta(days=offset)
        Transaction.objects.create(
            date=tx_day,
            description=f"{prefix} DAY {offset}",
            amount=str(100 + offset),
            type="debit",
            subtype="expense",
            category="other",
            source_file="regression-test.pdf",
        )

    dataset_path = tmp_path / "regression_daily_dataset.csv"
    rows = build_regression_dataset(dataset_path)

    assert rows >= 6
    assert dataset_path.exists()

    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        data = list(reader)

    assert data
    assert {"lag_1", "lag_3_mean", "lag_7_mean", "lag_14_mean", "target_total_debit"}.issubset(data[0].keys())


def test_train_regressor_writes_artifacts(tmp_path: Path) -> None:
    dataset_path = tmp_path / "regression_daily_dataset.csv"
    dataset_path.write_text(
        "date,target_total_debit,lag_1,lag_3_mean,lag_7_mean,lag_14_mean,weekday,month,is_weekend\n"
        "2026-01-15,120.0,110.0,108.0,105.0,100.0,3,1,0\n"
        "2026-01-16,130.0,120.0,115.0,108.0,101.0,4,1,0\n"
        "2026-01-17,150.0,130.0,120.0,112.0,102.0,5,1,1\n"
        "2026-01-18,140.0,150.0,133.0,118.0,103.0,6,1,1\n"
        "2026-01-19,160.0,140.0,140.0,125.0,104.0,0,1,0\n"
        "2026-01-20,170.0,160.0,150.0,132.0,105.0,1,1,0\n",
        encoding="utf-8",
    )

    model_path = tmp_path / "daily_spend_regressor.joblib"
    rows = train_regressor(dataset_path=dataset_path, model_path=model_path)

    assert rows == 6
    assert model_path.exists()

    metrics_path = model_path.with_suffix(".metrics.json")
    manifest_path = model_path.with_name("daily_spend_regressor.manifest.json")

    assert metrics_path.exists()
    assert manifest_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert metrics["selected_model"] in {"linear_regression", "ridge"}
    assert manifest["model_type"] == "regression"
    assert manifest["version"].startswith("v")
    assert Path(manifest["model_path"]).exists()
    assert Path(manifest["metrics_path"]).exists()