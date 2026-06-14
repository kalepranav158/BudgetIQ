from __future__ import annotations

import argparse
import csv
import os
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction


def _to_float(value: Decimal | str | float | int | None) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    index = int((len(values_sorted) - 1) * ratio)
    return float(values_sorted[index])


def _load_rows_from_clean_csv(clean_input_path: Path | None) -> list[dict]:
    if not clean_input_path or not clean_input_path.exists():
        return []
    with clean_input_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def build_regression_dataset(output_path: Path, clean_input_path: Path | None = None) -> int:
    tx_rows = _load_rows_from_clean_csv(clean_input_path)
    if not tx_rows:
        tx_rows = list(
            Transaction.objects.all().order_by("date", "id").values("date", "amount", "type")
        )

    if not tx_rows:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "date",
                    "target_total_debit",
                    "lag_1",
                    "lag_3_mean",
                    "lag_7_mean",
                    "lag_14_mean",
                    "target_total_debit_winsorized",
                    "is_spend_day",
                    "weekday",
                    "month",
                    "is_weekend",
                    "day_of_month",
                ],
            )
            writer.writeheader()
        return 0

    daily_debit: dict[date, float] = {}
    for row in tx_rows:
        day_raw = row["date"]
        day = day_raw if isinstance(day_raw, date) else date.fromisoformat(str(day_raw))
        if day not in daily_debit:
            daily_debit[day] = 0.0
        if str(row.get("type") or "").lower() == "debit":
            daily_debit[day] += _to_float(row.get("amount"))

    all_days = sorted(daily_debit.keys())
    start_day = all_days[0]
    end_day = all_days[-1]

    full_days = []
    cursor = start_day
    while cursor <= end_day:
        full_days.append(cursor)
        cursor += timedelta(days=1)

    debit_series = [daily_debit.get(day, 0.0) for day in full_days]

    winsor_cap = _percentile(debit_series, 0.99)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "date",
                "target_total_debit",
                "lag_1",
                "lag_3_mean",
                "lag_7_mean",
                "lag_14_mean",
                "target_total_debit_winsorized",
                "is_spend_day",
                "weekday",
                "month",
                "is_weekend",
                "day_of_month",
            ],
        )
        writer.writeheader()

        for index in range(14, len(full_days)):
            day = full_days[index]
            target = debit_series[index]
            lag_1 = debit_series[index - 1]
            lag_3_mean = _mean(debit_series[index - 3:index])
            lag_7_mean = _mean(debit_series[index - 7:index])
            lag_14_mean = _mean(debit_series[index - 14:index])
            winsorized = min(target, winsor_cap)
            writer.writerow(
                {
                    "date": day.isoformat(),
                    "target_total_debit": f"{target:.2f}",
                    "lag_1": f"{lag_1:.2f}",
                    "lag_3_mean": f"{lag_3_mean:.2f}",
                    "lag_7_mean": f"{lag_7_mean:.2f}",
                    "lag_14_mean": f"{lag_14_mean:.2f}",
                    "target_total_debit_winsorized": f"{winsorized:.2f}",
                    "is_spend_day": 1 if target > 0 else 0,
                    "weekday": day.weekday(),
                    "month": day.month,
                    "is_weekend": 1 if day.weekday() >= 5 else 0,
                    "day_of_month": day.day,
                }
            )
            rows_written += 1

    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily spend regression dataset.")
    parser.add_argument(
        "--output",
        default="ml/data/regression_daily_dataset.csv",
        help="CSV output path",
    )
    parser.add_argument(
        "--clean-input",
        default="ml/data/clean_transactions.csv",
        help="Optional sanitized transaction CSV input. Falls back to DB when absent.",
    )
    args = parser.parse_args()
    output_path = Path(args.output)
    rows = build_regression_dataset(output_path, clean_input_path=Path(args.clean_input))
    print(f"Wrote {rows} regression rows to {output_path}")


if __name__ == "__main__":
    main()