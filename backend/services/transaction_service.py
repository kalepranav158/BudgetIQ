from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.db import CategoryMapping, TransactionRecord
from backend.services.categorization import HybridTransactionCategorizer
from backend.utils.parsing import ParsedTransaction, StatementParser
from backend.utils.preprocessing import transaction_fingerprint


@dataclass(frozen=True)
class ImportSummary:
    imported_count: int
    duplicate_count: int
    total_parsed: int
    categories: list[str]


class TransactionIngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.parser = StatementParser()
        self.categorizer = HybridTransactionCategorizer()

    def import_statement(
        self,
        pdf_source,
        source_name: str | None,
        password: str | None = None,
    ) -> dict[str, object]:
        parsed_transactions = self.parser.parse(
            pdf_source=pdf_source,
            password=password or settings.default_pdf_password,
            source_name=source_name,
        )
        summary = self.persist_transactions(parsed_transactions)
        return asdict(summary)

    def persist_transactions(self, parsed_transactions: Iterable[ParsedTransaction]) -> ImportSummary:
        stored_mappings = self._load_mappings()
        pending_mapping_updates: dict[str, str] = {}
        imported_count = 0
        duplicate_count = 0
        categories: set[str] = set()

        for parsed in parsed_transactions:
            fingerprint = transaction_fingerprint(
                transaction_date=parsed.transaction_date,
                description=parsed.description,
                amount=parsed.amount,
                source_file=parsed.source_file,
            )
            if self._is_duplicate(fingerprint):
                duplicate_count += 1
                continue

            decision = self.categorizer.categorize(
                description=parsed.description,
                counterparty=parsed.counterparty,
                direction=parsed.direction,
                stored_mappings=stored_mappings,
            )

            record = TransactionRecord(
                fingerprint=fingerprint,
                transaction_date=parsed.transaction_date,
                description=parsed.description,
                reference_number=parsed.reference_number,
                debit_amount=parsed.debit_amount,
                credit_amount=parsed.credit_amount,
                amount=parsed.amount,
                balance=parsed.balance,
                direction=parsed.direction,
                category=decision.category,
                predicted_category=decision.predicted_category,
                prediction_source=decision.source,
                counterparty=parsed.counterparty,
                transaction_channel=parsed.transaction_channel,
                source_file=parsed.source_file,
                raw_text=parsed.raw_text,
            )
            self.session.add(record)
            categories.add(decision.category)
            imported_count += 1

            if parsed.counterparty and parsed.direction == "debit" and decision.source in {"mapping", "rule", "ml"}:
                stored_mappings.setdefault(parsed.counterparty, decision.category)
                pending_mapping_updates[parsed.counterparty] = decision.category

        for counterparty, category in pending_mapping_updates.items():
            self._upsert_mapping(counterparty, category)

        self.session.commit()
        return ImportSummary(
            imported_count=imported_count,
            duplicate_count=duplicate_count,
            total_parsed=imported_count + duplicate_count,
            categories=sorted(categories),
        )

    def _load_mappings(self) -> dict[str, str]:
        rows = self.session.scalars(select(CategoryMapping)).all()
        return {row.counterparty: row.category for row in rows}

    def _is_duplicate(self, fingerprint: str) -> bool:
        existing = self.session.scalar(
            select(TransactionRecord.id).where(TransactionRecord.fingerprint == fingerprint)
        )
        return existing is not None

    def _upsert_mapping(self, counterparty: str, category: str) -> None:
        mapping = self.session.scalar(
            select(CategoryMapping).where(CategoryMapping.counterparty == counterparty)
        )
        if mapping is None:
            self.session.add(CategoryMapping(counterparty=counterparty, category=category))
            return
        mapping.category = category
