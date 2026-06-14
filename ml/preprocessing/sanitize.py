from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction


def _to_iso_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def _normalize_text(value: str | None) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _to_amount(value: Decimal | str | float | int | None) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


def _compute_bounds(values: list[float]) -> tuple[float, float]:
    if len(values) < 4:
        return float("-inf"), float("inf")
    values_sorted = sorted(values)
    q1 = values_sorted[int((len(values_sorted) - 1) * 0.25)]
    q3 = values_sorted[int((len(values_sorted) - 1) * 0.75)]
    iqr = q3 - q1
    return q1 - (1.5 * iqr), q3 + (1.5 * iqr)


def _regression_row_estimate(rows: list[dict]) -> int:
    if not rows:
        return 0
    all_dates = sorted(date.fromisoformat(row["date"]) for row in rows)
    span_days = (all_dates[-1] - all_dates[0]).days + 1
    return max(0, span_days - 14)


def sanitize_transactions(
    clean_output_path: Path,
    quarantine_output_path: Path,
    report_output_path: Path,
    synthetic_year_threshold: int = 2027,
) -> dict:
    tx_rows = list(
        Transaction.objects.all().order_by("date", "id").values(
            "date",
            "description",
            "amount",
            "type",
            "subtype",
            "category",
            "category_source",
            "confidence",
            "source_file",
            "created_at",
        )
    )

    all_rows: list[dict] = []
    for row in tx_rows:
        tx_date = _to_iso_date(row["date"])
        all_rows.append(
            {
                "date": tx_date,
                "description": str(row.get("description") or "").strip(),
                "amount": f"{_to_amount(row.get('amount')):.2f}",
                "type": str(row.get("type") or "").lower().strip(),
                "subtype": str(row.get("subtype") or "").lower().strip(),
                "category": str(row.get("category") or "").lower().strip(),
                "category_source": str(row.get("category_source") or "keyword").strip(),
                "confidence": float(row.get("confidence") or 0.0),
                "source_file": str(row.get("source_file") or "").strip(),
                "created_at": str(row.get("created_at") or ""),
            }
        )

    real_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    for row in all_rows:
        tx_year = date.fromisoformat(row["date"]).year
        if tx_year >= synthetic_year_threshold:
            quarantine_rows.append(row)
        else:
            real_rows.append(row)

    deduped: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    duplicates_removed = 0
    for row in real_rows:
        key = (
            row["date"],
            _normalize_text(row["description"]),
            row["amount"],
            row["type"],
        )
        if key in seen:
            duplicates_removed += 1
            continue
        seen.add(key)
        deduped.append(row)

    amount_by_type: dict[str, list[float]] = defaultdict(list)
    for row in deduped:
        amount_by_type[row["type"]].append(float(row["amount"]))

    bounds_by_type = {k: _compute_bounds(v) for k, v in amount_by_type.items()}
    outlier_counts: dict[str, int] = {k: 0 for k in amount_by_type.keys()}
    for row in deduped:
        lower, upper = bounds_by_type.get(row["type"], (float("-inf"), float("inf")))
        amt = float(row["amount"])
        is_outlier = amt < lower or amt > upper
        row["is_outlier"] = int(is_outlier)
        if is_outlier:
            outlier_counts[row["type"]] = outlier_counts.get(row["type"], 0) + 1

    fieldnames = [
        "date",
        "description",
        "amount",
        "type",
        "subtype",
        "category",
        "category_source",
        "confidence",
        "source_file",
        "created_at",
        "is_outlier",
    ]

    clean_output_path.parent.mkdir(parents=True, exist_ok=True)
    quarantine_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)

    with clean_output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    with quarantine_output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames[:-1])
        writer.writeheader()
        writer.writerows(quarantine_rows)

    real_dates = [date.fromisoformat(row["date"]) for row in deduped]
    report = {
        "run_date": datetime.now(UTC).date().isoformat(),
        "input_transactions": len(all_rows),
        "quarantined_synthetic": len(quarantine_rows),
        "real_transactions": len(deduped),
        "duplicates_removed": duplicates_removed,
        "amount_outliers_flagged_debit": outlier_counts.get("debit", 0),
        "amount_outliers_flagged_credit": outlier_counts.get("credit", 0),
        "regression_rows_before": _regression_row_estimate(all_rows),
        "regression_rows_after_decontamination": _regression_row_estimate(deduped),
        "real_date_range": [
            real_dates[0].isoformat() if real_dates else None,
            real_dates[-1].isoformat() if real_dates else None,
        ],
        "synthetic_year_threshold": synthetic_year_threshold,
    }
    report_output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize transactions by quarantining synthetic dates and flagging outliers.")
    parser.add_argument("--clean-output", default="ml/data/clean_transactions.csv", help="CSV output for cleaned transactions")
    parser.add_argument("--quarantine-output", default="ml/data/quarantine_synthetic.csv", help="CSV output for quarantined synthetic transactions")
    parser.add_argument("--report-output", default="ml/data/sanitization_report.json", help="JSON output for sanitization report")
    parser.add_argument("--synthetic-year-threshold", type=int, default=2027, help="Rows with year >= threshold are quarantined")
    args = parser.parse_args()

    report = sanitize_transactions(
        clean_output_path=Path(args.clean_output),
        quarantine_output_path=Path(args.quarantine_output),
        report_output_path=Path(args.report_output),
        synthetic_year_threshold=args.synthetic_year_threshold,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
