from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any

import pdfplumber

from backend.utils.preprocessing import detect_channel, normalize_text, parse_date, parse_decimal, signed_amount

HEADER_ALIASES = {
    "date": "date",
    "txn date": "date",
    "transaction date": "date",
    "value date": "date",
    "details": "details",
    "description": "details",
    "particulars": "details",
    "remarks": "details",
    "ref no cheque no": "reference_number",
    "ref no./cheque no": "reference_number",
    "ref no / cheque no": "reference_number",
    "ref_no_cheque_no": "reference_number",
    "debit": "debit",
    "withdrawal amt": "debit",
    "credit": "credit",
    "deposit amt": "credit",
    "balance": "balance",
}

COUNTERPARTY_PATTERNS = (
    r"UPI/(?:DR|CR|P2A|P2M|COLLECT)/\d+/([^/]+)/",
    r"UPI/\w+/\d+/([^/]+)/",
    r"TRANSFER (?:TO|FROM) .*?UPI/(?:DR|CR)/\d+/([^/]+)/",
    r"([A-Za-z][A-Za-z .]{2,})@\w+",
)

DATE_PREFIX_PATTERN = re.compile(r"^(\d{2}(?:/\d{2}/\d{4}|-\d{2}-\d{4}|\s+[A-Za-z]{3,9}\s+\d{4}))\s+(.*)$")
AMOUNT_TOKEN_PATTERN = re.compile(r"\d[\d,]*\.\d{2}(?:\s*(?:DR|CR))?", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedTransaction:
    transaction_date: Any
    description: str
    reference_number: str | None
    debit_amount: Decimal
    credit_amount: Decimal
    amount: Decimal
    balance: Decimal | None
    counterparty: str | None
    transaction_channel: str
    source_file: str | None
    raw_text: str

    @property
    def direction(self) -> str:
        return "credit" if self.credit_amount > 0 else "debit"


class StatementParser:
    def parse(self, pdf_source, password: str | None = None, source_name: str | None = None) -> list[ParsedTransaction]:
        if hasattr(pdf_source, "seek"):
            pdf_source.seek(0)

        extracted_rows: list[dict[str, str | None]] = []
        try:
            with pdfplumber.open(pdf_source, password=password or None) as pdf:
                for page in pdf.pages:
                    extracted_rows.extend(self._extract_transactions_from_page(page))
        except Exception as exc:
            raise ValueError(f"Unable to parse the supplied SBI statement: {exc}") from exc

        parsed_transactions: list[ParsedTransaction] = []
        for row in extracted_rows:
            parsed = self._build_transaction(row=row, source_name=source_name)
            if parsed is not None:
                parsed_transactions.append(parsed)

        if not parsed_transactions:
            raise ValueError("No valid transactions were detected in the PDF statement.")
        return parsed_transactions

    def _extract_transactions_from_page(self, page) -> list[dict[str, str | None]]:
        rows = self._extract_from_tables(page)
        if rows:
            return rows
        return self._extract_from_text(page)

    def _extract_from_tables(self, page) -> list[dict[str, str | None]]:
        extracted: list[dict[str, str | None]] = []
        for table in page.extract_tables() or []:
            if not table or len(table) < 2:
                continue
            canonical_headers = [self._normalize_header(item) for item in table[0]]
            if "date" not in canonical_headers or "details" not in canonical_headers:
                continue

            for raw_row in table[1:]:
                padded_row = list(raw_row) + [None] * (len(canonical_headers) - len(raw_row))
                row_map: dict[str, str | None] = {}
                for index, header in enumerate(canonical_headers):
                    if header is None:
                        continue
                    row_map[header] = padded_row[index]

                if not normalize_text(row_map.get("date")) and extracted:
                    for key, value in row_map.items():
                        text = normalize_text(value)
                        if text:
                            previous_value = normalize_text(extracted[-1].get(key))
                            extracted[-1][key] = f"{previous_value} {text}".strip()
                    continue

                if normalize_text(row_map.get("date")) and normalize_text(row_map.get("details")):
                    extracted.append(row_map)
        return extracted

    def _extract_from_text(self, page) -> list[dict[str, str | None]]:
        text = page.extract_text() or ""
        grouped_entries: list[str] = []
        current_entry = ""
        for line in text.splitlines():
            normalized_line = normalize_text(line)
            if not normalized_line:
                continue
            if DATE_PREFIX_PATTERN.match(normalized_line):
                if current_entry:
                    grouped_entries.append(current_entry)
                current_entry = normalized_line
            elif current_entry:
                current_entry = f"{current_entry} {normalized_line}"

        if current_entry:
            grouped_entries.append(current_entry)

        rows: list[dict[str, str | None]] = []
        for entry in grouped_entries:
            row = self._parse_text_entry(entry)
            if row is not None:
                rows.append(row)
        return rows

    def _parse_text_entry(self, entry: str) -> dict[str, str | None] | None:
        match = DATE_PREFIX_PATTERN.match(entry)
        if match is None:
            return None
        entry_date, body = match.groups()
        amount_matches = list(AMOUNT_TOKEN_PATTERN.finditer(body))
        if not amount_matches:
            return None

        debit: str | None = None
        credit: str | None = None
        balance = amount_matches[-1].group(0)
        description_end = amount_matches[0].start()
        description = normalize_text(body[:description_end])
        candidate_amounts = amount_matches[:-1]

        for candidate in candidate_amounts:
            token = candidate.group(0).upper()
            if token.endswith("CR"):
                credit = token
            elif token.endswith("DR"):
                debit = token

        if debit is None and credit is None and candidate_amounts:
            ambiguous_token = candidate_amounts[-1].group(0)
            if "TRANSFER FROM" in entry.upper() or "BY TRANSFER" in entry.upper():
                credit = ambiguous_token
            else:
                debit = ambiguous_token

        return {
            "date": entry_date,
            "details": description,
            "reference_number": self._extract_reference_number(body),
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

    def _build_transaction(self, row: dict[str, str | None], source_name: str | None) -> ParsedTransaction | None:
        transaction_date = parse_date(row.get("date"))
        description = normalize_text(row.get("details"))
        if transaction_date is None or not description:
            return None

        debit_amount = parse_decimal(row.get("debit")) or Decimal("0.00")
        credit_amount = parse_decimal(row.get("credit")) or Decimal("0.00")
        if debit_amount == 0 and credit_amount == 0:
            return None

        balance = parse_decimal(row.get("balance"))
        counterparty = self._extract_counterparty(description)

        return ParsedTransaction(
            transaction_date=transaction_date,
            description=description,
            reference_number=normalize_text(row.get("reference_number")) or None,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            amount=signed_amount(debit_amount, credit_amount),
            balance=balance,
            counterparty=counterparty,
            transaction_channel=detect_channel(description),
            source_file=source_name,
            raw_text=description,
        )

    def _normalize_header(self, value: object) -> str | None:
        normalized = normalize_text(value).lower().replace("_", " ")
        return HEADER_ALIASES.get(normalized)

    def _extract_reference_number(self, body: str) -> str | None:
        match = re.search(r"\b[A-Z0-9]{6,}\b", body)
        if match is None:
            return None
        return match.group(0)

    def _extract_counterparty(self, description: str) -> str | None:
        for pattern in COUNTERPARTY_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match is not None:
                return normalize_text(match.group(1)).lower()
        return None
