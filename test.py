from __future__ import annotations

import argparse
from decimal import Decimal

from backend.services.analytics import AnalyticsService
from database.connection.session import SessionLocal, init_db


def _format_decimal(value: Decimal) -> str:
    return f'{value:.2f}'


def main() -> None:
    parser = argparse.ArgumentParser(description='Print category and monthly analytics from the normalized budget database.')
    parser.add_argument('--year', type=int, default=None, help='Optional year filter for monthly analytics')
    args = parser.parse_args()

    init_db()
    with SessionLocal() as session:
        service = AnalyticsService(session)
        category_summary = service.category_summary()
        monthly_summary = service.monthly_analytics(year=args.year)

    print('Category Summary')
    for item in category_summary:
        print(
            f"- {item.category}: debit={_format_decimal(item.total_debit)} "
            f"credit={_format_decimal(item.total_credit)} count={item.transaction_count}"
        )

    print('\nMonthly Analytics')
    for item in monthly_summary:
        print(
            f"- {item.month}: debit={_format_decimal(item.total_debit)} "
            f"credit={_format_decimal(item.total_credit)} top_spend={item.top_spend_category or 'n/a'}"
        )


if __name__ == '__main__':
    main()
