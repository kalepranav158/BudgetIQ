import os
from decimal import Decimal
from uuid import uuid4

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import MonthlySummary, Transaction
from backend.django_app.services.db_service import save_transactions, upsert_daily_summaries


def test_monthly_rollup_correctness() -> None:
    summaries = [
        {
            "date": "2099-01-15",
            "cash_withdrawal": "10.00",
            "extra": "5.00",
            "lunch": "15.00",
            "other": "0.00",
            "recharge": "0.00",
            "tea": "0.00",
            "credit": "0.00",
            "total_debit": "30.00",
            "total_credit": "0.00",
        },
        {
            "date": "2099-01-16",
            "cash_withdrawal": "0.00",
            "extra": "0.00",
            "lunch": "0.00",
            "other": "0.00",
            "recharge": "0.00",
            "tea": "0.00",
            "credit": "100.00",
            "total_debit": "0.00",
            "total_credit": "100.00",
        },
    ]

    upsert_daily_summaries(summaries)

    monthly = MonthlySummary.objects.get(year=2099, month=1)
    assert monthly.total_debit == Decimal("30.00")
    assert monthly.total_credit == Decimal("100.00")


def test_duplicate_transaction_prevention_by_hash() -> None:
    unique_tag = uuid4().hex[:8].upper()
    description = f"UPI/DR/1234/ALPHA-{unique_tag}/BANK"
    transactions = [
        {
            "date": "2099-02-01",
            "description": description,
            "amount": "42.50",
            "type": "debit",
            "category": "other",
        }
    ]

    first = save_transactions(transactions=transactions, source_file="dedup_test.pdf")
    second = save_transactions(transactions=transactions, source_file="dedup_test.pdf")

    assert len(first) == 1
    assert len(second) == 0

    matching_rows = Transaction.objects.filter(
        date="2099-02-01",
        amount=Decimal("42.50"),
        description=description,
    )
    assert matching_rows.count() == 1
