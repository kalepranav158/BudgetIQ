from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any

import django
import joblib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction


DEFAULT_REGRESSOR_PATH = "ml/models/daily_spend_regressor.joblib"


def _manifest_for_model(model_path: Path) -> dict[str, Any] | None:
    manifest_path = model_path.with_name(f"{model_path.stem}.manifest.json")
    if not manifest_path.exists():
        return None

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    return payload if isinstance(payload, dict) else None


def _resolve_regressor_path(model_path: Path) -> tuple[Path, dict[str, Any] | None]:
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


def generate_daily_spend_forecast(days: int = 7) -> dict[str, Any]:
    if days < 1 or days > 60:
        raise ValueError("days must be between 1 and 60")

    model_path = Path(os.getenv("ML_DAILY_REGRESSOR_PATH", DEFAULT_REGRESSOR_PATH))
    resolved_model_path, manifest = _resolve_regressor_path(model_path)

    if not resolved_model_path.exists():
        raise RuntimeError("Daily spend regressor artifact is not available")

    all_days, series = _daily_debit_series()
    if len(series) < 14:
        raise ValueError("Not enough historical data to generate forecast")

    model = joblib.load(resolved_model_path)
    history = list(series)
    anchor_day = all_days[-1]

    rmse = 0.0
    if manifest:
        metrics_path = Path(str(manifest.get("metrics_path", "")))
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                candidates = metrics.get("candidates", {})
                selected_model = manifest.get("selected_model")
                selected_metrics = candidates.get(selected_model, {}) if isinstance(candidates, dict) else {}
                rmse = float(selected_metrics.get("validation_rmse") or 0.0)
            except (json.JSONDecodeError, ValueError, TypeError):
                rmse = 0.0

    forecast_rows: list[dict[str, Any]] = []
    for offset in range(1, days + 1):
        target_day = anchor_day + timedelta(days=offset)
        features = _feature_vector(history, target_day)
        prediction = float(model.predict([features])[0])
        prediction = max(prediction, 0.0)
        history.append(prediction)

        lower_bound = max(prediction - rmse, 0.0)
        upper_bound = prediction + rmse

        forecast_rows.append(
            {
                "date": target_day.isoformat(),
                "predicted_total_debit": round(prediction, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
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
        "model_version": manifest.get("version") if manifest else "unversioned",
        "selected_model": manifest.get("selected_model") if manifest else "unknown",
        "last_observed_date": all_days[-1].isoformat(),
        "recent_actuals": recent_actuals,
        "forecast": forecast_rows,
    }