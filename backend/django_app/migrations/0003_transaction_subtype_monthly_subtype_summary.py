from decimal import Decimal

from django.db import migrations, models


def _infer_subtype(description: str, tx_type: str) -> str:
    text = (description or "").lower()
    normalized_type = (tx_type or "").lower()

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


def backfill_transaction_subtypes_and_monthly_summary(apps, schema_editor):
    Transaction = apps.get_model("django_app", "Transaction")
    MonthlySubtypeSummary = apps.get_model("django_app", "MonthlySubtypeSummary")

    month_buckets: dict[tuple[int, int], dict[str, Decimal]] = {}

    for tx in Transaction.objects.all().iterator():
        subtype = _infer_subtype(tx.description, tx.type)
        tx.subtype = subtype
        tx.save(update_fields=["subtype"])

        key = (tx.date.year, tx.date.month)
        if key not in month_buckets:
            month_buckets[key] = {
                "expense_debit": Decimal("0.00"),
                "transfer_out": Decimal("0.00"),
                "transfer_in": Decimal("0.00"),
                "atm_withdrawal": Decimal("0.00"),
                "salary": Decimal("0.00"),
                "refund": Decimal("0.00"),
                "other_credit": Decimal("0.00"),
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
            }

        bucket = month_buckets[key]
        amount = tx.amount
        if tx.type == "debit":
            bucket["total_debit"] += amount
            if subtype == "expense":
                bucket["expense_debit"] += amount
            elif subtype == "transfer_out":
                bucket["transfer_out"] += amount
            elif subtype == "atm_withdrawal":
                bucket["atm_withdrawal"] += amount
        else:
            bucket["total_credit"] += amount
            if subtype == "transfer_in":
                bucket["transfer_in"] += amount
            elif subtype == "salary":
                bucket["salary"] += amount
            elif subtype == "refund":
                bucket["refund"] += amount
            else:
                bucket["other_credit"] += amount

    for (year, month), bucket in month_buckets.items():
        classified_credit = bucket["transfer_in"] + bucket["salary"] + bucket["refund"]
        other_credit = bucket["total_credit"] - classified_credit
        MonthlySubtypeSummary.objects.update_or_create(
            year=year,
            month=month,
            defaults={
                "expense_debit": bucket["expense_debit"],
                "transfer_out": bucket["transfer_out"],
                "transfer_in": bucket["transfer_in"],
                "atm_withdrawal": bucket["atm_withdrawal"],
                "salary": bucket["salary"],
                "refund": bucket["refund"],
                "other_credit": other_credit,
                "total_debit": bucket["total_debit"],
                "total_credit": bucket["total_credit"],
                "net_savings": bucket["total_credit"] - bucket["total_debit"],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0002_monthlysummary_daily_month_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="subtype",
            field=models.CharField(
                choices=[
                    ("expense", "Expense"),
                    ("transfer_out", "Transfer Out"),
                    ("transfer_in", "Transfer In"),
                    ("atm_withdrawal", "ATM Withdrawal"),
                    ("salary", "Salary"),
                    ("refund", "Refund"),
                ],
                default="expense",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="MonthlySubtypeSummary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.IntegerField()),
                ("month", models.IntegerField()),
                ("expense_debit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("transfer_out", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("transfer_in", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("atm_withdrawal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("salary", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("refund", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("other_credit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("total_debit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("total_credit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("net_savings", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "monthly_subtype_summary",
                "unique_together": {("year", "month")},
            },
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["subtype"], name="transactions_subtype_dcd943_idx"),
        ),
        migrations.RunPython(backfill_transaction_subtypes_and_monthly_summary, migrations.RunPython.noop),
    ]
