from decimal import Decimal
from django.db import migrations, models

def backfill_month_fk(apps, schema_editor):
    DailyExpenseSummary = apps.get_model("django_app", "DailyExpenseSummary")
    MonthlySummary = apps.get_model("django_app", "MonthlySummary")

    for daily in DailyExpenseSummary.objects.all().iterator():
        monthly, _ = MonthlySummary.objects.get_or_create(
            year=daily.date.year,
            month=daily.date.month,
            defaults={
                "total_debit": Decimal("0.00"),
                "total_credit": Decimal("0.00"),
            },
        )
        daily.month_id = monthly.id
        daily.save(update_fields=["month"])

    for monthly in MonthlySummary.objects.all().iterator():
        daily_rows = DailyExpenseSummary.objects.filter(month_id=monthly.id)
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        for row in daily_rows.iterator():
            total_debit += row.total_debit
            total_credit += row.total_credit
        monthly.total_debit = total_debit
        monthly.total_credit = total_credit
        monthly.save(update_fields=["total_debit", "total_credit"])


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonthlySummary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.IntegerField()),
                ("month", models.IntegerField()),
                ("total_debit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("total_credit", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "monthly_summary",
                "unique_together": {("year", "month")},
            },
        ),
        migrations.AddField(
            model_name="dailyexpensesummary",
            name="month",
            field=models.ForeignKey(null=True, on_delete=models.CASCADE, related_name="daily_summaries", to="django_app.monthlysummary"),
        ),
        migrations.RunPython(backfill_month_fk, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dailyexpensesummary",
            name="month",
            field=models.ForeignKey(on_delete=models.CASCADE, related_name="daily_summaries", to="django_app.monthlysummary"),
        ),
    ]
