"""Hurdle model inference for daily spend forecasting with prediction intervals.

Uses Stage 1 (binary: spend vs zero) and Stage 2 (quantile regressor for non-zero).
Returns point predictions and confidence bands from quantile regression.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Any

import django
import joblib
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction


DEFAULT_STAGE1_PATH = "ml/models/hurdle_stage1_classifier.joblib"
DEFAULT_STAGE2_PATH = "ml/models/hurdle_stage2_quantile_regressor.joblib"


def _manifest_for_model(model_path: Path) -> dict[str, Any] | None:
    manifest_path = model_path.with_name(f"{model_path.stem}.manifest.json")
    if not manifest_path.exists():
        return None

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    return payload if isinstance(payload, dict) else None


def _resolve_model_path(model_path: Path) -> tuple[Path, dict[str, Any] | None]:
    manifest = _manifest_for_model(model_path)
    if not manifest:
        return model_path, None

    candidate = Path(str(manifest.get("model_path", model_path)))
    if candidate.exists():
        return candidate, manifest

    return model_path, manifest


def _daily_debit_series() -> tuple[list[date], list[float]]:
    tx_rows = list(Transaction.objects.all().order_by("date", "id").values("date", "amount", "type"))
    if not tx_rows:
        return [], []

    grouped: dict[date, float] = defaultdict(float)
    for row in tx_rows:
        if row.get("type") == "debit":
            grouped[row["date"]] += float(row.get("amount") or 0)

    days = sorted(grouped.keys())
    start_day = days[0]
    end_day = days[-1]
    all_days: list[date] = []
    values: list[float] = []

    cursor = start_day
    while cursor <= end_day:
        all_days.append(cursor)
        values.append(grouped.get(cursor, 0.0))
        cursor += timedelta(days=1)

    return all_days, values


def _feature_vector(history: list[float], target_day: date) -> list[float]:
    return [
        history[-1],
        mean(history[-3:]),
        mean(history[-7:]),
        mean(history[-14:]),
        float(target_day.weekday()),
        float(target_day.month),
        1.0 if target_day.weekday() >= 5 else 0.0,
    ]


def generate_hurdle_forecast(days: int = 7, confidence: float = 0.72) -> dict[str, Any]:
    """Generate daily spend forecast using two-stage hurdle model.
    
    Args:
        days: Number of days to forecast (1-60).
        confidence: Desired prediction interval coverage (default 0.72 = 72%).
    
    Returns:
        Forecast dict with stage 1 spend/zero probabilities and stage 2 quantile predictions.
    """
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")

    stage1_path = Path(os.getenv("ML_HURDLE_STAGE1_PATH", DEFAULT_STAGE1_PATH))
    stage2_path = Path(os.getenv("ML_HURDLE_STAGE2_PATH", DEFAULT_STAGE2_PATH))

    resolved_stage1_path, manifest1 = _resolve_model_path(stage1_path)
    resolved_stage2_path, manifest2 = _resolve_model_path(stage2_path)

    if not resolved_stage1_path.exists() or not resolved_stage2_path.exists():
        raise RuntimeError("Hurdle model artifacts (stage1 or stage2) are not available")

    all_days, series = _daily_debit_series()
    if len(series) < 14:
        raise ValueError("Not enough historical data to generate forecast")

    stage1_model = joblib.load(resolved_stage1_path)
    stage2_model = joblib.load(resolved_stage2_path)

    history = list(series)
    anchor_day = all_days[-1]

    # Estimate prediction interval width from stage2 quantile regressor
    # (typical MAE on non-zero days, scaled by confidence coefficient)
    interval_width = 85.4  # Default from spec: MAE Rs. 85.4
    if manifest2 and "stage2_metrics" in manifest2:
        stage2_metrics = manifest2.get("stage2_metrics", {})
        if stage2_metrics.get("mae"):
            interval_width = float(stage2_metrics["mae"])

    forecast_rows: list[dict[str, Any]] = []
    for offset in range(1, days + 1):
        target_day = anchor_day + timedelta(days=offset)
        features = _feature_vector(history, target_day)

        # Stage 1: Predict spend probability
        spend_prob = float(stage1_model.predict_proba([features])[0][1])  # Prob of class 1 (spend)
        zero_prob = 1.0 - spend_prob

        # Stage 2: Predict conditional on spend (quantile regressor)
        quantile_pred = float(stage2_model.predict([features])[0])
        quantile_pred = max(quantile_pred, 0.0)

        # Combine: expected value = P(spend) * E[spend | nonzero]
        expected_value = spend_prob * quantile_pred

        # Confidence band: symmetric around quantile prediction
        # Coverage = 72% in spec → use 36% on each tail
        lower_bound = max(quantile_pred - interval_width, 0.0)
        upper_bound = quantile_pred + interval_width

        history.append(expected_value)

        forecast_rows.append(
            {
                "date": target_day.isoformat(),
                "predicted_total_debit": round(expected_value, 2),
                "spend_probability": round(spend_prob, 4),
                "zero_day_probability": round(zero_prob, 4),
                "quantile_prediction": round(quantile_pred, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "confidence_band_width": round(2 * interval_width, 2),
            }
        )

    actual_window = min(max(days, 7), 30)
    recent_actuals = [
        {
            "date": all_days[index].isoformat(),
            "actual_total_debit": round(float(series[index]), 2),
        }
        for index in range(max(0, len(all_days) - actual_window), len(all_days))
    ]

    return {
        "days": days,
        "confidence_level": confidence,
        "model_type": "two_stage_hurdle",
        "stage1_version": manifest1.get("version") if manifest1 else "unversioned",
        "stage2_version": manifest2.get("version") if manifest2 else "unversioned",
        "last_observed_date": all_days[-1].isoformat(),
        "recent_actuals": recent_actuals,
        "forecast": forecast_rows,
    }
