from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from backend.services.categorization import HybridTransactionCategorizer
from backend.utils.parsing import StatementParser
from .model import DailyTransactionSummary, Raw_Transaction, UPI_Category_Mapping

LEGACY_CATEGORY_MAP = {
    'cash_withdrawal': 'cash_withdrawal',
    'tea': 'tea',
    'mess': 'lunch',
    'food': 'lunch',
    'recharge': 'other_expenses',
    'shopping': 'other_expenses',
    'stationery': 'other_expenses',
    'transport': 'other_expenses',
    'income': 'other_expenses',
    'other': 'other_expenses',
}


def process_sbi_statement(pdf_file, password=None, user=None, filename=None):
    parser = StatementParser()
    categorizer = HybridTransactionCategorizer()
    raw_transactions = []
    daily_summaries = defaultdict(
        lambda: {
            'cash_withdrawal': Decimal('0.00'),
            'tea': Decimal('0.00'),
            'lunch': Decimal('0.00'),
            'dinner': Decimal('0.00'),
            'other_expenses': Decimal('0.00'),
            'total_debit': Decimal('0.00'),
            'total_credit': Decimal('0.00'),
        }
    )

    stored_mappings = {}
    if user is not None:
        stored_mappings = {
            mapping.upi_id.lower(): mapping.category
            for mapping in UPI_Category_Mapping.objects.filter(user=user)
        }

    try:
        parsed_transactions = parser.parse(
            pdf_source=pdf_file,
            password=password,
            source_name=filename,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    for parsed in parsed_transactions:
        decision = categorizer.categorize(
            description=parsed.description,
            counterparty=parsed.counterparty,
            direction=parsed.direction,
            stored_mappings=stored_mappings,
        )
        raw_transactions.append(
            Raw_Transaction(
                date=parsed.transaction_date,
                details=parsed.description[:2000],
                debit=str(parsed.debit_amount) if parsed.debit_amount > 0 else None,
                credit=str(parsed.credit_amount) if parsed.credit_amount > 0 else None,
                balance=str(parsed.balance) if parsed.balance is not None else None,
                source_pdf=filename[:100] if filename else None,
                uploaded_by=user,
                upi_id=parsed.counterparty,
                category=decision.category,
            )
        )
        _update_daily_summary(daily_summaries, parsed.transaction_date.isoformat(), decision.category, parsed.debit_amount, parsed.credit_amount)

        if parsed.counterparty and user is not None and decision.source in {'mapping', 'rule', 'ml'}:
            stored_mappings.setdefault(parsed.counterparty, decision.category)

    if not raw_transactions:
        raise ValidationError('No valid transactions found in PDF')
    return raw_transactions, daily_summaries


def _update_daily_summary(
    daily_summaries: dict[str, dict[str, Decimal]],
    date_key: str,
    category: str,
    debit_amount: Decimal,
    credit_amount: Decimal,
) -> None:
    summary = daily_summaries[date_key]
    summary['total_debit'] += debit_amount
    summary['total_credit'] += credit_amount

    if debit_amount > 0:
        legacy_category = LEGACY_CATEGORY_MAP.get(category, 'other_expenses')
        summary[legacy_category] += debit_amount


@transaction.atomic
def save_transaction_data(raw_transactions, daily_summaries, user):
    Raw_Transaction.objects.bulk_create(raw_transactions)

    if user is not None:
        for date_str, summary in daily_summaries.items():
            DailyTransactionSummary.objects.update_or_create(
                date=date.fromisoformat(date_str),
                user=user,
                defaults=summary,
            )

        for txn in raw_transactions:
            if txn.upi_id and txn.category:
                UPI_Category_Mapping.objects.update_or_create(
                    user=user,
                    upi_id=txn.upi_id,
                    defaults={'category': _legacy_mapping_choice(txn.category)},
                )


def _legacy_mapping_choice(category: str) -> str:
    if category in {'cash_withdrawal', 'tea', 'lunch', 'dinner'}:
        return category
    return 'other'