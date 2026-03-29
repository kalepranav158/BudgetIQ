import io
import re
from datetime import datetime
from decimal import Decimal

import pdfplumber

START_LINE_PATTERN = re.compile(r"^(?P<date>\d{2}\s+[A-Za-z]{3}\s+\d{4})\s+(?P<body>.+)$")

SBI_AMOUNT_COLUMNS_PATTERN = re.compile(
    r"^(?P<description>.+?)\s+"
    r"(?P<ref>\S+)\s+"
    r"(?P<debit>-|[\d,]+\.\d{2})\s+"
    r"(?P<credit>-|[\d,]+\.\d{2})\s+"
    r"(?P<balance>[\d,]+\.\d{2})$",
    re.IGNORECASE,
)


def _parse_sbi_date(raw: str) -> str:
    return datetime.strptime(raw.strip(), "%d %b %Y").date().isoformat()


def _parse_decimal(raw: str) -> Decimal:
    return Decimal(raw.replace(",", "").strip())


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _build_transaction(date_text: str, first_line_body: str, continuation_lines: list[str]) -> dict | None:
    match = SBI_AMOUNT_COLUMNS_PATTERN.match(first_line_body.strip())
    if not match:
        return None

    debit_raw = match.group("debit")
    credit_raw = match.group("credit")

    if credit_raw != "-":
        tx_type = "credit"
        amount = _parse_decimal(credit_raw)
    else:
        tx_type = "debit"
        amount = _parse_decimal(debit_raw)

    full_description = " ".join([match.group("description")] + continuation_lines)

    return {
        "date": _parse_sbi_date(date_text),
        "description": _normalize_space(full_description),
        "amount": amount,
        "type": tx_type,
        "balance": _parse_decimal(match.group("balance")),
    }


def extract_transactions_from_pdf(pdf_bytes: bytes, password: str | None = None) -> list[dict]:
    transactions: list[dict] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes), password=password or None) as pdf:
        current_date: str | None = None
        current_first_line: str | None = None
        current_continuation: list[str] = []

        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue

                start_match = START_LINE_PATTERN.match(stripped)
                if start_match:
                    if current_date and current_first_line:
                        built = _build_transaction(current_date, current_first_line, current_continuation)
                        if built is not None:
                            transactions.append(built)
                    current_date = start_match.group("date")
                    current_first_line = start_match.group("body")
                    current_continuation = []
                    continue

                if current_date and current_first_line:
                    current_continuation.append(stripped)

        if current_date and current_first_line:
            built = _build_transaction(current_date, current_first_line, current_continuation)
            if built is not None:
                transactions.append(built)

    return transactions
