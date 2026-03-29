from decimal import Decimal

from backend.django_app.services.aggregator import build_daily_summaries


def test_build_daily_summaries_groups_by_date_and_type() -> None:
    transactions = [
        {"date": "2024-07-01", "amount": Decimal("200.00"), "type": "debit", "category": "lunch"},
        {"date": "2024-07-01", "amount": Decimal("100.00"), "type": "debit", "category": "tea"},
        {"date": "2024-07-01", "amount": Decimal("5000.00"), "type": "credit", "category": "credit"},
    ]

    result = build_daily_summaries(transactions)

    assert len(result) == 1
    assert result[0]["lunch"] == Decimal("200.00")
    assert result[0]["tea"] == Decimal("100.00")
    assert result[0]["total_debit"] == Decimal("300.00")
    assert result[0]["credit"] == Decimal("5000.00")
    assert result[0]["total_credit"] == Decimal("5000.00")
