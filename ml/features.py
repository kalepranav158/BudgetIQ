from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.fastapi_service.parser.categorizer import extract_upi_counterparty_name

from ml.utils import normalize_text


AMOUNT_BUCKETS = (
    (0, "zero"),
    (50, "micro"),
    (250, "small"),
    (1000, "medium"),
    (5000, "large"),
)


def _to_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value

    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _amount_bucket(amount: Decimal) -> str:
    absolute_amount = abs(amount)
    for threshold, label in AMOUNT_BUCKETS:
        if absolute_amount <= Decimal(str(threshold)):
            return label
    return "very_large"


def _weekday_label(value: date | None) -> str:
    if not value:
        return "unknown_weekday"
    return value.strftime("%a").lower()


def _month_label(value: date | None) -> str:
    if not value:
        return "unknown_month"
    return value.strftime("%b").lower()


def build_feature_row(row: dict[str, Any]) -> dict[str, Any]:
    description = normalize_text(row.get("description") or row.get("text"))
    counterparty = normalize_text(row.get("counterparty") or extract_upi_counterparty_name(description) or "")
    tx_date = _to_date(row.get("date"))
    amount = _to_decimal(row.get("amount"))
    tx_type = normalize_text(row.get("type"))
    subtype = normalize_text(row.get("subtype"))
    category = normalize_text(row.get("category"))

    amount_bucket = _amount_bucket(amount)
    weekday = _weekday_label(tx_date)
    month = _month_label(tx_date)
    year = str(tx_date.year) if tx_date else "unknown_year"
    day_of_month = tx_date.day if tx_date else 0
    is_weekend = int(tx_date.weekday() >= 5) if tx_date else 0

    tokens = [token for token in description.split() if token]
    prefix_bigram = " ".join(tokens[:2]) if len(tokens) >= 2 else (tokens[0] if tokens else "")

    is_upi = int("upi" in description)
    is_transfer = int("transfer" in description or subtype == "transfer_out")

    combined_text = normalize_text(
        " ".join(
            part
            for part in (
                description,
                f"counterparty {counterparty}" if counterparty else "",
                f"amount_bucket {amount_bucket}",
                f"weekday {weekday}",
                f"month {month}",
                f"year {year}",
                f"type {tx_type}" if tx_type else "",
                f"subtype {subtype}" if subtype else "",
                f"is_upi {is_upi}",
                f"is_transfer {is_transfer}",
            )
            if part
        )
    )

    return {
        "date": tx_date.isoformat() if tx_date else "",
        "description": description,
        "text": description,
        "counterparty": counterparty,
        "amount": float(amount),
        "amount_log1p": float(math.log1p(max(0.0, float(amount)))),
        "amount_bucket": amount_bucket,
        "weekday": weekday,
        "month": month,
        "year": year,
        "day_of_month": day_of_month,
        "is_weekend": is_weekend,
        "prefix_bigram": prefix_bigram,
        "type": tx_type,
        "subtype": subtype,
        "category": category,
        "is_upi": is_upi,
        "is_transfer": is_transfer,
        "combined_text": combined_text,
    }


def build_features(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [build_feature_row(row) for row in rows]
