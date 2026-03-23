from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from backend.models.db import TransactionRecord
from backend.schemas.transaction import CategorySummaryItem, MonthlyAnalyticsItem


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_transactions(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        category: str | None = None,
        limit: int = 200,
    ) -> list[TransactionRecord]:
        statement: Select[tuple[TransactionRecord]] = select(TransactionRecord).order_by(
            desc(TransactionRecord.transaction_date),
            desc(TransactionRecord.id),
        )
        statement = self._apply_filters(statement, start_date, end_date, category)
        return list(self.session.scalars(statement.limit(limit)).all())

    def category_summary(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CategorySummaryItem]:
        rows = self.list_transactions(start_date=start_date, end_date=end_date, limit=10000)
        grouped: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "transaction_count": 0,
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
                "net_amount": Decimal("0.00"),
            }
        )

        for row in rows:
            bucket = grouped[row.category]
            bucket["transaction_count"] += 1
            bucket["total_debit"] += Decimal(row.debit_amount)
            bucket["total_credit"] += Decimal(row.credit_amount)
            bucket["net_amount"] += Decimal(row.amount)

        return [
            CategorySummaryItem(category=category, **values)
            for category, values in sorted(
                grouped.items(),
                key=lambda item: (item[1]["total_debit"], item[1]["transaction_count"]),
                reverse=True,
            )
        ]

    def monthly_analytics(self, year: int | None = None) -> list[MonthlyAnalyticsItem]:
        rows = self.list_transactions(limit=10000)
        grouped: dict[str, dict[str, object]] = defaultdict(
            lambda: {
                "transaction_count": 0,
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
                "net_amount": Decimal("0.00"),
                "category_spend": defaultdict(lambda: Decimal("0.00")),
            }
        )

        for row in rows:
            if year is not None and row.transaction_date.year != year:
                continue
            bucket_key = row.transaction_date.strftime("%Y-%m")
            bucket = grouped[bucket_key]
            bucket["transaction_count"] += 1
            bucket["total_debit"] += Decimal(row.debit_amount)
            bucket["total_credit"] += Decimal(row.credit_amount)
            bucket["net_amount"] += Decimal(row.amount)
            category_spend = bucket["category_spend"]
            category_spend[row.category] += Decimal(row.debit_amount)

        response: list[MonthlyAnalyticsItem] = []
        for month, values in sorted(grouped.items()):
            category_spend = values["category_spend"]
            top_spend_category = None
            if category_spend:
                top_spend_category = max(category_spend.items(), key=lambda item: item[1])[0]
            response.append(
                MonthlyAnalyticsItem(
                    month=month,
                    transaction_count=values["transaction_count"],
                    total_debit=values["total_debit"],
                    total_credit=values["total_credit"],
                    net_amount=values["net_amount"],
                    top_spend_category=top_spend_category,
                )
            )
        return response

    def _apply_filters(
        self,
        statement: Select[tuple[TransactionRecord]],
        start_date: date | None,
        end_date: date | None,
        category: str | None,
    ) -> Select[tuple[TransactionRecord]]:
        if start_date is not None:
            statement = statement.where(TransactionRecord.transaction_date >= start_date)
        if end_date is not None:
            statement = statement.where(TransactionRecord.transaction_date <= end_date)
        if category:
            statement = statement.where(TransactionRecord.category == category)
        return statement
