import logging
from datetime import date
from decimal import Decimal

from django.db import transaction

from backend.django_app.models import CategoryMapping, DailyExpenseSummary, Transaction

logger = logging.getLogger(__name__)


def get_category_mappings() -> list[dict[str, str]]:
    rows = CategoryMapping.objects.all().values("keyword", "category")
    return [{"keyword": row["keyword"], "category": row["category"]} for row in rows]


@transaction.atomic
def save_transactions(transactions: list[dict], source_file: str) -> list[Transaction]:
    created_records: list[Transaction] = []
    for item in transactions:
        record = Transaction.objects.create(
            date=item["date"],
            description=item["description"],
            amount=Decimal(str(item["amount"])),
            type=item["type"],
            category=item.get("category", "other"),
            source_file=source_file,
        )
        created_records.append(record)
    logger.info("Saved %s transactions from %s", len(created_records), source_file)
    return created_records


@transaction.atomic
def upsert_daily_summaries(summaries: list[dict]) -> None:
    for item in summaries:
        summary_date = date.fromisoformat(str(item["date"]))
        defaults = {
            "cash_withdrawal": Decimal(str(item.get("cash_withdrawal", 0))),
            "extra": Decimal(str(item.get("extra", 0))),
            "lunch": Decimal(str(item.get("lunch", 0))),
            "other": Decimal(str(item.get("other", 0))),
            "recharge": Decimal(str(item.get("recharge", 0))),
            "tea": Decimal(str(item.get("tea", 0))),
            "credit": Decimal(str(item.get("credit", 0))),
            "total_debit": Decimal(str(item.get("total_debit", 0))),
            "total_credit": Decimal(str(item.get("total_credit", 0))),
        }
        DailyExpenseSummary.objects.update_or_create(date=summary_date, defaults=defaults)
    logger.info("Upserted %s daily summary rows", len(summaries))
