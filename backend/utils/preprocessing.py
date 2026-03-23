from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = (
    "%d %b %Y",
    "%d %B %Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
)

AMOUNT_PATTERN = re.compile(r"\d[\d,]*\.\d{2}")


def normalize_text(value: object) -> str:
    text = str(value or "").replace("\n", " ").replace("\r", " ")
    return " ".join(text.split()).strip()


def parse_date(value: object) -> date | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return None


def parse_decimal(value: object) -> Decimal | None:
    normalized = normalize_text(value).upper()
    if not normalized or normalized == "-":
        return None
    match = AMOUNT_PATTERN.search(normalized)
    if match is None:
        return None
    try:
        return Decimal(match.group(0).replace(",", ""))
    except InvalidOperation:
        return None


def signed_amount(debit_amount: Decimal | None, credit_amount: Decimal | None) -> Decimal:
    if credit_amount is not None and credit_amount > 0:
        return credit_amount
    if debit_amount is not None and debit_amount > 0:
        return -debit_amount
    return Decimal("0.00")


def transaction_fingerprint(
    transaction_date: date,
    description: str,
    amount: Decimal,
    source_file: str | None,
) -> str:
    payload = "|".join(
        [
            transaction_date.isoformat(),
            normalize_text(description).lower(),
            str(amount),
            normalize_text(source_file).lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def detect_channel(description: str) -> str:
    normalized = normalize_text(description).lower()
    if "upi" in normalized or "@" in normalized:
        return "upi"
    if "atm" in normalized:
        return "atm"
    if "neft" in normalized:
        return "neft"
    if "imps" in normalized:
        return "imps"
    return "bank_statement"
