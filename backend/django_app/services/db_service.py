import logging
import hashlib
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from backend.django_app.models import (
    AccountCategoryMapping,
    CategoryMapping,
    DailyExpenseSummary,
    MonthlySubtypeSummary,
    MonthlySummary,
    RegexCategoryMapping,
    SUBTYPE_CHOICES,
    Transaction,
)

logger = logging.getLogger(__name__)
VALID_SUBTYPES = {key for key, _ in SUBTYPE_CHOICES}


def _build_transaction_hash(tx_date: date, amount: Decimal, description: str) -> str:
    normalized_description = " ".join(str(description).strip().upper().split())
    canonical = f"{tx_date.isoformat()}|{amount.quantize(Decimal('0.01'))}|{normalized_description}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _recalculate_monthly_totals(year: int, month: int) -> None:
    monthly_summary, _ = MonthlySummary.objects.get_or_create(year=year, month=month)
    totals = DailyExpenseSummary.objects.filter(month=monthly_summary).aggregate(
        total_debit=Coalesce(
            Sum("total_debit"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        total_credit=Coalesce(
            Sum("total_credit"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
    monthly_summary.total_debit = totals["total_debit"]
    monthly_summary.total_credit = totals["total_credit"]
    monthly_summary.save(update_fields=["total_debit", "total_credit"])


def _sum_transactions(queryset) -> Decimal:
    return queryset.aggregate(
        total=Coalesce(
            Sum("amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )["total"]


def _recalculate_monthly_subtype_totals(year: int, month: int) -> None:
    subtype_summary, _ = MonthlySubtypeSummary.objects.get_or_create(year=year, month=month)
    monthly_transactions = Transaction.objects.filter(date__year=year, date__month=month)

    expense_debit = _sum_transactions(
        monthly_transactions.filter(type="debit", subtype="expense")
    )
    transfer_out = _sum_transactions(
        monthly_transactions.filter(type="debit", subtype="transfer_out")
    )
    atm_withdrawal = _sum_transactions(
        monthly_transactions.filter(type="debit", subtype="atm_withdrawal")
    )

    transfer_in = _sum_transactions(
        monthly_transactions.filter(type="credit", subtype="transfer_in")
    )
    salary = _sum_transactions(
        monthly_transactions.filter(type="credit", subtype="salary")
    )
    refund = _sum_transactions(
        monthly_transactions.filter(type="credit", subtype="refund")
    )

    total_debit = _sum_transactions(monthly_transactions.filter(type="debit"))
    total_credit = _sum_transactions(monthly_transactions.filter(type="credit"))

    classified_credit = transfer_in + salary + refund
    other_credit = total_credit - classified_credit

    subtype_summary.expense_debit = expense_debit
    subtype_summary.transfer_out = transfer_out
    subtype_summary.transfer_in = transfer_in
    subtype_summary.atm_withdrawal = atm_withdrawal
    subtype_summary.salary = salary
    subtype_summary.refund = refund
    subtype_summary.other_credit = other_credit
    subtype_summary.total_debit = total_debit
    subtype_summary.total_credit = total_credit
    subtype_summary.net_savings = total_credit - total_debit
    subtype_summary.save(
        update_fields=[
            "expense_debit",
            "transfer_out",
            "transfer_in",
            "atm_withdrawal",
            "salary",
            "refund",
            "other_credit",
            "total_debit",
            "total_credit",
            "net_savings",
        ]
    )


def infer_transaction_subtype(description: str, tx_type: str) -> str:
    text = str(description).lower()
    normalized_type = str(tx_type).lower()

    if "atm" in text or "cash withdrawal" in text or "withdrawal" in text:
        return "atm_withdrawal"

    if normalized_type == "debit" and "upi" in text and (
        "transfer to" in text or " to " in text or "sent" in text or "dr/" in text
    ):
        return "transfer_out"

    if normalized_type == "credit" and "upi" in text and (
        "transfer from" in text or " from " in text or "received" in text or "cr/" in text
    ):
        return "transfer_in"

    if normalized_type == "credit" and "salary" in text:
        return "salary"

    if normalized_type == "credit" and "refund" in text:
        return "refund"

    return "expense" if normalized_type == "debit" else "transfer_in"


def get_category_mappings() -> list[dict[str, str | int]]:
    keyword_rows = CategoryMapping.objects.all().values("keyword", "category")
    regex_rows = RegexCategoryMapping.objects.all().order_by("priority", "name").values(
        "name", "pattern", "category", "priority"
    )
    account_rows = AccountCategoryMapping.objects.all().order_by("priority", "upi_id").values(
        "upi_id", "name", "category", "priority"
    )

    mappings: list[dict[str, str | int]] = [
        {
            "kind": "keyword",
            "keyword": row["keyword"],
            "category": row["category"],
        }
        for row in keyword_rows
    ]
    mappings.extend(
        {
            "kind": "regex",
            "name": row["name"],
            "pattern": row["pattern"],
            "category": row["category"],
            "priority": row["priority"],
        }
        for row in regex_rows
    )
    mappings.extend(
        {
            "kind": "account",
            "upi_id": row["upi_id"],
            "name": row["name"],
            "category": row["category"],
            "priority": row["priority"],
        }
        for row in account_rows
    )
    return mappings


@transaction.atomic
def save_transactions(transactions: list[dict], source_file: str) -> list[Transaction]:
    created_records: list[Transaction] = []
    touched_months: set[tuple[int, int]] = set()
    skipped_duplicates = 0
    existing_hashes_by_bucket: dict[tuple[date, Decimal], set[str]] = {}
    for item in transactions:
        tx_date = item["date"]
        if isinstance(tx_date, str):
            tx_date = date.fromisoformat(tx_date)
        amount = Decimal(str(item["amount"]))
        transaction_hash = _build_transaction_hash(
            tx_date=tx_date,
            amount=amount,
            description=item["description"],
        )

        bucket_key = (tx_date, amount.quantize(Decimal("0.01")))
        if bucket_key not in existing_hashes_by_bucket:
            existing_descriptions = Transaction.objects.filter(date=tx_date, amount=amount).values_list(
                "description", flat=True
            )
            existing_hashes_by_bucket[bucket_key] = {
                _build_transaction_hash(tx_date=tx_date, amount=amount, description=desc)
                for desc in existing_descriptions
            }

        if transaction_hash in existing_hashes_by_bucket[bucket_key]:
            skipped_duplicates += 1
            continue

        subtype = str(item.get("subtype") or infer_transaction_subtype(item["description"], item["type"])).lower()
        if subtype not in VALID_SUBTYPES:
            subtype = "expense"
        payload = {
            "date": tx_date,
            "description": item["description"],
            "amount": amount,
            "type": item["type"],
            "subtype": subtype,
            "category": item.get("category", "other"),
            "source_file": source_file,
        }
        record = Transaction.objects.create(**payload)
        created_records.append(record)
        existing_hashes_by_bucket[bucket_key].add(transaction_hash)
        touched_months.add((tx_date.year, tx_date.month))

    for year, month in touched_months:
        _recalculate_monthly_subtype_totals(year=year, month=month)

    logger.info(
        "Saved %s transactions from %s (skipped_duplicates=%s)",
        len(created_records),
        source_file,
        skipped_duplicates,
    )
    return created_records


@transaction.atomic
def upsert_daily_summaries(summaries: list[dict]) -> None:
    touched_months: set[tuple[int, int]] = set()
    for item in summaries:
        summary_date = date.fromisoformat(str(item["date"]))
        monthly_summary, _ = MonthlySummary.objects.get_or_create(
            year=summary_date.year,
            month=summary_date.month,
        )
        defaults = {
            "month": monthly_summary,
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
        touched_months.add((summary_date.year, summary_date.month))

    for year, month in touched_months:
        _recalculate_monthly_totals(year=year, month=month)

    logger.info("Upserted %s daily summary rows", len(summaries))
