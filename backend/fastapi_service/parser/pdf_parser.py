import io
import re
from datetime import datetime
from decimal import Decimal

import pdfplumber

# Some statements start with Value Date + Post Date and may use either
# textual dates ("01 Apr 2026") or numeric dates ("01/04/2026").
_DATE_TOKEN = r"(?:\d{2}\s+[A-Za-z]{3}\s+\d{4}|\d{2}[/-]\d{2}[/-]\d{4})"
START_LINE_PATTERN = re.compile(rf"^(?P<date>{_DATE_TOKEN})(?:\s+{_DATE_TOKEN})?\s+(?P<body>.+)$")

SBI_AMOUNT_COLUMNS_PATTERN = re.compile(
    # Matches lines where the last three columns are: debit, credit, balance
    # Optionally captures a reference/cheque number between description and the numeric columns.
    r"^(?P<description>.+?)\s+"  # non-greedy description
    r"(?:(?P<ref>\S+)\s+)?"  # optional reference/cheque no
    r"(?P<debit>-|[\d,]+\.\d{2})\s+"  # debit column or '-'
    r"(?P<credit>-|[\d,]+\.\d{2})\s+"  # credit column or '-'
    r"(?P<balance>[\d,]+\.\d{2})$",
    re.IGNORECASE,
)


def _parse_sbi_date(raw: str) -> str:
    value = raw.strip()
    for fmt in ("%d %b %Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {raw}")


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
